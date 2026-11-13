# ShortLink - Python URL Shortener

A URL-shortening website built with Flask, SQLite, HTML, CSS and JavaScript.

## Requirements
- Python 3.9 or newer
- pip

## Run on macOS

```bash
cd shortlink
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Open http://127.0.0.1:5000 in your browser. Without additional configuration,
generated links use the host from the incoming request, so locally they use
`127.0.0.1`.

The SQLite database (`shortlinks.db`) is created automatically on first run.

## Features
- Shorten HTTP and HTTPS URLs
- Redirect short links to their original destinations
- Count link clicks
- Dashboard with recent links and totals
- Generate and download QR codes

## Use a public link

`render.yaml` configures a public Render web service, Gunicorn, and a persistent
disk for the SQLite database. Deploy this project to Render from a connected
Git repository. The Render service URL is publicly reachable and can be shared.

To use your own domain, add a domain you own in the Render service's Custom
Domains settings and configure the DNS records Render provides at your domain
registrar. Then set `PUBLIC_BASE_URL` in the Render service environment to
`https://your-domain.example` and redeploy. The app uses it for generated links,
dashboard links, and QR codes. A custom domain and DNS access are required;
they cannot be created by this project.

The Render configuration uses a paid instance and persistent disk so created
links survive restarts. The database is initialized automatically at startup.

## Important
This project is not production-hardened. Before public deployment, disable
Flask debug mode and add authentication, rate limiting, abuse prevention, and
production-grade hosting/database configuration.
# shorturl
