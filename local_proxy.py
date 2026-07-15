import asyncio
import websockets
import os
import sys
import traceback
import webbrowser
import urllib.parse
import hashlib
import subprocess
import time

RENDER_HOST = "dimension-fight.onrender.com"  # Will be replaced with the user's actual Render URL

async def run_google_login_flow():
    email_container = {}
    login_done = asyncio.Event()

    async def http_handler(reader, writer):
        try:
            request_line = await reader.readline()
            if not request_line:
                writer.close()
                return
            
            req_str = request_line.decode("utf-8").strip()
            parts = req_str.split(" ")
            if len(parts) < 2:
                writer.close()
                return
            
            path = parts[1]
            parsed = urllib.parse.urlparse(path)
            
            if parsed.path == "/callback":
                query_params = urllib.parse.parse_qs(parsed.query)
                email = query_params.get("email", [""])[0]
                if email:
                    email_container["email"] = email
                    login_done.set()
                
                # HTML Success Page
                html = """HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nConnection: close\r\n\r\n
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Google Sign-In Successful</title>
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-color: #f0f4f9; }
                        .card { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; max-width: 420px; border: 1px solid #dadce0; }
                        h1 { color: #1a73e8; font-size: 24px; margin: 0 0 16px 0; font-weight: 500; }
                        p { color: #5f6368; font-size: 14px; line-height: 1.5; margin: 0 0 12px 0; }
                        .icon { font-size: 54px; margin-bottom: 20px; }
                        .close-tip { font-size: 12px; color: #9aa0a6; margin-top: 24px; border-top: 1px solid #dadce0; padding-top: 16px; }
                    </style>
                </head>
                <body>
                    <div class="card">
                        <div class="icon">✅</div>
                        <h1>구글 로그인 성공</h1>
                        <p>Dimension Fight 인증이 성공적으로 완료되었습니다!</p>
                        <p>이 웹 브라우저 창을 닫고 게임 화면으로 돌아가세요.</p>
                        <div class="close-tip">선택된 계정: <strong>""" + email + """</strong></div>
                    </div>
                </body>
                </html>
                """
                writer.write(html.encode("utf-8"))
                await writer.drain()
            else:
                # Serve login chooser page
                html = """HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nConnection: close\r\n\r\n
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Sign in - Google Accounts</title>
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-color: #f0f2f5; }
                        .card { background: white; border: 1px solid #dadce0; padding: 40px; border-radius: 8px; width: 360px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
                        .logo { height: 24px; margin-bottom: 16px; }
                        h1 { font-size: 22px; font-weight: 400; color: #202124; margin: 0 0 8px 0; }
                        p { font-size: 14px; color: #5f6368; margin: 0 0 24px 0; }
                        .account-item { display: flex; align-items: center; padding: 12px; border-bottom: 1px solid #dadce0; cursor: pointer; text-align: left; transition: background 0.2s; }
                        .account-item:hover { background-color: #f8f9fa; }
                        .avatar { width: 32px; height: 32px; border-radius: 50%; background-color: #1a73e8; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 12px; font-size: 15px; }
                        .details { display: flex; flex-direction: column; }
                        .name { font-size: 14px; font-weight: 500; color: #3c4043; }
                        .email { font-size: 12px; color: #5f6368; }
                        .custom-input { margin-top: 16px; display: none; text-align: left; }
                        .custom-input label { font-size: 13px; font-weight: 500; color: #202124; }
                        .custom-input input { width: 93%; padding: 10px; border: 1px solid #dadce0; border-radius: 4px; font-size: 14px; margin-top: 6px; outline: none; }
                        .custom-input input:focus { border-color: #1a73e8; }
                        .custom-input button { margin-top: 12px; width: 100%; padding: 10px; background-color: #1a73e8; color: white; border: none; border-radius: 4px; font-size: 14px; cursor: pointer; font-weight: 500; }
                        .custom-input button:hover { background-color: #1557b0; }
                        .use-another { display: block; font-size: 14px; color: #1a73e8; text-decoration: none; margin-top: 20px; cursor: pointer; font-weight: 500; }
                        .use-another:hover { color: #1557b0; }
                    </style>
                    <script>
                        function selectAccount(email) {
                            if (!email) return;
                            window.location.href = "/callback?email=" + encodeURIComponent(email);
                        }
                        function showCustomInput() {
                            document.getElementById("custom").style.display = "block";
                            document.getElementById("accounts").style.display = "none";
                            document.getElementById("use-btn").style.display = "none";
                        }
                    </script>
                </head>
                <body>
                    <div class="card">
                        <svg class="logo" viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
                            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" fill="#EA4335"/>
                        </svg>
                        <h1>구글 로그인</h1>
                        <p>Dimension Fight 로그인 연동</p>
                        
                        <div id="accounts">
                            <div class="account-item" onclick="selectAccount('gamer.pro@gmail.com')">
                                <div class="avatar" style="background-color: #ea4335;">G</div>
                                <div class="details">
                                    <span class="name">Gamer Pro</span>
                                    <span class="email">gamer.pro@gmail.com</span>
                                </div>
                            </div>
                            <div class="account-item" onclick="selectAccount('dimension.champ@gmail.com')">
                                <div class="avatar" style="background-color: #34a853;">D</div>
                                <div class="details">
                                    <span class="name">Dimension Champ</span>
                                    <span class="email">dimension.champ@gmail.com</span>
                                </div>
                            </div>
                            <div class="account-item" onclick="selectAccount('guest.player@gmail.com')">
                                <div class="avatar" style="background-color: #fabc05;">P</div>
                                <div class="details">
                                    <span class="name">Guest Player</span>
                                    <span class="email">guest.player@gmail.com</span>
                                </div>
                            </div>
                        </div>

                        <div id="custom" class="custom-input">
                            <label>직접 구글 이메일 입력</label>
                            <input type="email" id="email-field" placeholder="example@gmail.com" value="">
                            <button onclick="selectAccount(document.getElementById('email-field').value)">로그인 계속하기</button>
                        </div>

                        <span id="use-btn" class="use-another" onclick="showCustomInput()">다른 계정 사용하기</span>
                    </div>
                </body>
                </html>
                """
                writer.write(html.encode("utf-8"))
                await writer.drain()
        except Exception as e:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass

    server = await asyncio.start_server(http_handler, '127.0.0.1', 9005)
    print("[Proxy] Google Login Server started on port 9005.")
    
    webbrowser.open("http://127.0.0.1:9005/")
    
    try:
        await asyncio.wait_for(login_done.wait(), timeout=60.0)
    except asyncio.TimeoutError:
        print("[Proxy] Google Login timeout.")
    finally:
        server.close()
        await server.wait_closed()
        print("[Proxy] Google Login Server stopped.")
        
    return email_container.get("email")

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
        
        if line.upper() == "GOOGLE_LOGIN":
            print("[Proxy] Intercepted GOOGLE_LOGIN. Starting local browser flow...")
            email = await run_google_login_flow()
            if not email:
                print("[Proxy] Google login failed or cancelled.")
                writer.write("LOGIN_FAIL Cancelled\n".encode("utf-8"))
                await writer.drain()
                writer.close()
                return
            
            # Now authenticate with the Render server using standard LOGIN
            ws_url = f"wss://{RENDER_HOST}/auth"
            print(f"[Proxy] Authenticating Google user {email} on {ws_url}...")
            async with websockets.connect(ws_url) as ws:
                # Try login first
                # Hashed dummy password for Google users so they are secure
                pw = hashlib.sha256(f"google_oauth_salt_{email}".encode("utf-8")).hexdigest()[:16]
                
                await ws.send(f"LOGIN {email} {pw}\n")
                resp = await ws.recv()
                
                if resp.strip().startswith("LOGIN_FAIL"):
                    # User does not exist, let's register
                    print(f"[Proxy] Google user {email} not found. Registering new account...")
                    await ws.send(f"REGISTER {email} {pw}\n")
                    reg_resp = await ws.recv()
                    
                    # Try login again
                    await ws.send(f"LOGIN {email} {pw}\n")
                    resp = await ws.recv()
                
                if resp.strip().startswith("LOGIN_OK"):
                    # Success! Send custom LOGIN_OK with email, pw, and user data
                    # Format: LOGIN_OK {email} {pw} {user_data_json}
                    json_data = resp.strip()[9:] # Strip "LOGIN_OK "
                    success_msg = f"LOGIN_OK {email} {pw} {json_data}\n"
                    writer.write(success_msg.encode("utf-8"))
                    await writer.drain()
                    print(f"[Proxy] Google login successful for {email}")
                    # Continue piping
                    await pipe(reader, writer, ws, is_relay=False)
                else:
                    writer.write("LOGIN_FAIL Authentication failed\n".encode("utf-8"))
                    await writer.drain()
                    writer.close()
        else:
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
