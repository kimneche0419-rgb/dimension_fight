from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import os

app = FastAPI(title="Dimension Fight API")

# Path to save data
SAVE_FILE = "save_data.json"

class SaveData(BaseModel):
    data: dict

@app.get("/api/load")
async def load_game():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return {}

@app.post("/api/save")
async def save_game(save_data: SaveData):
    with open(SAVE_FILE, "w") as f:
        json.dump(save_data.data, f)
    return {"status": "success"}

# Serve the game build directory (after pygbag build)
# Note: The 'build/web' folder is where pygbag puts the output
if os.path.exists("build/web"):
    app.mount("/", StaticFiles(directory="build/web", html=True), name="static")

@app.get("/")
async def read_index():
    if os.path.exists("build/web/index.html"):
        return FileResponse("build/web/index.html")
    return {"message": "Game not built yet. Run 'pygbag .' to build the web version."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
