# usage: python3 check.py AGENT_ID slug_or_url [slug_or_url ...]   (or pipe them on stdin)
# Checks only never-seen slugs; appends valid ones to found/AGENT_ID.txt, all tried ones to tried/AGENT_ID.txt.
import glob, os, re, sys, time, urllib.request, urllib.error

# ponytail: 0.5s per agent x 10 agents ~= 20 req/s total, same cap as scan.py; /v1/boards/<slug> is 200 for a board, 404 otherwise
GAP = float(os.environ.get("GAP", 0.5))
agent, args = sys.argv[1], sys.argv[2:] or sys.stdin.read().splitlines()
os.makedirs("found", exist_ok=True); os.makedirs("tried", exist_ok=True)

def slug(s):
    m = re.search(r"(?:job-)?boards(?:-api)?(?:\.eu)?\.greenhouse\.io/(?:v1/boards/|embed/job_board(?:/js)?\?for=)?([^/?#&\s]+)", s)
    # ponytail: canonical form is %-encoded ("flock safety" -> "flock%20safety") so files stay whitespace-split safe
    return urllib.request.quote(urllib.request.unquote((m.group(1) if m else s).strip().lower()), safe="")

seen = set(open("all_slugs.txt").read().split())
for f in glob.glob("tried/*.txt") + glob.glob("found/*.txt"):
    seen |= {slug(l) for l in open(f).read().splitlines() if l.strip()}

todo = sorted({slug(a) for a in args if a.strip()} - seen)
found, errored = [], set()
tried_f, found_f = open(f"tried/{agent}.txt", "a"), open(f"found/{agent}.txt", "a")
for s in todo:
    time.sleep(GAP)
    for attempt in range(4):
        try:
            req = urllib.request.Request(f"https://boards-api.greenhouse.io/v1/boards/{s}", headers={"User-Agent": "Mozilla/5.0"})
            urllib.request.urlopen(req, timeout=20).read()
            found.append(s)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5 * (attempt + 1)); continue
            if e.code != 404:
                errored.add(s)
        except Exception:
            errored.add(s)  # timeouts etc. stay untried so a later run retries them
        break
    else:
        errored.add(s)  # 429 on every attempt
    # write per slug so a killed run keeps its progress
    if s not in errored:
        tried_f.write(s + "\n"); tried_f.flush()
    if found and found[-1] == s:
        found_f.write(s + "\n"); found_f.flush()
print(f"{len(args)} given, {len(todo)} new, {len(found)} valid, {len(errored)} errored (will retry): {' '.join(found)}")
