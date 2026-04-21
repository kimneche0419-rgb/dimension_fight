import json
import os
import asyncio
import platform

# Detect if running in browser
IS_WEB = platform.system() == "Emscripten"

class SaveManager:
    @staticmethod
    def save(data, filename="save_data.json"):
        if IS_WEB:
            try:
                import browser
                browser.window.localStorage.setItem("game_save", json.dumps(data))
                
                # Async sync to server
                async def sync_to_server():
                    browser.window.eval(f"""
                        fetch('/api/save', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ data: {json.dumps(data)} }})
                        }}).catch(err => console.error("Server save failed", err));
                    """)
                asyncio.create_task(sync_to_server())
            except Exception as e:
                print(f"Web save error: {e}")
        else:
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)

    @staticmethod
    def load(filename="save_data.json"):
        if IS_WEB:
            try:
                import browser
                stored = browser.window.localStorage.getItem("game_save")
                if stored:
                    return json.loads(stored)
            except:
                pass
            
            # If not in localStorage, maybe it's in the virtual FS (pre-bundled)
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    return json.load(f)
        else:
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    return json.load(f)
        return {}
