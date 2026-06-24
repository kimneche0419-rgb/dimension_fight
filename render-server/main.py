import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import sqlite3
import json
import uuid
import os

app = FastAPI()

# Database init
DB_FILE = "users.db"
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            gold INTEGER DEFAULT 0,
            diamonds INTEGER DEFAULT 0,
            high_score INTEGER DEFAULT 0,
            player_job TEXT DEFAULT '',
            equipped_fruit TEXT DEFAULT '',
            upgrades TEXT DEFAULT '[0,0,0,0,0,0]',
            owned_skills TEXT DEFAULT '{}',
            owned_anime_fruits TEXT DEFAULT '{}',
            job_upgrades TEXT DEFAULT '{}',
            crafted_items TEXT DEFAULT '{}',
            fruit_awakenings TEXT DEFAULT '{}',
            equipped_skills TEXT DEFAULT '[]',
            unlocked_jobs TEXT DEFAULT '["전사", "저격수", "파일럿", "마법사", "흡혈귀", "기계공", "탱커", "광속", "차원술사", "학살자"]'
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/")
async def root():
    return {"status": "ok", "service": "Dimension Fight WebSocket Server"}

@app.websocket("/auth")
async def websocket_auth(websocket: WebSocket):
    await websocket.accept()
    username = None
    try:
        while True:
            data = await websocket.receive_text()
            line = data.strip()
            if not line:
                continue
            
            parts = line.split(" ", 1)
            cmd = parts[0].upper()
            args = parts[1] if len(parts) > 1 else ""
            
            db = sqlite3.connect(DB_FILE)
            cursor = db.cursor()
            
            if cmd == "REGISTER":
                try:
                    u, p = args.split(" ", 1)
                    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (u, p))
                    db.commit()
                    await websocket.send_text("REGISTER_OK\n")
                except sqlite3.IntegrityError:
                    await websocket.send_text("REGISTER_FAIL User already exists\n")
                except Exception as e:
                    await websocket.send_text(f"REGISTER_FAIL {str(e)}\n")
                    
            elif cmd == "LOGIN":
                try:
                    u, p = args.split(" ", 1)
                    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
                    row = cursor.fetchone()
                    if row:
                        username = u
                        col_names = [d[0] for d in cursor.description]
                        user_data = dict(zip(col_names, row))
                        user_data.pop("password", None)
                        
                        # Parse JSON fields
                        for col in ["upgrades", "owned_skills", "owned_anime_fruits", 
                                    "job_upgrades", "crafted_items", "fruit_awakenings", 
                                    "equipped_skills", "unlocked_jobs"]:
                            val = user_data.get(col, "")
                            if isinstance(val, str):
                                try:
                                    user_data[col] = json.loads(val)
                                except:
                                    pass
                        
                        json_str = json.dumps(user_data)
                        await websocket.send_text(f"LOGIN_OK {json_str}\n")
                    else:
                        await websocket.send_text("LOGIN_FAIL Invalid credentials\n")
                except Exception as e:
                    await websocket.send_text(f"LOGIN_FAIL {str(e)}\n")
                    
            elif cmd == "SAVE":
                if not username:
                    await websocket.send_text("SAVE_FAIL Log in first\n")
                else:
                    try:
                        save_data = json.loads(args)
                        cursor.execute("""
                            UPDATE users SET
                                gold = ?, diamonds = ?, high_score = ?, player_job = ?, equipped_fruit = ?,
                                upgrades = ?, owned_skills = ?, owned_anime_fruits = ?, job_upgrades = ?,
                                crafted_items = ?, fruit_awakenings = ?, equipped_skills = ?, unlocked_jobs = ?
                            WHERE username = ?
                        """, (
                            save_data.get("gold", 0),
                            save_data.get("diamonds", 0),
                            save_data.get("high_score", 0),
                            save_data.get("player_job", ""),
                            save_data.get("equipped_fruit", ""),
                            json.dumps(save_data.get("upgrades", [0]*6)),
                            json.dumps(save_data.get("owned_skills", {})),
                            json.dumps(save_data.get("owned_anime_fruits", {})),
                            json.dumps(save_data.get("job_upgrades", {})),
                            json.dumps(save_data.get("crafted_items", {})),
                            json.dumps(save_data.get("fruit_awakenings", {})),
                            json.dumps(save_data.get("equipped_skills", [])),
                            json.dumps(save_data.get("unlocked_jobs", [])),
                            username
                        ))
                        db.commit()
                        await websocket.send_text("SAVE_OK\n")
                    except Exception as e:
                        await websocket.send_text(f"SAVE_FAIL {str(e)}\n")
            db.close()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Auth WS error: {e}")

# Active queues for matchmaking
queues = {
    "1v1": [], # list of (WebSocket, username)
    "coop": []
}

@app.websocket("/match")
async def websocket_match(websocket: WebSocket):
    await websocket.accept()
    username = None
    try:
        while True:
            data = await websocket.receive_text()
            line = data.strip()
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
                        for m in queues:
                            queues[m] = [p for p in queues[m] if p[1] != username]
                        queues[mode].append((websocket, username))
                        await websocket.send_text("MATCH_QUEUED\n")
                        print(f"[Matchmaking] {username} queued for {mode}")
                        
                        # Match checking
                        q = queues[mode]
                        if len(q) >= 2:
                            p1_ws, p1_user = q.pop(0)
                            p2_ws, p2_user = q.pop(0)
                            session_id = str(uuid.uuid4())[:8]
                            
                            # The C++ client expects to connect to local port 9002 (local_proxy relay listener)
                            await p1_ws.send_text(f"MATCHED HOST 127.0.0.1 9002 {session_id} {p2_user}\n")
                            await p2_ws.send_text(f"MATCHED CLIENT 127.0.0.1 9002 {session_id} {p1_user}\n")
                            print(f"[Matchmaking] Paired {p1_user} and {p2_user}. Session: {session_id}")
                    else:
                        await websocket.send_text("MATCH_FAIL Invalid mode\n")
                except Exception as e:
                    await websocket.send_text(f"MATCH_FAIL {str(e)}\n")
                    
            elif cmd == "CANCEL":
                u = args.strip() or username
                if u:
                    for m in queues:
                        queues[m] = [p for p in queues[m] if p[1] != u]
                    await websocket.send_text("CANCEL_OK\n")
    except WebSocketDisconnect:
        pass
    finally:
        if username:
            for m in queues:
                queues[m] = [p for p in queues[m] if p[1] != username]

# Relay sessions: session_id -> { "HOST": WebSocket, "CLIENT": WebSocket, "event": asyncio.Event() }
relay_sessions = {}
relay_lock = asyncio.Lock()

@app.websocket("/relay/{session_id}")
async def websocket_relay(websocket: WebSocket, session_id: str):
    await websocket.accept()
    role = None
    try:
        # Read the INIT line
        init_data = await websocket.receive_text()
        line = init_data.strip()
        parts = line.split(" ")
        if len(parts) < 4 or parts[0].upper() != "INIT":
            await websocket.close()
            return
        
        role = parts[2].upper() # HOST or CLIENT
        username = parts[3]
        
        async with relay_lock:
            if session_id not in relay_sessions:
                relay_sessions[session_id] = {
                    "HOST": None,
                    "CLIENT": None,
                    "event": asyncio.Event()
                }
            session = relay_sessions[session_id]
            session[role] = websocket
            
            ready = session["HOST"] is not None and session["CLIENT"] is not None
            if ready:
                session["event"].set()
                
        if not ready:
            try:
                await asyncio.wait_for(session["event"].wait(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.close()
                return
                
        # Relaying loop
        other_role = "CLIENT" if role == "HOST" else "HOST"
        other_ws = session[other_role]
        
        while True:
            message = await websocket.receive()
            if "bytes" in message:
                await other_ws.send_bytes(message["bytes"])
            elif "text" in message:
                await other_ws.send_text(message["text"])
            else:
                break
    except WebSocketDisconnect:
        pass
    finally:
        async with relay_lock:
            if session_id in relay_sessions:
                session = relay_sessions[session_id]
                other_role = "CLIENT" if role == "HOST" else "HOST"
                if session[other_role]:
                    try:
                        await session[other_role].close()
                    except:
                        pass
                del relay_sessions[session_id]
