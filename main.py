import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from rembg import new_session, remove

BASE_DIR = Path(__file__).resolve().parent
MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

os.environ.setdefault("U2NET_HOME", str(BASE_DIR))


@lru_cache(maxsize=1)
def get_rembg_session():
    return new_session("u2net")


def process_image(image: bytes) -> bytes:
    return remove(
        image,
        session=get_rembg_session(),
        force_return_bytes=True,
    )


app = FastAPI(title="Clearcut")


@app.post("/api/remove-background")
async def remove_background(request: Request) -> Response:
    content_type = request.headers.get("content-type", "").split(";", 1)[0]
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Upload a JPG, PNG, or WebP image.")

    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_FILE_SIZE:
        raise HTTPException(413, "Image must be smaller than 20 MB.")

    image = await request.body()
    if not image:
        raise HTTPException(400, "The uploaded image is empty.")
    if len(image) > MAX_FILE_SIZE:
        raise HTTPException(413, "Image must be smaller than 20 MB.")

    try:
        output = await run_in_threadpool(process_image, image)
    except Exception as error:
        raise HTTPException(422, "The image could not be processed.") from error

    return Response(
        content=output,
        media_type="image/png",
        headers={"Content-Disposition": 'attachment; filename="background-removed.png"'},
    )


app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")