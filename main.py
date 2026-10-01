import io
import os
import urllib.request
from functools import lru_cache
from pathlib import Path

import numpy as np
import onnxruntime
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MODEL_PATH = BASE_DIR / "u2net.onnx"
MODEL_CACHE_PATH = Path("/tmp/u2net.onnx")
MODEL_URL = os.environ.get(
    "U2NET_MODEL_URL",
    "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx",
)


@lru_cache(maxsize=1)
def get_model_path() -> Path:
    if MODEL_PATH.exists():
        return MODEL_PATH
    if not MODEL_CACHE_PATH.exists():
        urllib.request.urlretrieve(MODEL_URL, MODEL_CACHE_PATH)
    return MODEL_CACHE_PATH


@lru_cache(maxsize=1)
def get_session():
    return onnxruntime.InferenceSession(
        str(get_model_path()),
        providers=["CPUExecutionProvider"],
    )


def process_image(image: bytes) -> bytes:
    source = Image.open(io.BytesIO(image)).convert("RGB")
    model_input = np.asarray(
        source.resize((320, 320), Image.Resampling.LANCZOS),
        dtype=np.float32,
    ).transpose(2, 0, 1)[None] / 255.0
    session = get_session()
    output = session.run(
        None,
        {session.get_inputs()[0].name: model_input},
    )[0][:, 0].squeeze()
    output = (output - output.min()) / (output.max() - output.min())
    mask = Image.fromarray((output * 255).astype(np.uint8)).resize(
        source.size,
        Image.Resampling.LANCZOS,
    )
    source.putalpha(mask)

    buffer = io.BytesIO()
    source.save(buffer, format="PNG")
    return buffer.getvalue()


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