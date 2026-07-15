import asyncio
import os
import uuid
import traceback

# Queues for matchmaking: mode -> list of (reader, writer, username)
queues = {
    "1v1": [],
    "coop": []
}

RELAY_HOST = os.environ.get("RELAY_HOST", "127.0.0.1")
RELAY_PORT = int(os.environ.get("RELAY_PORT", 9002))

async def matchmaker_loop():
    while True:
        await asyncio.sleep(1.0)
        for mode in ["1v1", "coop"]:
            q = queues[mode]
            while len(q) >= 2:
                p1 = q.pop(0)
                p2 = q.pop(0)

                r1, w1, user1 = p1
                r2, w2, user2 = p2

                session_id = str(uuid.uuid4())[:8] # Short unique session ID

                print(f"[Matchmaker] Matched {user1} and {user2} in {mode}. Session: {session_id}")

                try:
                    # Notify player 1 to connect to relay as HOST
                    w1.write(f"MATCHED HOST {RELAY_HOST} {RELAY_PORT} {session_id} {user2}\n".encode("utf-8"))
                    await w1.drain()
                except Exception as e:
                    print(f"[Matchmaker] Failed to notify {user1}: {e}")
                
                try:
                    # Notify player 2 to connect to relay as CLIENT
                    w2.write(f"MATCHED CLIENT {RELAY_HOST} {RELAY_PORT} {session_id} {user1}\n".encode("utf-8"))
                    await w2.drain()
                except Exception as e:
                    print(f"[Matchmaker] Failed to notify {user2}: {e}")

def remove_from_queues(username):
    for mode in queues:
        queues[mode] = [p for p in queues[mode] if p[2] != username]

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"[Match Server] Connected: {addr}")
    username = None

    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            
            line = data.decode("utf-8").strip()
            if not line:
                continue

            parts = line.split(" ", 1)
            cmd = parts[0].upper()
            args = parts[1] if len(parts) > 1 else ""

            if cmd == "MATCH":
                try:
                    u, mode = args.split(" ", 1)
                    username = u
                    mode = mode.lower()
                    if mode in ["1v1", "coop"]:
                        # Remove existing occurrences
                        remove_from_queues(username)
                        queues[mode].append((reader, writer, username))
                        writer.write(b"MATCH_QUEUED\n")
                        await writer.drain()
                        print(f"[Match Server] User {username} queued for {mode}")
                    else:
                        writer.write(b"MATCH_FAIL Invalid mode\n")
                        await writer.drain()
                except Exception as e:
                    writer.write(f"MATCH_FAIL {str(e)}\n".encode("utf-8"))
                    await writer.drain()

            elif cmd == "CANCEL":
                if username:
                    remove_from_queues(username)
                    writer.write(b"CANCEL_OK\n")
                    await writer.drain()
                    print(f"[Match Server] User {username} cancelled search")
                else:
                    # Cancel with specific username from args if not set on connection
                    u = args.strip()
                    if u:
                        remove_from_queues(u)
                        writer.write(b"CANCEL_OK\n")
                        await writer.drain()
                        print(f"[Match Server] User {u} cancelled search")
                    else:
                        writer.write(b"CANCEL_FAIL Specify username\n")
                        await writer.drain()
    except Exception as e:
        print(f"[Match Server] Error handling client {addr}: {e}")
    finally:
        if username:
            remove_from_queues(username)
        writer.close()
        await writer.wait_closed()
        print(f"[Match Server] Disconnected: {addr}")

async def main():
    port = int(os.environ.get("PORT", 9001))
    server = await asyncio.start_server(handle_client, '0.0.0.0', port)
    print(f"[Match Server] Listening on port {port}...")
    
    # Start matchmaker queue loop
    asyncio.create_task(matchmaker_loop())
    
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
