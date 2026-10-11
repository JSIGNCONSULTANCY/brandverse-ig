# BrandVerse Instagram Auto-Poster

120 posters (30 days x 4 a day), captions, hashtags, alt text and a UAE-time schedule, plus a
publisher that posts each one automatically through Instagram's official API.

## What is in this folder

| Item | What it is |
|---|---|
| `posters/` | 120 ready posters, 1080 x 1350 JPEG (Instagram only accepts JPEG through the API) |
| `schedule.csv` | The full plan: date, UAE time, pillar, headline, caption. Open in Excel to review |
| `content.json` | Same data for the robot (do not edit while it is running) |
| `tools/publish.py` | The publisher: posts whatever is due, never twice |
| `.github/workflows/publish.yml` | Runs the publisher every 10 minutes, free, no computer needed |
| `state/posted.json` | The robot's log of what it has posted |
| `tools/make_content.py` | Rebuilds schedule + captions for a new start date or new posting times |
| `tools/build_posters.py` | Re-renders posters from content (only needed if you change wording) |
| `preview/` | Contact sheets: all 120 posters at a glance |

Default start: **Wednesday 14 Oct 2026, 08:30 UAE**. Last post: Thursday 12 Nov 2026, 20:45.
To start on another date: `python3 tools/make_content.py --start 2026-10-19` (the posters do not change).

## Posting times (UAE time, GST)

| Days | Slot 1 | Slot 2 | Slot 3 | Slot 4 |
|---|---|---|---|---|
| Mon-Thu | 08:30 | 12:30 | 18:45 | 20:45 |
| Friday | 09:30 | 15:00 | 18:45 | 20:45 |
| Sat-Sun | 10:30 | 13:30 | 18:30 | 20:30 |

Why: published UAE guidance puts the strongest Instagram windows at about 11:00-13:00 and 19:00-21:00 on
weekdays and 10:00-14:00 and 18:00-20:00 at weekends. Early morning is added for business owners. Friday skips
12:00-14:00 (Friday prayers). Slot 4 each day is a poll or question so comments arrive when people are online.
These are general averages, not a guarantee. After week 1, open Instagram **Insights -> Total followers ->
Most active times** and move the slots in `tools/make_content.py` (the `SLOTS` table) to match your own audience.

## One-time setup (about 45 minutes)

### Step 1. Make sure the Instagram account can log in
The robot needs a login for the BrandVerse account itself. If it was created from your personal account and has
no password of its own, set one first (Instagram app -> Settings -> Accounts Centre -> Password and security).
The account must be **Professional** (Business or Creator).

### Step 2. Create a free Meta developer app
1. Go to developers.facebook.com and log in with your Facebook account (create one if you do not have it).
2. **My Apps -> Create App**, choose the **Business** type, give it any name (e.g. "BrandVerse Poster").
3. In the app, add the product **Instagram** and open **API setup with Instagram login**.
4. Under **Generate access tokens**, add your BrandVerse Instagram account and log in to it when asked.
   Approve the permissions `instagram_business_basic` and `instagram_business_content_publish`.
5. Click **Generate token**. Copy two things: the **access token** (long, starts with `IG...`) and the
   **Instagram account ID** (a number, shown next to the account).
   The token is valid for 60 days. This plan runs 30 days, so one token is enough.
   Meta changes this screen from time to time. If a label differs, look for "Instagram API with Instagram Login".

While the app stays in Development mode and the account is yours, no App Review is needed.

### Step 3. Put the project on GitHub (free)
The images must be on a public web address because Instagram downloads them from there. GitHub Pages gives you
that for free, and GitHub Actions is the free clock that runs the robot.
1. Create a free account at github.com and a **public** repository named `brandverse-ig`.
   (Public is required for free unlimited run time. The posters are public on Instagram anyway.)
2. Upload everything in this folder to the repository, including the hidden `.github` folder.
   The website upload accepts 100 files at a time, so upload `posters/` in two batches, or use git:
   ```
   git init && git add -A && git commit -m "BrandVerse poster bot"
   git branch -M main
   git remote add origin https://github.com/YOUR-NAME/brandverse-ig.git
   git push -u origin main
   ```
3. **Settings -> Pages**: Source = *Deploy from a branch*, Branch = `main`, folder = `/ (root)`. Save.
   After a minute, open `https://YOUR-NAME.github.io/brandverse-ig/posters/001_d01_s1.jpg`.
   If you can see the poster, hosting works.
4. **Settings -> Secrets and variables -> Actions -> New repository secret**. Add two secrets:
   - `IG_USER_ID` = the Instagram account ID from Step 2
   - `IG_ACCESS_TOKEN` = the token from Step 2
   Never paste these anywhere else, and never share them in chat.
5. **Actions** tab: enable workflows if asked. Open "Publish BrandVerse Instagram posts", press **Run workflow**.
   Before the start date it should finish green and say "0 posted, 120 remaining".

### Step 4. Watch the first post
At 08:30 on the start date the robot posts poster 1 (within about 10-20 minutes, because GitHub's timer can
be a little late). Check Instagram, then check the Actions log. If it worked, nothing else is needed.
Each run saves its result to `state/posted.json`, so a post is never published twice.

## Rules built into the robot
- Never posts more than 2 per run, and never before its UAE time.
- If a post is more than 6 hours late (for example GitHub was down), it is **skipped**, not dumped in a burst.
- A failed attempt is retried on the next run (10 minutes later).
- To pause everything: Actions -> the workflow -> **...** -> Disable workflow.
- To change a caption before it is posted: edit it in `content.json` on GitHub (or tell me what to change).

## Please review before you go live
- Read `schedule.csv` once. Every claim comes from your BrandVerse quick guides and user guides, but you are the
  publisher. Check anything about UAE rules (VAT, e-invoicing, WPS) against the current FTA / MOHRE guidance.
- Screenshots use the demo company ("Al Noor Trading LLC").
- No phone number appears anywhere. Contact is www.brandverse.ae and hello@brandverse.ae only.

## Honest limits
- Not tested against the real Instagram service. I tested the whole publish flow against a simulated Instagram
  server (correct posts, correct times, no duplicates, late-skip, 2-per-run cap). Your first live post is the real test.
- 4 posts a day is heavy for a new account. If reach drops or followers fall, cut to 2 a day (keep slots 2 and 4).
- This posts feed images only. Reels and Stories are not automated.
- Use only Instagram's official API, as here. Tools that ask for your Instagram password get accounts restricted.
- After 30 days the token and content run out. For month 2, ask for a fresh content bank and generate a new token.
