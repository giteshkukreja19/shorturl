from flask import Flask, render_template, request, jsonify, redirect, send_file
import sqlite3
import secrets
import string
import re
import os
from urllib.parse import urlparse
from datetime import datetime, timezone
from io import BytesIO
import qrcode
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
DATABASE = os.environ.get("DATABASE_PATH", "shortlinks.db")
CODE_LENGTH = 7
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")

if PUBLIC_BASE_URL:
    parsed_public_url = urlparse(PUBLIC_BASE_URL)
    if (
        parsed_public_url.scheme not in ("http", "https")
        or not parsed_public_url.hostname
        or parsed_public_url.username
        or parsed_public_url.password
        or parsed_public_url.query
        or parsed_public_url.fragment
        or any(char.isspace() for char in PUBLIC_BASE_URL)
    ):
        raise ValueError(
            "PUBLIC_BASE_URL must be an absolute HTTP or HTTPS URL without "
            "credentials, a query, or a fragment."
        )


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            short_code TEXT UNIQUE NOT NULL,
            clicks INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def validate_url(url):
    if not isinstance(url, str) or len(url) > 2048:
        return False
    try:
        parsed = urlparse(url.strip())
        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.hostname)
            and not any(char.isspace() for char in url)
        )
    except ValueError:
        return False


def generate_code(conn):
    characters = string.ascii_letters + string.digits
    while True:
        code = "".join(secrets.choice(characters) for _ in range(CODE_LENGTH))
        existing = conn.execute(
            "SELECT 1 FROM urls WHERE short_code = ?", (code,)
        ).fetchone()
        if not existing:
            return code


def public_url(path=""):
    base_url = PUBLIC_BASE_URL or request.url_root.rstrip("/")
    return f"{base_url}/{path.lstrip('/')}"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/shorten", methods=["POST"])
def shorten_url():
    data = request.get_json(silent=True) or {}
    raw_url = data.get("url", "")
    original_url = raw_url.strip() if isinstance(raw_url, str) else ""

    if not validate_url(original_url):
        return jsonify({"error": "Please enter a valid HTTP or HTTPS URL."}), 400

    conn = get_db()
    existing = conn.execute(
        "SELECT short_code FROM urls WHERE original_url = ?", (original_url,)
    ).fetchone()

    if existing:
        code = existing["short_code"]
    else:
        code = generate_code(conn)
        conn.execute("""
            INSERT INTO urls (original_url, short_code, clicks, created_at)
            VALUES (?, ?, 0, ?)
        """, (original_url, code, datetime.now(timezone.utc).isoformat()))
        conn.commit()

    conn.close()
    short_url = public_url(code)
    return jsonify({
        "success": True,
        "original_url": original_url,
        "short_url": short_url,
        "qr_url": public_url(f"qr/{code}"),
        "short_code": code
    })


@app.route("/<code>")
def redirect_url(code):
    if not re.fullmatch(r"[A-Za-z0-9]{7}", code):
        return "Invalid short link", 404

    conn = get_db()
    result = conn.execute(
        "SELECT original_url FROM urls WHERE short_code = ?", (code,)
    ).fetchone()

    if result is None:
        conn.close()
        return "Short link not found", 404

    original_url = result["original_url"]
    conn.execute(
        "UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?", (code,)
    )
    conn.commit()
    conn.close()
    return redirect(original_url, code=302)


@app.route("/api/links")
def get_links():
    conn = get_db()
    links = conn.execute("""
        SELECT original_url, short_code, clicks, created_at
        FROM urls ORDER BY id DESC LIMIT 50
    """).fetchall()
    total_links = conn.execute("SELECT COUNT(*) FROM urls").fetchone()[0]
    total_clicks = conn.execute(
        "SELECT COALESCE(SUM(clicks), 0) FROM urls"
    ).fetchone()[0]
    conn.close()

    return jsonify({
        "total_links": total_links,
        "total_clicks": total_clicks,
        "links": [
            {**dict(link), "short_url": public_url(link["short_code"])}
            for link in links
        ]
    })


@app.route("/qr/<code>")
def generate_qr(code):
    if not re.fullmatch(r"[A-Za-z0-9]{7}", code):
        return "Invalid code", 400

    conn = get_db()
    result = conn.execute(
        "SELECT short_code FROM urls WHERE short_code = ?", (code,)
    ).fetchone()
    conn.close()

    if result is None:
        return "Link not found", 404

    short_url = public_url(code)
    qr = qrcode.make(short_url)
    image_buffer = BytesIO()
    qr.save(image_buffer, format="PNG")
    image_buffer.seek(0)
    return send_file(
        image_buffer,
        mimetype="image/png",
        download_name="shortlink-qr.png"
    )


initialize_database()


if __name__ == "__main__":
    # Local development only. Turn debug off before deployment.
    app.run(host="127.0.0.1", port=5000, debug=True)
