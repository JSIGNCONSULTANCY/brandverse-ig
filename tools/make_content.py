#!/usr/bin/env python3
"""Builds content.json + schedule.csv from the 120-post bank.
Usage: python3 make_content.py [--start 2026-10-14]
Times are UAE time (Asia/Dubai, UTC+4, no daylight saving)."""
import sys, os, re, json, csv, argparse, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
from bank_a import DAYS_A
from bank_b import DAYS_B

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GST = dt.timezone(dt.timedelta(hours=4))

# Best posting windows for UAE audiences (research: weekday 11-13 and 19-21, weekend 10-14 and 18-20;
# B2B owners also check early morning). Friday avoids the prayer/lunch window 12:00-14:00.
SLOTS = {
    'weekday': ['08:30', '12:30', '18:45', '20:45'],   # Mon-Thu
    'friday':  ['09:30', '15:00', '18:45', '20:45'],
    'weekend': ['10:30', '13:30', '18:30', '20:30'],   # Sat-Sun
}

POOLS = {
 'tips':  ['#AccountingTips','#BusinessTips','#SmallBusinessUAE','#AccountingSoftware','#DubaiBusiness','#Productivity'],
 'inv':   ['#Invoicing','#AccountingSoftware','#SmallBusinessUAE','#DubaiBusiness','#BusinessTools','#UAEBusiness'],
 'vat':   ['#VATUAE','#UAEVAT','#UAETax','#DubaiBusiness','#Accounting','#UAEBusiness'],
 'einv':  ['#EInvoicingUAE','#EInvoicing','#VATUAE','#UAEBusiness','#DigitalTransformation','#DubaiBusiness'],
 'gold':  ['#GoldAccounting','#DubaiGold','#GoldTrading','#JewelleryBusiness','#GoldSouk','#UAEBusiness'],
 'pay':   ['#WPS','#PayrollUAE','#UAEHR','#Payroll','#SmallBusinessUAE','#UAEBusiness'],
 'rep':   ['#FinancialReporting','#AccountingSoftware','#BusinessGrowth','#UAEBusiness','#Accounting','#DubaiBusiness'],
 'smb':   ['#SmallBusinessUAE','#UAEEntrepreneurs','#DubaiBusiness','#BusinessOwners','#StartupUAE','#UAEBusiness'],
 'brand': ['#AccountingSoftware','#UAEBusiness','#SimpleAccounting','#DubaiBusiness','#SmallBusinessUAE','#MadeForUAE'],
}
CTAS = [
    'Save this for later 📌',
    'Know a business owner who needs this? Share it.',
    'Learn more: link in bio · www.brandverse.ae',
    'Follow for a new BrandVerse tip every day.',
]
THEMES = ['dark', 'light', 'brand', 'dark']


def plain(s):
    return re.sub(r'<[^>]+>', '', s)


def slot_times(date):
    wd = date.weekday()  # Mon=0
    key = 'weekend' if wd in (5, 6) else ('friday' if wd == 4 else 'weekday')
    return SLOTS[key]


def build(start):
    days = DAYS_A + DAYS_B
    out, n = [], 0
    for di, posts in enumerate(days):
        date = start + dt.timedelta(days=di)
        times = slot_times(date)
        for si, p in enumerate(posts):
            n += 1
            h, m = map(int, times[si].split(':'))
            when = dt.datetime(date.year, date.month, date.day, h, m, tzinfo=GST)
            pool = POOLS[p['pool']]
            tags = ['#BrandVerse'] + [pool[(n + k) % len(pool)] for k in range(4)]
            tags = list(dict.fromkeys(tags))[:5]
            cta = p['cta'] or CTAS[n % len(CTAS)]
            caption = f"{p['hook']}\n\n{p['body']}\n\n{cta}\n\n{' '.join(tags)}"
            sub = p['sub'] or ''
            alt = p['alt'] or f"BrandVerse poster: {plain(p['h'])}. {sub}".strip()
            theme = THEMES[(si + di) % 4]
            rec = dict(n=n, day=di + 1, slot=si + 1, layout=p['l'], theme=theme, prod=p['p'],
                       kicker=p['k'], headline=p['h'], items=p['items'], shot=p['shot'], sub=sub,
                       big=p['big'], caption=caption, alt=alt[:900],
                       file=f"posters/{n:03d}_d{di+1:02d}_s{si+1}.jpg",
                       when_gst=when.strftime('%Y-%m-%d %H:%M'),
                       when_utc=when.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                       weekday=when.strftime('%a'))
            assert len(caption) <= 2200, (n, len(caption))
            assert caption.count('#') <= 5
            out.append(rec)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='2026-10-14')
    a = ap.parse_args()
    start = dt.date.fromisoformat(a.start)
    recs = build(start)
    os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
    json.dump(recs, open(os.path.join(ROOT, 'content.json'), 'w'), indent=1, ensure_ascii=False)
    with open(os.path.join(ROOT, 'schedule.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['#', 'Day', 'Weekday', 'Date & time (UAE)', 'Pillar', 'Product', 'Poster file', 'Headline', 'Caption'])
        for r in recs:
            w.writerow([r['n'], r['day'], r['weekday'], r['when_gst'], r['kicker'], r['prod'], r['file'],
                        plain(r['headline']), r['caption'].replace('\n', ' / ')])
    print(len(recs), 'posts', recs[0]['when_gst'], '->', recs[-1]['when_gst'])
