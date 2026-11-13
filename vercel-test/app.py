"""Mini projet de test pour Vercel : vérifie (1) la recherche d'emails sur un site
d'entreprise et (2) la connexion SMTP sortante. Aucune base de données."""
import re
import smtplib
import ssl
import time

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)  # Vercel cherche une variable nommée "app"

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
BAD = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", "sentry", "example.", "wixpress", "@2x")


def find_emails(url, errors):
    """Même logique que cv_tools.find_emails, mais remplit `errors` pour le diagnostic."""
    found = []
    for u in (url, url.rstrip("/") + "/contact"):
        try:
            r = requests.get(u, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            if r.ok:
                found += EMAIL_RE.findall(r.text)
            else:
                errors.append(f"HTTP {r.status_code} sur {u}")
        except requests.exceptions.RequestException as exc:
            errors.append(f"{type(exc).__name__} sur {u}: {exc}")
    out = []
    for e in found:
        e = e.lower()
        if not any(b in e for b in BAD) and e not in out:
            out.append(e)
    return out[:5]


@app.get("/")
def home():
    return (
        "<h2>Test Vercel - Khedma Marrakech</h2><ul>"
        "<li><a href='/find?url=https://techspace.ma'>/find?url=...</a> : recherche d'email</li>"
        "<li><a href='/smtp'>/smtp</a> : connexion SMTP sortante (port 587)</li></ul>"
    )


@app.get("/find")
def find():
    url = (request.args.get("url") or "").strip()
    if not url.startswith("http"):
        return jsonify(ok=False, error="Ajoutez ?url=https://site-de-l-entreprise.ma"), 400
    errors, t0 = [], time.time()
    emails = find_emails(url, errors)
    return jsonify(ok=bool(emails), emails=emails, errors=errors, seconds=round(time.time() - t0, 1))


@app.get("/smtp")
def smtp_test():
    t0 = time.time()
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as s:
            s.ehlo()
            s.starttls(context=ssl.create_default_context())
            s.ehlo()
        return jsonify(ok=True, message="Connexion SMTP (587 + STARTTLS) reussie", seconds=round(time.time() - t0, 1))
    except Exception as exc:
        return jsonify(ok=False, error=f"{type(exc).__name__}: {exc}", seconds=round(time.time() - t0, 1)), 502
