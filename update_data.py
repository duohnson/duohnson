#!/usr/bin/env python3
"""Actualiza data.json con la ultima cancion de Spotify + stats de GitHub.
Corre en GitHub Actions (cron) o local. Solo stdlib.

Env vars:
  SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET / SPOTIFY_REFRESH_TOKEN  (opcional)
  GITHUB_TOKEN o GH_TOKEN  (opcional, solo por rate limit; los datos son publicos)
"""
import base64
import json
import os
import time
import urllib.parse
import urllib.request

USER = "duohnson"
ORGS = ["duohnson"]          # orgs donde tambien cuento commits/LOC


def http(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            return r.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        return e.code, {}


# ---------------- Spotify ----------------
def spotify_last_played():
    cid = os.environ.get("SPOTIFY_CLIENT_ID")
    sec = os.environ.get("SPOTIFY_CLIENT_SECRET")
    ref = os.environ.get("SPOTIFY_REFRESH_TOKEN")
    if not (cid and sec and ref):
        print("spotify: sin credenciales, se mantiene el valor anterior")
        return None
    auth = base64.b64encode(f"{cid}:{sec}".encode()).decode()
    code, tok = http(
        "https://accounts.spotify.com/api/token",
        data=urllib.parse.urlencode(
            {"grant_type": "refresh_token", "refresh_token": ref}).encode(),
        headers={"Authorization": f"Basic {auth}",
                 "Content-Type": "application/x-www-form-urlencoded"})
    if code != 200 or "access_token" not in tok:
        print(f"spotify: refresh fallo ({code})")
        return None
    code, rp = http(
        "https://api.spotify.com/v1/me/player/recently-played?limit=1",
        headers={"Authorization": f"Bearer {tok['access_token']}"})
    items = rp.get("items") or []
    if not items:
        print("spotify: sin reproducciones recientes")
        return None
    t = items[0]["track"]
    artists = ", ".join(a["name"] for a in t["artists"])
    return f"{t['name']} - {artists}"


# ---------------- GitHub ----------------
def gh(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER}
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    return http(url, headers=headers)


def github_stats():
    _, owned = gh(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
    repos = list(owned)
    for org in ORGS:
        _, r = gh(f"https://api.github.com/orgs/{org}/repos?per_page=100")
        repos += r or []
    _, u = gh(f"https://api.github.com/users/{USER}")

    commits = adds = dels = 0
    skipped = 0
    for r in repos:
        # /stats/contributors responde 202 mientras calcula: reintentar
        for _ in range(8):
            code, stats = gh(f"https://api.github.com/repos/{r['full_name']}/stats/contributors")
            if code == 200 and isinstance(stats, list):
                break
            if code == 204:          # repo vacio: dato valido, no hay commits
                stats = []
                break
            time.sleep(4)
        else:
            print(f"stats: {r['full_name']} no respondio")
            skipped += 1
            continue
        for c in stats:
            if c.get("author") and c["author"]["login"].lower() == USER.lower():
                commits += c["total"]
                adds += sum(w["a"] for w in c["weeks"])
                dels += sum(w["d"] for w in c["weeks"])
    return {
        "repos": str(len(owned)),
        "stars": str(sum(r["stargazers_count"] for r in owned)),
        "followers": str(u.get("followers", "?")),
        "commits": f"{commits:,}",
        "loc_net": f"{adds - dels:,}",
        "loc_add": f"{adds:,}",
        "loc_del": f"{dels:,}",
    }, skipped


if __name__ == "__main__":
    try:
        with open("data.json") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    song = spotify_last_played()
    if song:
        data["last_played"] = song
    stats, skipped = github_stats()
    if skipped and all(k in data for k in stats):
        # cifras incompletas: mejor conservar las anteriores que publicar menos
        print(f"stats: {skipped} repos sin responder, conservo stats anteriores")
    else:
        data.update(stats)
    with open("data.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("data.json:", json.dumps(data, ensure_ascii=False))
