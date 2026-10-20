#!/usr/bin/env python3
"""
Final lineup = (curated Hindi/English) UNION (Tata Play FTA that has a live feed).

Rules:
  * Hindi + English only.
  * Tata Play channel numbers where the channel is listed.
  * Paid entertainment/sports/kids feeds are pirate rebroadcasts -> dropped.
  * Every URL is liveness-checked before shipping.
"""
import json, re, ssl, urllib.request, collections
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE

def norm(s):
    s = s.lower()
    s = re.sub(r"\((1080|720|576|540|480|478|400|396|392|360|288|240)p\)", "", s)
    s = re.sub(r"\[[^\]]*\]", "", s)
    s = re.sub(r"\bhd\+?\b|\bsd\b", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return re.sub(r"\s+", " ", s)

# subscription channels whose "free" web feeds are unauthorised rebroadcasts
PIRATE = {"hungama tv", "nickelodeon", "nickelodeon india", "disney international",
          "cartoon network", "cartoon network hd", "discovery kids", "colors",
          "colors infinity", "colors cineplex", "movies now", "sony max 2",
          "star sports 2", "star sports select 1", "star sports select 2",
          "sony sports ten 1", "sony sports ten 2", "sony sports ten 3",
          "sony sports ten 5", "national geographic", "nat geo wild",
          "sony bbc earth", "animal planet", "ten cricket"}

def alive(url):
    try:
        r = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(r, timeout=9, context=CTX) as x:
            if x.status != 200: return False
            b = x.read(60000).decode("utf-8", "replace")
        if "#EXTM3U" not in b: return False
        v = [l.strip() for l in b.splitlines() if l.strip() and not l.startswith("#")]
        if "#EXT-X-STREAM-INF" in b and v:
            base = url.rsplit("/", 1)[0]
            vu = v[0] if v[0].startswith("http") else (
                re.sub(r"^(https?://[^/]+).*", r"\1", url) + v[0] if v[0].startswith("/") else base + "/" + v[0])
            r = urllib.request.Request(vu, headers={"User-Agent": UA})
            with urllib.request.urlopen(r, timeout=9, context=CTX) as x:
                if x.status != 200: return False
                b = x.read(60000).decode("utf-8", "replace")
        return bool(re.search(r"\.(?:ts|m4s|aac|mp4)(?:\?|\b)", b))
    except Exception:
        return False

# Broadcaster-published feeds captured from their own live-TV web players
# (Playwright network interception). These beat any aggregator copy.
OFFICIAL_OVERRIDES = {
    "ABP News":     "https://d2l4ar6y3mrs4k.cloudfront.net/live-streaming/abpnews-livetv/master.m3u8",
    "Times Now":    "https://dztlhgid9me95.cloudfront.net/live-tv/Vidgyor/timesnow/timesnow_master.m3u8",
    "CNBC-TV18":    "https://nw18live.cdn.jio.com/bpk-tv/CNBC_TV18_NW18_MOB/output01/index.m3u8",
    "CNBC Awaaz":   "https://nw18live.cdn.jio.com/bpk-tv/CNBC_Awaaz_NW18_MOB/output01/index.m3u8",
    "News18 India": "https://nw18live.cdn.jio.com/bpk-tv/News18_India_NW18_MOB/output01/index.m3u8",
    "Aaj Tak":      "https://feeds.intoday.in/aajtak/api/aajtakhd/master.m3u8",
    "NDTV 24x7":    "https://ndtv24x7elemarchana.akamaized.net/hls/live/2003678/ndtv24x7/ndtv24x7master.m3u8",
    "NDTV India":   "https://ndtvindiaelemarchana.akamaized.net/hls/live/2003679/ndtvindia/ndtvindiamaster.m3u8",
}

curated = json.load(open("channels.curated71.json"))
broad = json.load(open("channels.json"))

merged = {}
for c in curated + broad:            # curated wins on conflict (better tagging)
    k = norm(c["name"])
    if k in PIRATE or any(k == p or k.startswith(p + " ") for p in PIRATE):
        continue
    if c["language"] not in ("Hindi", "English"):
        continue
    if k not in merged:
        merged[k] = c

print(f"candidates: {len(merged)}")
rows = list(merged.values())
for c in rows:
    ov = OFFICIAL_OVERRIDES.get(c["name"])
    if ov:
        c["url"] = ov
        c["source"] = "official"

with ThreadPoolExecutor(max_workers=24) as ex:
    live = list(ex.map(lambda c: alive(c["url"]), rows))
kept = [c for c, ok in zip(rows, live) if ok]
dead = [c for c, ok in zip(rows, live) if not ok]

# transient failures are common: retry once, gently, before dropping a channel
if dead:
    with ThreadPoolExecutor(max_workers=4) as ex:
        retried = list(ex.map(lambda c: alive(c["url"]), dead))
    recovered = [c for c, ok in zip(dead, retried) if ok]
    kept += recovered
    dead = [c for c, ok in zip(dead, retried) if not ok]
    if recovered:
        print(f"  recovered on retry: {', '.join(c['name'] for c in recovered)}")

dropped_dead = [c["name"] for c in dead]
print(f"live: {len(kept)}   dropped dead: {len(dropped_dead)}")
if dropped_dead:
    print("  dead:", ", ".join(dropped_dead))

# Two channels must never share one stream: fuzzy name matching had mapped both
# "Dangal" and "Dangal 2" onto the Dangal 2 feed. Keep the closest name match.
def alnum(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

by_url = {}
for c in kept:
    by_url.setdefault(c["url"], []).append(c)

resolved, dropped_dup = [], []
for url, group in by_url.items():
    if len(group) == 1:
        resolved.append(group[0])
        continue
    slug = alnum(url)
    best = max(group, key=lambda c: (alnum(c["name"]) in slug, len(alnum(c["name"]))))
    resolved.append(best)
    dropped_dup += [c["name"] for c in group if c is not best]
if dropped_dup:
    print("  duplicate feed dropped:", ", ".join(dropped_dup))
kept = resolved

# unique numbers, TP numbers first
seen, nxt = set(), 950
for c in sorted(kept, key=lambda x: x.get("number", 9999)):
    if c["number"] in seen:
        while nxt in seen: nxt += 1
        c["number"] = nxt; seen.add(nxt)
    else:
        seen.add(c["number"])
kept.sort(key=lambda c: c["number"])

json.dump(kept, open("channels.json", "w"), indent=1)
with open("channels.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for c in kept:
        f.write(f'#EXTINF:-1 tvg-chno="{c["number"]}" tvg-logo="{c["logo"]}" '
                f'group-title="{c["genre"]}",{c["name"]}\n{c["url"]}\n')

print(f"\nFINAL: {len(kept)}")
print("genre:", dict(collections.Counter(c["genre"] for c in kept)))
print("language:", dict(collections.Counter(c["language"] for c in kept)))
print("\nnews channels:", ", ".join(sorted(c["name"] for c in kept if c["genre"] in ("News","Business"))))
