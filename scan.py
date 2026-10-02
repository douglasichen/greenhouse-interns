import json, os, re, sys, threading, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

INTERN = re.compile(r"\b(intern|internship|co-?op)\b", re.I)
HOURS = int(os.environ.get("HOURS", 24))
cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS)

# ponytail: global 20 req/s cap + 429 backoff; per-host token bucket if Greenhouse still complains
GAP, lock, last = 0.05, threading.Lock(), [0.0]

def throttle():
    with lock:
        wait = last[0] + GAP - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        last[0] = time.monotonic()

def fetch(slug, tries=4):
    throttle()
    try:
        req = urllib.request.Request(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return slug, json.load(r).get("jobs", [])
    except urllib.error.HTTPError as e:
        if e.code == 429 and tries:
            time.sleep(2 * (5 - tries))
            return fetch(slug, tries - 1)
        if e.code != 404:
            print("http", e.code, slug)
        return slug, None  # 404 = no board
    except Exception as e:
        print("err", slug, e)
        return slug, None

slugs = sorted({w for f in (sys.argv[1:] or ["slugs.txt"]) for w in open(f).read().split()})
valid, fresh = [], []
with ThreadPoolExecutor(16) as ex:
    for slug, jobs in ex.map(fetch, slugs):
        if jobs is None:
            continue
        valid.append(f"https://boards.greenhouse.io/{slug}")
        for j in jobs:
            pub = j.get("first_published") or j["updated_at"]  # first_published = original post time; updated_at moves on every edit
            t = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            if INTERN.search(j["title"]) and t >= cutoff:
                fresh.append(f"{j['absolute_url']}\t{slug}\t{j['title'].strip()}\t{pub}")

open("valid_boards.txt", "w").write("\n".join(sorted(valid)) + "\n")
open(f"internships_last_{HOURS}h.txt", "w").write("\n".join(sorted(fresh)) + "\n")
print(len(slugs), "checked,", len(valid), "valid,", len(fresh), "fresh intern posts")
