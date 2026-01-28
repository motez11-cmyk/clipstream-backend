import subprocess
import uuid
import os
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS (باش الواجهة تخدم من Netlify)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/clip")
def clip(
    url: str = Form(...),
    start: int = Form(...),
    end: int = Form(...)
):
    if end <= start:
        return JSONResponse(
            status_code=400,
            content={"error": "end must be greater than start"}
        )

    uid = str(uuid.uuid4())
    inp = f"/tmp/{uid}.mp4"
    out = f"/tmp/{uid}_cut.mp4"

    try:
        # 1️⃣ تحميل الفيديو (best video + best audio → mp4)
        subprocess.run(
            [
                "yt-dlp",
                "-f", "bv*+ba/b",
                "--merge-output-format", "mp4",
                "-o", inp,
                url
            ],
            check=True
        )

        # 2️⃣ قص الفيديو (إعادة ترميز – مضمون)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", inp,
                "-ss", str(start),
                "-to", str(end),
                "-map", "0:v:0",
                "-map", "0:a:0?",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-movflags", "+faststart",
                out
            ],
            check=True
        )

        return FileResponse(
            out,
            media_type="video/mp4",
            filename="clip.mp4"
        )

    except subprocess.CalledProcessError as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "processing failed",
                "details": str(e)
            }
        )

    finally:
        # تنظيف الملفات المؤقتة
        if os.path.exists(inp):
            os.remove(inp)
        if os.path.exists(out):
            os.remove(out)
