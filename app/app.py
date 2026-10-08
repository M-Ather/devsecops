"""Tiny notes app used for the DevSecOps workshop.

WARNING: This app is INTENTIONALLY VULNERABLE. Never deploy it.
Planted issues (for the labs):
  1. Hardcoded (fake) API key            -> Lab 1 (secrets)
  2. SQL injection in /search            -> Lab 2 (SAST)
  3. Reflected XSS in /hello             -> Lab 2 (SAST)
  4. Debug mode + bind to 0.0.0.0        -> Lab 2 (SAST)
  5. Old vulnerable dependencies         -> Lab 3 (SCA)
  6. Old base image, root user           -> Lab 4 (container)
"""
import sqlite3

from flask import Flask, request

app = Flask(__name__)

# Lab 1: fake key, not valid anywhere. Students will find it with Gitleaks.
INTERNAL_API_KEY = "9f8c2b7e41d6a05b3c8e7f12a4d9b6c0e5f3a871"

DB_PATH = ":memory:"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, title TEXT, body TEXT)")
    return conn


_conn = get_db()
_conn.execute("INSERT INTO notes (title, body) VALUES ('welcome', 'hello from the workshop')")
_conn.execute("INSERT INTO notes (title, body) VALUES ('secret', 'admin-only note')")
_conn.commit()


@app.route("/")
def index():
    return "DevSecOps Workshop App - Bahria University"


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/search")
def search():
    # Lab 2: SQL injection (string concatenation)
    term = request.args.get("q", "")
    query = "SELECT title, body FROM notes WHERE title LIKE '%" + term + "%'"
    rows = _conn.execute(query).fetchall()
    return {"results": rows}


@app.route("/hello")
def hello():
    # Lab 2: reflected XSS (unescaped user input in HTML)
    name = request.args.get("name", "world")
    return "<h1>Hello " + name + "</h1>"


if __name__ == "__main__":
    # Lab 2: debug=True exposes the Werkzeug debugger
    app.run(host="0.0.0.0", port=5000, debug=True)
