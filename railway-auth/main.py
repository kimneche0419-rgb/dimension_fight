import asyncio
import os
import sqlite3
import json
import traceback

DB_URL = os.environ.get("DATABASE_URL")
IS_POSTGRES = False

if DB_URL:
    try:
        import psycopg2
        # Simple connection test
        conn = psycopg2.connect(DB_URL)
        conn.close()
        IS_POSTGRES = True
        print("[DB] PostgreSQL connection successful.")
    except Exception as e:
        print(f"[DB] Failed to connect to PostgreSQL ({e}). Falling back to SQLite.")
        IS_POSTGRES = False

def init_db():
    query = """
    CREATE TABLE IF NOT EXISTS users (
        username VARCHAR(255) PRIMARY KEY,
        password VARCHAR(255) NOT NULL,
        gold INTEGER DEFAULT 0,
        diamonds INTEGER DEFAULT 0,
        high_score INTEGER DEFAULT 0,
        player_job VARCHAR(255) DEFAULT '',
        equipped_fruit VARCHAR(255) DEFAULT '',
        upgrades TEXT DEFAULT '[0,0,0,0,0,0]',
        owned_skills TEXT DEFAULT '{}',
        owned_anime_fruits TEXT DEFAULT '{}',
        job_upgrades TEXT DEFAULT '{}',
        crafted_items TEXT DEFAULT '{}',
        fruit_awakenings TEXT DEFAULT '{}',
        equipped_skills TEXT DEFAULT '[]',
        unlocked_jobs TEXT DEFAULT '["전사", "저격수", "파일럿", "마법사", "흡혈귀", "기계공", "탱커", "광속", "차원술사", "학살자"]'
    )
    """
    if IS_POSTGRES:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        conn.close()
        print("[DB] PostgreSQL Database Initialized.")
    else:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        conn.close()
        print("[DB] SQLite Database Initialized.")

def execute_query(query, params=()):
    if IS_POSTGRES:
        query = query.replace("?", "%s")
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()
    else:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()

def fetch_one(query, params=()):
    if IS_POSTGRES:
        query = query.replace("?", "%s")
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        desc = cursor.description
        conn.close()
        return row, desc
    else:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        desc = cursor.description
        conn.close()
        return row, desc

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"[Auth Server] Connected: {addr}")
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

            if cmd == "REGISTER":
                try:
                    u, p = args.split(" ", 1)
                    execute_query("INSERT INTO users (username, password) VALUES (?, ?)", (u, p))
                    writer.write(b"REGISTER_OK\n")
                    await writer.drain()
                    print(f"[Auth Server] Registered new user: {u}")
                except Exception as e:
                    # SQLite IntegrityError or Postgres UniqueViolation
                    err_msg = str(e)
                    if "UNIQUE" in err_msg or "already exists" in err_msg or "Duplicate" in err_msg:
                        writer.write(b"REGISTER_FAIL User already exists\n")
                    else:
                        writer.write(f"REGISTER_FAIL {err_msg}\n".encode("utf-8"))
                    await writer.drain()

            elif cmd == "LOGIN":
                try:
                    u, p = args.split(" ", 1)
                    row, desc = fetch_one("SELECT * FROM users WHERE username=? AND password=?", (u, p))
                    if row:
                        username = u
                        col_names = [d[0] for d in desc]
                        user_data = dict(zip(col_names, row))
                        user_data.pop("password", None)

                        # Parse JSON columns back
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
                        writer.write(f"LOGIN_OK {json_str}\n".encode("utf-8"))
                        await writer.drain()
                        print(f"[Auth Server] User logged in: {u}")
                    else:
                        writer.write(b"LOGIN_FAIL Invalid credentials\n")
                        await writer.drain()
                except Exception as e:
                    writer.write(f"LOGIN_FAIL {str(e)}\n".encode("utf-8"))
                    await writer.drain()

            elif cmd == "SAVE":
                if not username:
                    writer.write(b"SAVE_FAIL Log in first\n")
                    await writer.drain()
                else:
                    try:
                        save_data = json.loads(args)
                        execute_query("""
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
                        writer.write(b"SAVE_OK\n")
                        await writer.drain()
                        print(f"[Auth Server] Saved user data for {username}")
                    except Exception as e:
                        writer.write(f"SAVE_FAIL {str(e)}\n".encode("utf-8"))
                        await writer.drain()
    except Exception as e:
        print(f"[Auth Server] Error handling client {addr}: {e}")
        traceback.print_exc()
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"[Auth Server] Disconnected: {addr}")

async def main():
    init_db()
    port = int(os.environ.get("PORT", 9000))
    server = await asyncio.start_server(handle_client, '0.0.0.0', port)
    print(f"[Auth Server] Listening on port {port}...")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
