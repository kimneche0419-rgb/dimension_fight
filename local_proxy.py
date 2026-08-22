import asyncio
import websockets
import os
import sys
import traceback
import subprocess
import time

RENDER_HOST = "dimension-fight-ws.onrender.com"  # Overridden by proxy_config.txt RENDER_HOST at runtime

def load_config():
    global RENDER_HOST
    # Check in current dir or parent dir for proxy_config.txt
    paths = ["proxy_config.txt", "../proxy_config.txt", "dimension_fight_cpp/build/proxy_config.txt"]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            k, v = line.split("=", 1)
                            if k.strip() == "RENDER_HOST":
                                RENDER_HOST = v.strip()
                                print(f"[Local Proxy] Config loaded from {p}")
                                return
            except:
                pass
    print("[Local Proxy] Using default Render URL.")

async def pipe(reader, writer, ws, is_relay=False):
    async def tcp_to_ws():
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                if is_relay:
                    await ws.send(data)
                else:
                    await ws.send(data.decode("utf-8"))
        except Exception as e:
            pass
        finally:
            try:
                await ws.close()
            except:
                pass

    async def ws_to_tcp():
        try:
            async for message in ws:
                if isinstance(message, str):
                    writer.write(message.encode("utf-8"))
                else:
                    writer.write(message)
                await writer.drain()
        except Exception as e:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass

    await asyncio.gather(tcp_to_ws(), ws_to_tcp())

async def handle_auth(reader, writer):
    try:
        # Read the first line (command)
        line_bytes = await reader.readline()
        if not line_bytes:
            writer.close()
            return
        
        line = line_bytes.decode("utf-8").strip()

        # Standard login/register flow, connect to Render immediately
        ws_url = f"wss://{RENDER_HOST}/auth"
        print(f"[Proxy] Standard Auth -> Connecting to {ws_url}...")
        async with websockets.connect(ws_url) as ws:
            # Send the first line we read
            await ws.send(line + "\n")
            await pipe(reader, writer, ws, is_relay=False)
    except Exception as e:
        print(f"[Proxy] Auth handler error: {e}")
        writer.close()

async def handle_match(reader, writer):
    ws_url = f"wss://{RENDER_HOST}/match"
    print(f"[Proxy] Match connection -> Connecting to {ws_url}...")
    try:
        async with websockets.connect(ws_url) as ws:
            print("[Proxy] Match WS connected.")
            await pipe(reader, writer, ws, is_relay=False)
    except Exception as e:
        print(f"[Proxy] Match WS connection failed: {e}")
        writer.close()

async def handle_relay(reader, writer):
    print("[Proxy] Relay connection accepted. Waiting for INIT...")
    try:
        # Read the first line (INIT line)
        line_bytes = await reader.readline()
        if not line_bytes:
            writer.close()
            return
        
        line = line_bytes.decode("utf-8").strip()
        parts = line.split(" ")
        if len(parts) < 4 or parts[0].upper() != "INIT":
            print(f"[Proxy] Invalid relay INIT line: {line}")
            writer.close()
            return
        
        session_id = parts[1]
        ws_url = f"wss://{RENDER_HOST}/relay/{session_id}"
        print(f"[Proxy] Relay INIT received. Connecting to {ws_url}...")

        async with websockets.connect(ws_url) as ws:
            print("[Proxy] Relay WS connected. Sending INIT...")
            # Forward the INIT line immediately
            await ws.send(line + "\n")
            # Relaying data
            await pipe(reader, writer, ws, is_relay=True)
    except Exception as e:
        print(f"[Proxy] Relay connection error: {e}")
        traceback.print_exc()
        writer.close()

def kill_process_on_port(port):
    """포트를 점유한 프로세스를 종료합니다 (Windows 전용)."""
    try:
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            # netstat 형식: TCP  127.0.0.1:PORT  0.0.0.0:0  LISTENING  PID
            if len(parts) >= 5 and parts[3] == 'LISTENING' and parts[1].endswith(f':{port}'):
                pid = parts[4]
                subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                print(f"[Local Proxy] 포트 {port} 점유 프로세스 종료 (PID: {pid})")
                return True
    except Exception as e:
        print(f"[Local Proxy] 포트 {port} 프로세스 종료 실패: {e}")
    return False

async def start_server_with_retry(handler, host, port, retries=3):
    """포트 충돌 시 기존 프로세스를 종료하고 재시도합니다."""
    for attempt in range(retries + 1):
        try:
            server = await asyncio.start_server(handler, host, port)
            return server
        except OSError as e:
            if e.errno in (10048, 98) and attempt < retries:
                print(f"[Local Proxy] 포트 {port} 사용 중. 기존 프로세스 종료 중... (시도 {attempt+1}/{retries})")
                kill_process_on_port(port)
                time.sleep(1.5)
            else:
                raise

async def main():
    load_config()
    print(f"[Local Proxy] Starting TCP listeners on 127.0.0.1...")
    print(f"  - Auth Server: TCP port 9000 -> wss://{RENDER_HOST}/auth")
    print(f"  - Matchmaking Server: TCP port 9001 -> wss://{RENDER_HOST}/match")
    print(f"  - Relay Server: TCP port 9002 -> wss://{RENDER_HOST}/relay/<session_id>")

    try:
        server_auth = await start_server_with_retry(handle_auth, '127.0.0.1', 9000)
        server_match = await start_server_with_retry(handle_match, '127.0.0.1', 9001)
        server_relay = await start_server_with_retry(handle_relay, '127.0.0.1', 9002)
    except OSError as e:
        print(f"[Local Proxy] 서버 시작 실패: {e}")
        print("[Local Proxy] 작업 관리자에서 local_proxy.exe 프로세스를 직접 종료 후 다시 실행하세요.")
        sys.exit(1)

    async with server_auth, server_match, server_relay:
        await asyncio.gather(
            server_auth.serve_forever(),
            server_match.serve_forever(),
            server_relay.serve_forever()
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[Local Proxy] Shutting down.")
