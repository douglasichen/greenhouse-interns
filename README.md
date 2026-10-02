# greenhouse-interns

Find fresh internship postings across every Greenhouse job board we could discover. Greenhouse twin of the Ashby scanner; same commands, same file layout.

## Usage

```sh
# scan boards, keep intern posts published in the last N hours (default 24)
HOURS=100 python3 scan.py valid_slugs.txt
#  -> internships_last_100h.txt  (url \t slug \t title \t published)
#  -> valid_boards.txt           (https://boards.greenhouse.io/<slug>)

# test new candidate slugs/URLs (skips anything already in all_slugs.txt, tried/, found/)
python3 check.py myid stripe https://job-boards.greenhouse.io/airbnb/jobs/123
cat candidates.txt | GAP=0.1 python3 check.py myid
#  -> found/myid.txt (valid), tried/myid.txt (definitive 200/404 only; errors are retried next run)

# SWE-only filter
grep -iE 'software|developer|\bai\b|technical staff' internships_last_100h.txt \
  | grep -viE 'embedded|hardware|firmware|fpga|asic|electrical|electronics|mechanical|circuit|pcb|silicon|actuator|finance|marketing|marketer|sales|recruit|talent|operations|business|social|creative|product manager|mba' \
  > internships_last_100h_swe.txt
```

Both scripts throttle to 20 requests/sec total (check.py: 0.05s/request at `GAP=0.05` for a single agent, or 0.5s each for 10 agents), send a browser User-Agent, and back off on 429. Don't run things in parallel that add up to more than that.

## API

- Board check: `GET https://boards-api.greenhouse.io/v1/boards/<slug>` returns 200 for a real board and 404 otherwise.
- Jobs: `GET https://boards-api.greenhouse.io/v1/boards/<slug>/jobs`. The link comes from `absolute_url`.
- **Publish time: `first_published`**, with `updated_at` as a fallback. `updated_at` changes every time a posting is edited, so a stale job would look fresh. You can check this on `airbnb` or `stripe`.
- Intern match: `\b(intern|internship|co-?op)\b`, case-insensitive.

## Files

- `all_slugs.txt`: every slug tested (200 or 404)
- `valid_slugs.txt`: slugs with a live board (7,551 of 32,770 tested as of 2026-10-02); also copied to `slugs.txt`, the default input for scan.py
- `valid_boards.txt`: board URLs from the last scan

Candidate slugs came from the Wayback CDX (`boards.greenhouse.io/`, `job-boards.greenhouse.io/`, `embed/job_board?for=`), GitHub code search and job-list repos (SimplifyJobs, vanshb03, cvrve, speedyapply, jobright-ai, zapplyjobs, and scraper repos that ship greenhouse company lists), Hacker News (Algolia), YC companies (slug, name, domain), and the Ashby slug lists. The Common Crawl index timed out, so nothing came from it.
