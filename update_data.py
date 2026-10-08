#!/usr/bin/env python3
"""Actualiza data.json con estadisticas de GitHub.
Corre en GitHub Actions (cron) o local. Solo stdlib.

Env vars:
    GITHUB_TOKEN o GH_TOKEN  (opcional, solo por rate limit; los datos son publicos)
"""
import json
import os
import time
import urllib.request

USER = "duohnson"


def http(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            return r.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        return e.code, {}


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
            print(f"stats: {r['full_name']} 404 error")
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
        "stats_status": (f"Partial: {skipped} repository(ies) pending"
                 if skipped else "Complete"),
    }, skipped


if __name__ == "__main__":
    try:
        with open("data.json") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    stats, skipped = github_stats()
    data.update(stats)
    with open("data.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("data.json:", json.dumps(data, ensure_ascii=False))
