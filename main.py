import subprocess
import uuid
import os
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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
    cookies_path = f"/tmp/{uid}_cookies.txt"

    try:
        # تحميل الكوكيز من Environment Variables
        cookies_data = os.environ.get("YT_COOKIES")
        if not cookies_data:
            return JSONResponse(
                status_code=500,
                content={"error": "YT_COOKIES not found in environment"}
            )

        # كتابة الكوكيز في ملف مؤقت
        with open(cookies_path, "w") as f:
            f.write(cookies_data)

        # تحميل الفيديو باستعمال yt-dlp + cookies
        subprocess.run(
            [
                "yt-dlp",
                "--cookies", cookies_path,
                "-f", "bv*+ba/b",
                "--merge-output-format", "mp4",
                "-o", inp,
                url
            ],
            check=True
        )

        # قص الفيديو (إعادة ترميز مضمونة)
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
        for f in [inp, out, cookies_path]:
            if f and os.path.exists(f):
                os.remove(f)
