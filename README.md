# DevSecOps Workshop Lab: Vulnerable Notes App

Intentionally vulnerable Flask app for the DevSecOps workshop.
**Do not deploy. All secrets are fake.**

- Students: follow `LAB-GUIDE.md`.

## Run locally (optional)

The starter pins old packages (Flask 1.1.2), which need **Python 3.9 or older**. On newer Python, skip this and use Docker below.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest
pytest -q
python app/app.py          # http://127.0.0.1:5000
```

## Docker

```bash
docker build -t workshop-app:local .
docker run --rm -p 5000:5000 workshop-app:local
```

## Planted issues (instructor cheat sheet)

| Lab | Issue | Where |
|---|---|---|
| 1 | Hardcoded fake API key | `app/app.py` |
| 2 | SQL injection `/search`, XSS `/hello`, debug=True | `app/app.py` |
| 3 | Old vulnerable packages | `requirements.txt` |
| 4 | Old base image, root user | `Dockerfile` |
