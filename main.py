import subprocess, uuid
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse

app = FastAPI()

@app.post("/clip")
def clip(url: str = Form(...), start: int = Form(...), end: int = Form(...)):
    uid = str(uuid.uuid4())
    inp = f"/tmp/{uid}.mp4"
    out = f"/tmp/{uid}_cut.mp4"

    subprocess.run(["yt-dlp","-f","mp4","-o",inp,url], check=True)
    subprocess.run(["ffmpeg","-ss",str(start),"-to",str(end),"-i",inp,"-c","copy",out], check=True)

    return FileResponse(out, media_type="video/mp4", filename="clip.mp4")
