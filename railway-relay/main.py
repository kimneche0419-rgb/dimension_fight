import asyncio
import os
import traceback
import hmac
import hashlib
import time

# sessions: session_id -> { "HOST": (reader, writer, username), "CLIENT": (reader, writer, username), "event": asyncio.Event() }
sessions = {}
sessions_lock = asyncio.Lock()

# Must match railway-auth's AUTH_SHARED_SECRET so tokens it issues verify here.
AUTH_SHARED_SECRET = os.environ.get("AUTH_SHARED_SECRET", "dev-insecure-shared-secret-change-me")

def verify_session_token(username: str, token: str) -> bool:
    try:
        tok_user, expiry_str, sig = token.split(".", 2)
        if tok_user != username:
            return False
        expiry = int(expiry_str)
        if expiry < int(time.time()):
            return False
        payload = f"{tok_user}.{expiry}"
        expected_sig = hmac.new(AUTH_SHARED_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, sig)
    except Exception:
        return False

async def relay_stream(reader, writer, name_from, name_to):
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                print(f"[Relay] Connection closed by {name_from}")
                break
            writer.write(data)
            await writer.drain()
    except Exception as e:
        print(f"[Relay] Stream error {name_from} -> {name_to}: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"[Relay Server] Connection from {addr}")

    session_id = None
    role = None
    username = None

    try:
        # Read the INIT line (timeout 10s)
        init_data = await asyncio.wait_for(reader.readline(), timeout=10.0)
        if not init_data:
            writer.close()
            return

        line = init_data.decode("utf-8").strip()
        parts = line.split(" ")
        if len(parts) < 5 or parts[0].upper() != "INIT":
            print(f"[Relay Server] Invalid INIT from {addr}: {line}")
            writer.close()
            return

        session_id = parts[1]
        role = parts[2].upper() # HOST or CLIENT
        username = parts[3]
        token = parts[4]

        if role not in ["HOST", "CLIENT"]:
            print(f"[Relay Server] Invalid role {role} from {username}")
            writer.close()
            return

        if not verify_session_token(username, token):
            print(f"[Relay Server] Rejected INIT: invalid/expired session token for {username} (session {session_id})")
            writer.close()
            return

        print(f"[Relay Server] Client registered: {username} as {role} for session {session_id}")

        async with sessions_lock:
            if session_id not in sessions:
                sessions[session_id] = {
                    "HOST": None,
                    "CLIENT": None,
                    "event": asyncio.Event()
                }
            session = sessions[session_id]
            
            # Close existing if duplicate
            if session[role] is not None:
                old_r, old_w, old_u = session[role]
                try:
                    old_w.close()
                except:
                    pass

            session[role] = (reader, writer, username)

            # Check if both are now connected
            ready = session["HOST"] is not None and session["CLIENT"] is not None
            if ready:
                session["event"].set()

        if not ready:
            # Wait for the other peer to connect
            try:
                await asyncio.wait_for(session["event"].wait(), timeout=30.0)
            except asyncio.TimeoutError:
                print(f"[Relay Server] Timeout waiting for peer in session {session_id} for user {username}")
                writer.close()
                return

        # Start relaying
        async with sessions_lock:
            # Re-fetch elements safely
            session = sessions.get(session_id)
            if not session or not session["HOST"] or not session["CLIENT"]:
                writer.close()
                return
            h_r, h_w, h_u = session["HOST"]
            c_r, c_w, c_u = session["CLIENT"]

        if role == "HOST":
            print(f"[Relay Server] Relaying started for session {session_id}: {h_u} <-> {c_u}")
            await relay_stream(h_r, c_w, h_u, c_u)
        else:
            await relay_stream(c_r, h_w, c_u, h_u)

    except Exception as e:
        print(f"[Relay Server] Error handling {addr}: {e}")
        traceback.print_exc()
    finally:
        # Cleanup session from global dict
        if session_id:
            async with sessions_lock:
                if session_id in sessions:
                    session = sessions[session_id]
                    # Close other writer if exists
                    other_role = "CLIENT" if role == "HOST" else "HOST"
                    if session[other_role]:
                        _, other_w, other_u = session[other_role]
                        try:
                            other_w.close()
                        except:
                            pass
                    del sessions[session_id]
                    print(f"[Relay Server] Session {session_id} cleaned up.")
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass

async def main():
    port = int(os.environ.get("PORT", 9002))
    server = await asyncio.start_server(handle_client, '0.0.0.0', port)
    print(f"[Relay Server] Listening on port {port}...")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
