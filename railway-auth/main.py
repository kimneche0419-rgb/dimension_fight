import asyncio
import os
import sqlite3
import json
import traceback
import bcrypt
import hmac
import hashlib
import time

DB_URL = os.environ.get("DATABASE_URL")
IS_POSTGRES = False

# Shared secret used to sign session tokens handed to railway-match and
# railway-relay so they can verify a caller actually owns the username they
# claim, without a network round-trip back to this service. MUST be set to
# the same value (via the AUTH_SHARED_SECRET env var) on all three services.
AUTH_SHARED_SECRET = os.environ.get("AUTH_SHARED_SECRET", "dev-insecure-shared-secret-change-me")
SESSION_TOKEN_TTL_SECONDS = 12 * 3600

def make_session_token(username: str) -> str:
    expiry = int(time.time()) + SESSION_TOKEN_TTL_SECONDS
    payload = f"{username}.{expiry}"
    sig = hmac.new(AUTH_SHARED_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"

def build_login_payload(u, user_data):
    """Turn a raw DB row dict for username u into the LOGIN_OK JSON payload."""
    user_data = dict(user_data)
    user_data.pop("password", None)

    for col in ["owned_skills", "owned_anime_fruits", "job_upgrades",
                "crafted_items", "fruit_awakenings", "equipped_skills",
                "unlocked_jobs", "ship_levels"]:
        val = user_data.get(col, "")
        if isinstance(val, str):
            try:
                user_data[col] = json.loads(val)
            except Exception:
                pass

    # Expand the stored "upgrades" array into the individual keys the
    # C++ client's SaveData::load() actually parses (save.h).
    upgrades_raw = user_data.pop("upgrades", "[0,0,0,0,0,0]")
    try:
        upgrades_list = json.loads(upgrades_raw) if isinstance(upgrades_raw, str) else upgrades_raw
    except Exception:
        upgrades_list = [0] * 6
    upgrades_list = (upgrades_list + [0] * 6)[:6]
    for key, val in zip(UPGRADE_KEYS, upgrades_list):
        user_data[key] = val

    user_data["session_token"] = make_session_token(u)
    return json.dumps(user_data)

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

# Individual upgrade keys as used by the C++ client's SaveData (save.h), in
# the fixed order matching SaveData::upgrades[6] (shield, speed, hp, xp, dash, dmg).
UPGRADE_KEYS = ["shield_boost", "speed_boost", "hp_boost", "xp_bonus", "dash_cdr", "dmg_boost"]

# Columns added after the initial schema. Each entry is (column_name, sql_type_and_default).
EXTRA_COLUMNS = [
    ("max_unlocked_chapter", "INTEGER DEFAULT 1"),
    ("crystals", "INTEGER DEFAULT 0"),
    ("boss_cores", "INTEGER DEFAULT 0"),
    ("void_essences", "INTEGER DEFAULT 0"),
    ("abyss_pearls", "INTEGER DEFAULT 0"),
    ("time_shards", "INTEGER DEFAULT 0"),
    ("gacha_tickets", "INTEGER DEFAULT 100"),
    ("gacha_pity_count", "INTEGER DEFAULT 0"),
    ("equipped_ship", "VARCHAR(255) DEFAULT 'fighter'"),
    ("ship_levels", "TEXT DEFAULT '{\"fighter\": 1}'"),
]

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, stored: str) -> bool:
    if stored.startswith("$2"):
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))
        except ValueError:
            return False
    # Legacy plaintext row from before hashing was introduced.
    return plain == stored

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

    migrate_schema()

def migrate_schema():
    """Add columns introduced after the initial schema to existing databases."""
    for col_name, col_def in EXTRA_COLUMNS:
        try:
            execute_query(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
            print(f"[DB] Migrated: added column '{col_name}'.")
        except Exception as e:
            err = str(e).lower()
            if "duplicate column" in err or "already exists" in err:
                pass  # Column already present, nothing to do.
            else:
                print(f"[DB] Migration warning for column '{col_name}': {e}")

def execute_query(query, params=()):
    # @MX:ANCHOR: 모든 DB 쓰기가 통과하는 단일 관문
    # @MX:REASON: 커넥션을 try/finally로 닫지 않으면 쿼리 실패 시(예: 중복 키 INSERT) 잠금이
    #             풀리지 않아 이후 모든 쓰기가 "database is locked"로 실패함
    if IS_POSTGRES:
        query = query.replace("?", "%s")
        conn = psycopg2.connect(DB_URL)
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = sqlite3.connect("users.db", timeout=10)
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

def fetch_one(query, params=()):
    if IS_POSTGRES:
        query = query.replace("?", "%s")
        conn = psycopg2.connect(DB_URL)
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            desc = cursor.description
            return row, desc
        finally:
            conn.close()
    else:
        conn = sqlite3.connect("users.db", timeout=10)
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            desc = cursor.description
            return row, desc
        finally:
            conn.close()

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
                    execute_query("INSERT INTO users (username, password) VALUES (?, ?)", (u, hash_password(p)))
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
                    row, desc = fetch_one("SELECT * FROM users WHERE username=?", (u,))
                    col_names = [d[0] for d in desc] if desc else []
                    user_data = dict(zip(col_names, row)) if row else None

                    if user_data and verify_password(p, user_data["password"]):
                        # Lazily upgrade legacy plaintext rows to a bcrypt hash on successful login.
                        if not user_data["password"].startswith("$2"):
                            execute_query("UPDATE users SET password = ? WHERE username = ?", (hash_password(p), u))

                        username = u
                        json_str = build_login_payload(u, user_data)
                        writer.write(f"LOGIN_OK {json_str}\n".encode("utf-8"))
                        await writer.drain()
                        print(f"[Auth Server] User logged in: {u}")
                    else:
                        writer.write(b"LOGIN_FAIL Invalid credentials\n")
                        await writer.drain()
                except Exception as e:
                    writer.write(f"LOGIN_FAIL {str(e)}\n".encode("utf-8"))
                    await writer.drain()

            elif cmd == "LOGIN_TOKEN":
                # Passwordless re-login for the client's "remember me" auto-login,
                # using the short-lived session token issued at the last LOGIN
                # instead of storing the plaintext password on disk.
                try:
                    u, token = args.split(" ", 1)
                    if not verify_session_token(u, token):
                        writer.write(b"LOGIN_FAIL Invalid or expired session\n")
                        await writer.drain()
                    else:
                        row, desc = fetch_one("SELECT * FROM users WHERE username=?", (u,))
                        col_names = [d[0] for d in desc] if desc else []
                        user_data = dict(zip(col_names, row)) if row else None
                        if user_data:
                            username = u
                            json_str = build_login_payload(u, user_data)
                            writer.write(f"LOGIN_OK {json_str}\n".encode("utf-8"))
                            await writer.drain()
                            print(f"[Auth Server] User re-logged in via token: {u}")
                        else:
                            writer.write(b"LOGIN_FAIL Invalid or expired session\n")
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

                        # The C++ client sends individual upgrade keys (save.h), not an
                        # "upgrades" array — pack them back into the array the DB stores.
                        upgrades_list = [save_data.get(key, 0) for key in UPGRADE_KEYS]

                        execute_query("""
                            UPDATE users SET
                                gold = ?, diamonds = ?, high_score = ?, player_job = ?, equipped_fruit = ?,
                                upgrades = ?, owned_skills = ?, owned_anime_fruits = ?, job_upgrades = ?,
                                crafted_items = ?, fruit_awakenings = ?, equipped_skills = ?, unlocked_jobs = ?,
                                max_unlocked_chapter = ?, crystals = ?, boss_cores = ?, void_essences = ?,
                                abyss_pearls = ?, time_shards = ?, gacha_tickets = ?, gacha_pity_count = ?,
                                equipped_ship = ?, ship_levels = ?
                            WHERE username = ?
                        """, (
                            save_data.get("gold", 0),
                            save_data.get("diamonds", 0),
                            save_data.get("high_score", 0),
                            save_data.get("player_job", ""),
                            save_data.get("equipped_fruit", ""),
                            json.dumps(upgrades_list),
                            json.dumps(save_data.get("owned_skills", {})),
                            json.dumps(save_data.get("owned_anime_fruits", {})),
                            json.dumps(save_data.get("job_upgrades", {})),
                            json.dumps(save_data.get("crafted_items", {})),
                            json.dumps(save_data.get("fruit_awakenings", {})),
                            json.dumps(save_data.get("equipped_skills", [])),
                            json.dumps(save_data.get("unlocked_jobs", [])),
                            save_data.get("max_unlocked_chapter", 1),
                            save_data.get("crystals", 0),
                            save_data.get("boss_cores", 0),
                            save_data.get("void_essences", 0),
                            save_data.get("abyss_pearls", 0),
                            save_data.get("time_shards", 0),
                            save_data.get("gacha_tickets", 100),
                            save_data.get("gacha_pity_count", 0),
                            save_data.get("equipped_ship", "fighter"),
                            json.dumps(save_data.get("ship_levels", {"fighter": 1})),
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
    if AUTH_SHARED_SECRET == "dev-insecure-shared-secret-change-me":
        print("[Auth Server] WARNING: AUTH_SHARED_SECRET is not set. Using an insecure default. "
              "Set the same AUTH_SHARED_SECRET env var on railway-auth, railway-match and railway-relay before deploying.")
    init_db()
    port = int(os.environ.get("PORT", 9000))
    server = await asyncio.start_server(handle_client, '0.0.0.0', port)
    print(f"[Auth Server] Listening on port {port}...")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
