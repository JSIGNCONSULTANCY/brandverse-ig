#!/usr/bin/env python3
"""BrandVerse Instagram auto-publisher.

Runs every ~10 minutes (GitHub Actions or any scheduler). For each post in content.json whose
UAE-time slot has arrived and which is not yet in state/posted.json, it:
  1. creates an Instagram media container from the public image URL,
  2. waits until the container is FINISHED,
  3. publishes it, and records the result.

Uses only Meta's official Instagram API (graph.instagram.com). No passwords are used.

Environment variables:
  IG_USER_ID       numeric Instagram professional account id
  IG_ACCESS_TOKEN  long-lived Instagram User access token (scope instagram_business_content_publish)
  IMAGE_BASE_URL   public base URL where the posters/ folder is served, e.g. https://USER.github.io/brandverse-ig
  API_BASE         (optional) override, used by tests. Default https://graph.instagram.com/v21.0
  DRY_RUN=1        print what would be posted, do nothing
  MAX_LATE_HOURS   (optional, default 6) posts later than this past their slot are skipped, not posted late
  NOW              (optional, ISO UTC) override the clock, used by tests
"""
import os, sys, json, time, datetime as dt
import urllib.request, urllib.parse, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, 'state', 'posted.json')
API = os.environ.get('API_BASE', 'https://graph.instagram.com/v21.0').rstrip('/')


def http(method, url, data=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors='replace')
        raise RuntimeError(f'HTTP {e.code} on {method} {url.split("?")[0]}: {detail[:500]}')


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {}


def save_state(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(s, open(STATE, 'w'), indent=1)


def publish_one(rec, uid, token, base_url):
    # posters may sit at the repository root or inside posters/ ; the file name is what matters
    image_url = f"{base_url.rstrip('/')}/{os.path.basename(rec['file'])}"
    c = http('POST', f'{API}/{uid}/media', dict(image_url=image_url, caption=rec['caption'],
                                                alt_text=rec['alt'], access_token=token))
    cid = c['id']
    status = ''
    for _ in range(30):  # up to ~5 minutes
        st = http('GET', f'{API}/{cid}?' + urllib.parse.urlencode(dict(fields='status_code', access_token=token)))
        status = st.get('status_code', '')
        if status == 'FINISHED':
            break
        if status in ('ERROR', 'EXPIRED'):
            raise RuntimeError(f'container {cid} status {status}')
        time.sleep(10 if not os.environ.get('NOW') else 0.05)
    else:
        raise RuntimeError(f'container {cid} not ready, last status {status!r}')
    p = http('POST', f'{API}/{uid}/media_publish', dict(creation_id=cid, access_token=token))
    return p['id']


def main():
    uid = os.environ.get('IG_USER_ID', '')
    token = os.environ.get('IG_ACCESS_TOKEN', '')
    base_url = os.environ.get('IMAGE_BASE_URL', '')
    dry = os.environ.get('DRY_RUN') == '1'
    late_h = float(os.environ.get('MAX_LATE_HOURS', '6'))
    if not dry and not (uid and token and base_url):
        sys.exit('Missing IG_USER_ID / IG_ACCESS_TOKEN / IMAGE_BASE_URL')
    now = dt.datetime.fromisoformat(os.environ['NOW'].replace('Z', '+00:00')) if os.environ.get('NOW') \
        else dt.datetime.now(dt.timezone.utc)
    recs = json.load(open(os.path.join(ROOT, 'content.json')))
    state = load_state()
    due = []
    for r in recs:
        when = dt.datetime.fromisoformat(r['when_utc'].replace('Z', '+00:00'))
        key = str(r['n'])
        if key in state:
            continue
        if when > now:
            continue
        if (now - when).total_seconds() > late_h * 3600:
            state[key] = dict(status='skipped_late', at=now.isoformat())
            print(f"#{r['n']} skipped (more than {late_h:g}h late)")
            continue
        due.append(r)
    due.sort(key=lambda r: r['n'])
    done = 0
    for r in due[:2]:  # never burst more than 2 per run
        print(f"#{r['n']} due {r['when_gst']} UAE -> {'DRY RUN' if dry else 'publishing'}")
        if dry:
            continue
        try:
            media_id = publish_one(r, uid, token, base_url)
            state[str(r['n'])] = dict(status='posted', media_id=media_id, at=now.isoformat())
            done += 1
            print(f"#{r['n']} posted, media id {media_id}")
        except Exception as e:
            print(f"#{r['n']} FAILED: {e}", file=sys.stderr)
            state.setdefault(str(r['n']) + '_err', [])
            state[str(r['n']) + '_err'] = (state[str(r['n']) + '_err'] + [str(e)[:300]])[-3:]
            break  # stop this run; next run retries
        finally:
            save_state(state)
    save_state(state)
    left = sum(1 for r in recs if str(r['n']) not in state)
    print(f'done: {done} posted this run, {left} remaining')


if __name__ == '__main__':
    main()
