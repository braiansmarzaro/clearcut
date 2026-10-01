## Clearcut

A small local web app that removes image backgrounds with `rembg` and the bundled U2Net model.

### Run

```powershell
uv sync
uv run uvicorn main:app --reload
```

Open http://127.0.0.1:8000, then drop in a JPG, PNG, or WebP image (up to 20 MB).
