## Clearcut

A small local web app that removes image backgrounds with U2Net.

### Run

```powershell
uv sync
uv run uvicorn main:app --reload
```

Open http://127.0.0.1:8000, then drop in a JPG, PNG, or WebP image (up to 20 MB).

The app uses `u2net.onnx` from the project directory when available. In deployments
without the local model, it downloads the smaller U2NetP model to temporary storage
on the first request. Set `U2NET_MODEL_URL` to a reachable model URL to use another
model.
