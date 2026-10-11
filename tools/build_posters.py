#!/usr/bin/env python3
"""Renders content.json -> posters/*.jpg (1080x1350, JPEG, as Instagram requires).
Usage: python3 build_posters.py [--only 1,2,3] [--shots DIR]"""
import os, re, sys, json, argparse, io
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = open(os.path.join(ROOT, 'assets/fonts.css')).read()
LOGO = open(os.path.join(ROOT, 'assets/logo.html')).read()
LOGO_SVG = re.search(r'<svg.*?</svg>', LOGO, re.S).group(0)
LOGO_LIGHT = LOGO_SVG.replace('fill="#FFFFFF"', 'fill="#1A0E21"').replace('fill="#A090AA"', 'fill="#6F6076"')
SHOTS = os.path.join(ROOT, 'assets/shots')

ICON = {
 'check': '<svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
}

CSS = FONTS + """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1350px}
body{position:relative;overflow:hidden;font-family:Urbanist,sans-serif;font-weight:600;-webkit-font-smoothing:antialiased}
.theme-dark{--fg:#fff;--mut:#cdbbd6;--card:rgba(255,255,255,.07);--bd:rgba(255,255,255,.14);--acc:#E0559A;--acc2:#B06BD0;--chip:rgba(255,255,255,.12);--line:rgba(255,255,255,.16);
 background:radial-gradient(900px 700px at 92% 0%,rgba(168,46,110,.55),transparent 65%),radial-gradient(800px 700px at 0% 100%,rgba(98,40,122,.6),transparent 65%),linear-gradient(160deg,#1A0E21 0%,#2a1236 60%,#3a1747 100%);color:var(--fg)}
.theme-light{--fg:#1A0E21;--mut:#6F6076;--card:#fff;--bd:#E8DDEB;--acc:#C0306A;--acc2:#8a3aa8;--chip:#EFE4F2;--line:#E2D6E6;
 background:radial-gradient(800px 600px at 100% 0%,rgba(224,85,154,.16),transparent 65%),radial-gradient(800px 600px at 0% 100%,rgba(176,107,208,.16),transparent 65%),#F8F4F9;color:var(--fg)}
.theme-brand{--fg:#fff;--mut:#f3d6ea;--card:rgba(255,255,255,.13);--bd:rgba(255,255,255,.28);--acc:#FFE3F1;--acc2:#FFE3F1;--chip:rgba(255,255,255,.2);--line:rgba(255,255,255,.3);
 background:radial-gradient(900px 700px at 100% 0%,rgba(255,150,200,.35),transparent 60%),linear-gradient(155deg,#C0306A 0%,#7B2C8E 58%,#35153f 100%);color:var(--fg)}
/* gold accent */
.theme-dark.gold{--acc:#EDBF55;--acc2:#C58A22}
.theme-light.gold{--acc:#A8710E;--acc2:#C58A22;--chip:#F6EAD0}
.theme-brand.gold{background:radial-gradient(900px 700px at 100% 0%,rgba(255,215,120,.35),transparent 60%),linear-gradient(155deg,#A8620F 0%,#6E2F5E 58%,#2a1236 100%);--acc:#FFF0C8;--acc2:#FFF0C8}
.page{position:absolute;inset:0;padding:72px 84px 60px;display:flex;flex-direction:column}
.hd{display:flex;justify-content:space-between;align-items:center;height:80px;flex:none}
.hd .lk{width:300px}.hd .lk svg{width:100%;height:auto;display:block}
.pill{font-size:22px;letter-spacing:.22em;font-weight:700;background:var(--chip);padding:12px 22px;border-radius:40px;color:var(--fg)}
.main{flex:1;display:flex;flex-direction:column;justify-content:center;min-height:0;padding:20px 0}
.k{font-size:27px;letter-spacing:.3em;font-weight:700;color:var(--acc);margin-bottom:22px}
h1{font-weight:700;letter-spacing:-.03em;line-height:1.04}
h1 b{font-weight:700;background:linear-gradient(90deg,var(--acc),var(--acc2));-webkit-background-clip:text;background-clip:text;color:transparent}
.theme-brand h1 b{background:none;color:#FFE3F1;-webkit-text-fill-color:#FFE3F1;text-decoration:underline;text-decoration-thickness:6px;text-underline-offset:10px;text-decoration-color:rgba(255,255,255,.55)}
.sub{font-size:34px;line-height:1.35;color:var(--mut);margin-top:26px}
.ft{flex:none;display:flex;justify-content:space-between;align-items:center;font-size:28px;color:var(--mut);border-top:1.5px solid var(--line);padding-top:26px}
.ft b{color:var(--fg);font-weight:700}
.cards{display:flex;flex-direction:column;gap:16px;margin-top:44px}
.c{display:flex;align-items:center;gap:26px;background:var(--card);border:1.5px solid var(--bd);border-radius:28px;padding:22px 28px}
.theme-light .c{box-shadow:0 8px 24px rgba(98,40,122,.07)}
.ci{flex:none;width:72px;height:72px;border-radius:22px;background:linear-gradient(135deg,var(--acc),var(--acc2));display:flex;align-items:center;justify-content:center;font-size:36px;font-weight:700;color:#fff}
.theme-brand .ci{background:rgba(255,255,255,.22)}
.c p{font-size:36px;line-height:1.22;font-weight:700;letter-spacing:-.01em}
.c small{display:block;font-size:27px;color:var(--mut);font-weight:600;margin-top:4px}
.shot{margin-top:34px;background:var(--card);border:1.5px solid var(--bd);border-radius:30px;padding:16px;box-shadow:0 24px 60px rgba(0,0,0,.28)}
.shot img{display:block;width:100%;border-radius:18px;max-height:620px;object-fit:cover;object-position:top left}
.cap{font-size:28px;color:var(--mut);margin-top:22px;text-align:center}
.big{font-weight:700;letter-spacing:-.04em;line-height:.95;background:linear-gradient(90deg,var(--acc),var(--acc2));-webkit-background-clip:text;background-clip:text;color:transparent}
.theme-brand .big{background:none;color:#fff;-webkit-text-fill-color:#fff}
.keys .row{display:flex;align-items:center;gap:30px;background:var(--card);border:1.5px solid var(--bd);border-radius:28px;padding:24px 30px}
.cap-k{flex:none;width:300px;text-align:center;font-size:36px;white-space:nowrap;font-weight:700;padding:14px 22px;border-radius:18px;background:var(--chip);border-bottom:6px solid rgba(0,0,0,.18);letter-spacing:.02em}
.keys .row p{font-size:34px;font-weight:700;line-height:1.2}
.opts{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:46px}
.opts .c{padding:26px}
.opts .c p{font-size:34px}
.hint{margin-top:34px;font-size:30px;color:var(--mut);display:flex;align-items:center;gap:14px}
.mv{display:flex;flex-direction:column;gap:22px;margin-top:40px}
.pn{border-radius:30px;padding:34px 38px;border:1.5px solid var(--bd)}
.pn .t{font-size:24px;letter-spacing:.28em;font-weight:700;margin-bottom:14px}
.pn p{font-size:38px;line-height:1.25;font-weight:700;letter-spacing:-.01em}
.pn.my{background:var(--card)}.pn.my .t{color:#E5546B}.pn.my p{opacity:.8;text-decoration:line-through;text-decoration-thickness:3px;text-decoration-color:rgba(229,84,107,.7)}
.pn.fa{background:linear-gradient(135deg,rgba(31,138,91,.22),rgba(31,138,91,.08));border-color:rgba(31,138,91,.55)}.pn.fa .t{color:#2fbf86}
.theme-light .pn.fa .t{color:#13674A}
.num{flex:none;width:76px;height:76px;border-radius:50%;background:linear-gradient(135deg,var(--acc),var(--acc2));display:flex;align-items:center;justify-content:center;font-size:40px;font-weight:700;color:#fff}
.theme-brand .lk image{filter:brightness(0) invert(1)}
.theme-brand .num{background:#fff;color:#7B2C8E}
"""


def plain(s):
    return re.sub(r'<[^>]+>', '', s)


def h1_size(h, cap=118):
    n = len(plain(h))
    return int(max(72, min(cap, 150 - n * 1.9)))


def render_html(r):
    t, l = r['theme'], r['layout']
    gold = ' gold' if r['prod'] == 'gold' else ''
    pill = {'books': 'BOOKS', 'gold': 'GOLD', 'both': 'BOOKS · GOLD'}[r['prod']]
    logo = LOGO_LIGHT if t == 'light' else LOGO_SVG
    if t == 'brand':
        logo = LOGO_SVG.replace('fill="url(#vg)"', 'fill="#FFE3F1"').replace('fill="#A090AA"', 'fill="#f3d6ea"')
    items = r['items']
    h = r['headline']
    kick = f'<div class="k">{r["kicker"]}</div>'
    body = ''
    if l == 'tip':
        cards = ''.join(f'<div class="c"><div class="ci">{ICON["check"]}</div><p>{i}</p></div>' for i in items)
        body = f'{kick}<h1 style="font-size:{h1_size(h,112)}px">{h}</h1><div class="cards">{cards}</div>'
    elif l == 'steps':
        cards = ''.join(f'<div class="c"><div class="num">{n+1}</div><p>{i}</p></div>' for n, i in enumerate(items))
        body = f'{kick}<h1 style="font-size:{h1_size(h,92)}px">{h}</h1><div class="cards" style="margin-top:34px;gap:14px">{cards}</div>'
    elif l == 'keys':
        rows = ''.join(f'<div class="row c" style="gap:30px"><div class="cap-k">{a}</div><p>{b}</p></div>' for a, b in items)
        body = f'{kick}<h1 style="font-size:{h1_size(h,100)}px">{h}</h1><div class="cards keys">{rows}</div>'
    elif l == 'ask':
        letters = 'ABCD'
        opts = ''.join(f'<div class="c"><div class="ci">{letters[n]}</div><p>{i}</p></div>' for n, i in enumerate(items))
        body = (f'{kick}<h1 style="font-size:{h1_size(h,104)}px">{h}</h1><div class="opts">{opts}</div>'
                f'<div class="hint">💬 Comment your pick below</div>')
    elif l == 'mvf':
        body = (f'{kick}<h1 style="font-size:{h1_size(h,92)}px">{h}</h1><div class="mv">'
                f'<div class="pn my"><div class="t">MYTH</div><p>{items[0]}</p></div>'
                f'<div class="pn fa"><div class="t">FACT</div><p>{items[1]}</p></div></div>')
    elif l == 'big':
        b = r['big']
        size = 360 if len(b) <= 3 else (260 if len(b) <= 5 else 190)
        body = (f'{kick}<div class="big" style="font-size:{size}px">{b}</div>'
                f'<h1 style="font-size:{h1_size(h,76)}px;margin-top:20px">{h}</h1>'
                f'<div class="sub">{r["sub"]}</div>')
    elif l == 'shot':
        src = os.path.join(SHOTS, r['shot'] + '.jpg')
        body = (f'{kick}<h1 style="font-size:{h1_size(h,88)}px">{h}</h1>'
                f'<div class="shot"><img src="file://{src}"></div><div class="cap">{r["sub"]}</div>')
    else:  # quote
        qs = int(max(88, min(132, 190 - len(plain(h)) * 1.7)))
        body = (f'{kick}<h1 style="font-size:{qs}px">{h}</h1><div class="sub" style="font-size:38px;margin-top:36px">{r["sub"]}</div>')
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f'<body class="theme-{t}{gold}"><div class="page">'
            f'<div class="hd"><div class="lk">{logo}</div><div class="pill">{pill}</div></div>'
            f'<div class="main">{body}</div>'
            f'<div class="ft"><b>www.brandverse.ae</b><span>BrandVerse by J SIGN</span></div>'
            f'</div></body></html>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--out', default=os.path.join(ROOT))
    a = ap.parse_args()
    recs = json.load(open(os.path.join(ROOT, 'content.json')))
    only = {int(x) for x in a.only.split(',') if x}
    os.makedirs(os.path.join(a.out, 'posters'), exist_ok=True)
    tmp = os.path.join(ROOT, 'build'); os.makedirs(tmp, exist_ok=True)
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': 1080, 'height': 1350})
        for r in recs:
            if only and r['n'] not in only:
                continue
            f = os.path.join(tmp, f"{r['n']:03d}.html")
            open(f, 'w').write(render_html(r))
            pg.goto('file://' + f)
            pg.wait_for_timeout(250)
            png = pg.screenshot(type='png')
            im = Image.open(io.BytesIO(png)).convert('RGB')
            assert im.size == (1080, 1350), im.size
            im.save(os.path.join(a.out, r['file']), 'JPEG', quality=92, optimize=True, progressive=False, subsampling=0)
            print('ok', r['n'], flush=True)
        br.close()


if __name__ == '__main__':
    main()
