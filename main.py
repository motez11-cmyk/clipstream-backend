import subprocess
import uuid
import os
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# (اختياري لكن مفيد) CORS باش الواجهة تخدم بلا مشاكل
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
        # 1) تحميل الفيديو
        subprocess.run(
            ["yt-dlp", "-f", "mp4", "-o", inp, url],
            check=True
        )

        # 2) قص الفيديو (إعادة ترميز – مضمون)
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
            content={"error": "processing failed", "details": str(e)}
        )

    finally:
        # تنظيف الملفات
        if os.path.exists(inp):
            os.remove(inp)
        if os.path.exists(out):
            os.remove(out)
