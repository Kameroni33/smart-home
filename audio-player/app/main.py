import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

import pygame
import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

TRACKS_DIR = Path("/tracks")

# State
state = {
    "track": None,
    "paused": False,
    "volume": 1.0,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=8192)
    pygame.mixer.init()
    pygame.mixer.music.set_volume(state["volume"])
    yield
    pygame.mixer.quit()


app = FastAPI(lifespan=lifespan)


# --- Models ---

class PlayRequest(BaseModel):
    track: str


class VolumeRequest(BaseModel):
    level: int  # 0–100


class DownloadRequest(BaseModel):
    url: str


# --- API Routes ---

@app.get("/tracks")
def list_tracks():
    if not TRACKS_DIR.exists():
        return {"tracks": []}
    files = sorted(
        f.name for f in TRACKS_DIR.iterdir()
        if f.suffix.lower() in (".mp3", ".wav", ".ogg", ".flac")
    )
    return {"tracks": files}


@app.post("/play")
def play(req: PlayRequest):
    track_path = TRACKS_DIR / req.track
    if not track_path.exists():
        raise HTTPException(status_code=404, detail=f"Track not found: {req.track}")

    pygame.mixer.music.load(str(track_path))
    pygame.mixer.music.set_volume(state["volume"])
    pygame.mixer.music.play(loops=-1)  # loop indefinitely

    state["track"] = req.track
    state["paused"] = False
    return {"status": "playing", "track": req.track}


@app.post("/pause")
def pause():
    if state["track"] is None:
        raise HTTPException(status_code=400, detail="Nothing is loaded")

    if state["paused"]:
        pygame.mixer.music.unpause()
        state["paused"] = False
        return {"status": "playing", "track": state["track"]}
    else:
        pygame.mixer.music.pause()
        state["paused"] = True
        return {"status": "paused", "track": state["track"]}


@app.post("/volume")
def set_volume(req: VolumeRequest):
    if not 0 <= req.level <= 100:
        raise HTTPException(status_code=400, detail="Volume must be 0–100")
    vol = req.level / 100.0
    state["volume"] = vol
    pygame.mixer.music.set_volume(vol)
    return {"volume": req.level}


@app.get("/status")
def status():
    return {
        "track": state["track"],
        "paused": state["paused"],
        "playing": state["track"] is not None and not state["paused"],
        "volume": int(state["volume"] * 100),
    }


@app.post("/download")
async def download(req: DownloadRequest):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(TRACKS_DIR / "%(title)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "no_warnings": True,
    }

    def do_download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=True)
            # After FFmpeg post-processing the extension becomes .mp3
            raw_name = Path(ydl.prepare_filename(info)).stem
            return f"{raw_name}.mp3"

    try:
        loop = asyncio.get_running_loop()
        filename = await loop.run_in_executor(None, do_download)
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"track": filename}


# Serve frontend — must be mounted last so API routes take priority
app.mount("/", StaticFiles(directory="/ui", html=True), name="ui")
