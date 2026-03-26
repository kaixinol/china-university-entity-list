# China University Entity List

Small Python project that scrapes the BIS Entity List, filters China university-like entities, and writes `data.json`. The frontend is a static `index.html` that loads `data.json` with `fetch()`.

## Run

```bash
python scraper.py
python -m http.server
```

Then open `http://127.0.0.1:8000/`.

## Automation

GitHub Actions updates `data.json` automatically on the 1st of each month, and can also be triggered manually from `workflow_dispatch`.
