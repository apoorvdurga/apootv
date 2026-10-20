#!/usr/bin/env python3
"""
Build a curated, Tata-Play-shaped lineup: recognizable channels only,
Hindi + English only, channel-numbered by genre block.

Rule: nothing ships unless it is on this allowlist AND a feed verifiably plays.
"""
import re, json, collections

VERIFIED = "verified_all.json"

QUALITY = re.compile(r"\s*\((1080|720|576|540|480|478|400|396|392|360|288|240)p\)")
TAGS = re.compile(r"\s*\[[^\]]*\]")

def norm(n):
    n = TAGS.sub("", n)
    n = QUALITY.sub("", n).strip()
    n = re.sub(r"\s+HD\+?$", "", n, flags=re.I)
    n = re.sub(r"\s+\((India|United States|US|UK)\)$", "", n, flags=re.I)
    return re.sub(r"\s+", " ", n).strip()

def q(n):
    m = QUALITY.search(n)
    return int(m.group(1)) if m else 0

# (canonical name, genre, language, match keys)
LINEUP = [
    # ---------------- Hindi news ----------------
    ("Aaj Tak",              "News", "Hindi",   ["Aaj Tak"]),
    ("ABP News",             "News", "Hindi",   ["ABP News"]),
    ("India TV",             "News", "Hindi",   ["India TV"]),
    ("News18 India",         "News", "Hindi",   ["News18 India"]),
    ("Zee News",             "News", "Hindi",   ["Zee News"]),
    ("NDTV India",           "News", "Hindi",   ["NDTV India"]),
    ("Republic Bharat",      "News", "Hindi",   ["Republic Bharat"]),
    ("Times Now Navbharat",  "News", "Hindi",   ["Times Now Navbharat"]),
    ("TV9 Bharatvarsh",      "News", "Hindi",   ["TV9 Bharatvarsh"]),
    ("News Nation",          "News", "Hindi",   ["News Nation"]),
    ("Good News Today",      "News", "Hindi",   ["Good News Today"]),
    ("DD News",              "News", "Hindi",   ["DD News"]),
    ("Sudarshan News",       "News", "Hindi",   ["Sudarshan News"]),
    ("Swaraj Express",       "News", "Hindi",   ["Swaraj Express"]),
    ("Bharat Express",       "News", "Hindi",   ["Bharat Express"]),
    ("ABP Ganga",            "News", "Hindi",   ["ABP Ganga"]),
    ("Zee Bharat",           "News", "Hindi",   ["Zee Bharat"]),
    ("News 24",              "News", "Hindi",   ["News 24 MP", "News 24"]),
    ("CNBC Awaaz",           "Business", "Hindi", ["CNBC Awaaz"]),
    ("Zee Business",         "Business", "Hindi", ["Zee Business"]),

    # ---------------- English news ----------------
    ("NDTV 24x7",            "News", "English", ["NDTV 24x7"]),
    ("CNN-News18",           "News", "English", ["CNN News 18", "CNN-News18"]),
    ("India Today",          "News", "English", ["India Today"]),
    ("Times Now",            "News", "English", ["Times Now"]),
    ("Mirror Now",           "News", "English", ["Mirror Now"]),
    ("WION",                 "News", "English", ["WION"]),
    ("Firstpost",            "News", "English", ["Firstpost"]),
    ("Republic TV",          "News", "English", ["Republic TV"]),
    ("India Ahead",          "News", "English", ["India Ahead"]),
    ("NewsX",                "News", "English", ["NewsX"]),
    ("DD India",             "News", "English", ["DD India"]),
    ("CNBC-TV18",            "Business", "English", ["CNBC TV18", "CNBC-TV18"]),
    ("CNBC-TV18 Prime HD",   "Business", "English", ["CNBC TV18 Prime"]),
    ("ET Now",               "Business", "English", ["ET Now"]),
    ("NDTV Profit",          "Business", "English", ["NDTV Profit"]),

    # ---------------- International English news ----------------
    ("Al Jazeera English",   "News", "English", ["Al Jazeera English"]),
    ("DW English",           "News", "English", ["DW English"]),
    ("France 24 English",    "News", "English", ["France 24 English"]),
    ("Euronews English",     "News", "English", ["Euronews English"]),
    ("TRT World",            "News", "English", ["TRT World"]),
    ("GB News",              "News", "English", ["GB News"]),
    ("CNBC UK",              "Business", "English", ["CNBC UK"]),
    ("ABC News",             "News", "English", ["ABC News"]),
    ("i24NEWS English",      "News", "English", ["i24NEWS English"]),
    ("NHK World Japan",      "News", "English", ["NHK World"]),
    ("Arirang TV",           "News", "English", ["Arirang TV"]),
    ("CNA International",    "News", "English", ["CNA International"]),
    ("Bloomberg TV+",        "Business", "English", ["Bloomberg TV"]),

    # ---------------- Entertainment ----------------
    ("Colors",               "Entertainment", "Hindi", ["Colors"]),
    ("Colors Infinity",      "Entertainment", "English", ["Colors Infinity"]),
    ("DD National",          "Entertainment", "Hindi", ["DD National"]),
    ("Dangal 2",             "Entertainment", "Hindi", ["Dangal 2"]),

    # ---------------- Movies ----------------
    ("Goldmines",            "Movies", "Hindi", ["Goldmines"]),
    ("Goldmines Bollywood",  "Movies", "Hindi", ["Goldmines Bollywood"]),
    ("Goldmines Action",     "Movies", "Hindi", ["Goldmines Action"]),
    ("B4U Movies",           "Movies", "Hindi", ["B4U Movies"]),
    ("B4U Kadak",            "Movies", "Hindi", ["B4U Kadak"]),
    ("Sony Max 2",           "Movies", "Hindi", ["Sony Max 2"]),
    ("Colors Cineplex",      "Movies", "Hindi", ["Colors Cineplex"]),
    ("Movies Now",           "Movies", "English", ["Movies Now"]),
    ("Maha Movie",           "Movies", "Hindi", ["Maha Movie"]),
    ("Manoranjan Movies",    "Movies", "Hindi", ["Manoranjan Movies"]),

    # ---------------- Sports ----------------
    ("DD Sports",            "Sports", "Hindi", ["DD Sports"]),
    ("Star Sports 2",        "Sports", "Hindi", ["Star Sports 2"]),
    ("Star Sports Select 1", "Sports", "English", ["Star Sports Select 1"]),
    ("Star Sports Select 2", "Sports", "English", ["Star Sports Select 2"]),
    ("Sony Sports Ten 1",    "Sports", "Hindi", ["Sony Sports Ten 1"]),
    ("Sony Sports Ten 2",    "Sports", "Hindi", ["Sony Sports Ten 2"]),
    ("Sony Sports Ten 3",    "Sports", "Hindi", ["Sony Sports Ten 3"]),
    ("Sony Sports Ten 5",    "Sports", "Hindi", ["Sony Sports Ten 5"]),
    ("Ten Cricket",          "Sports", "English", ["Ten Cricket"]),

    # ---------------- Kids ----------------
    ("Cartoon Network HD+",  "Kids", "Hindi", ["Cartoon Network HD"]),
    ("Cartoon Network",      "Kids", "Hindi", ["Cartoon Network (India)"]),
    ("Nickelodeon India",    "Kids", "Hindi", ["Nickelodeon (India)"]),
    ("Discovery Kids",       "Kids", "Hindi", ["Discovery Kids"]),
    ("Hungama TV",           "Kids", "Hindi", ["Hungama TV"]),
    ("Disney International", "Kids", "English", ["Disney International"]),

    # ---------------- Music ----------------
    ("9X Jalwa",             "Music", "Hindi", ["9X Jalwa"]),
    ("9X Jhakaas",           "Music", "Hindi", ["9X Jhakaas"]),
    ("9X Tashan",            "Music", "Hindi", ["9X Tashan"]),
    ("B4U Music",            "Music", "Hindi", ["B4U Music"]),
    ("Mastiii",              "Music", "Hindi", ["Mastiii"]),
    ("Music India",          "Music", "Hindi", ["Music India"]),
    ("MH One Music",         "Music", "Hindi", ["Mh 1 Music", "MH One Music"]),
    ("Dhoom Music",          "Music", "Hindi", ["Dhoom Music"]),
    ("Dhamaal",              "Music", "Hindi", ["Dhamaal"]),

    # ---------------- Documentary ----------------
    ("Animal Planet India",  "Documentary", "English", ["Animal Planet (India)"]),
    ("National Geographic",  "Documentary", "English", ["National Geographic (India)"]),
    ("Nat Geo Wild",         "Documentary", "English", ["National Geographic Wild"]),
    ("Sony BBC Earth",       "Documentary", "English", ["Sony BBC Earth"]),
    ("Discovery India",      "Documentary", "English", ["Discovery Channel (India)"]),

    # ---------------- Lifestyle ----------------
    ("Food Food",            "Lifestyle", "Hindi", ["Food Food"]),
    ("NDTV Good Times",      "Lifestyle", "English", ["NDTV Good Times"]),
    ("TLC India",            "Lifestyle", "English", ["TLC (India)"]),
]

# Broadcaster-published feeds, verified working with higher resolution than the
# aggregator copy. These always win over a matched catalog entry.
OFFICIAL = {
    "Aaj Tak":   "https://feeds.intoday.in/aajtak/api/aajtakhd/master.m3u8",
    "NDTV 24x7": "https://ndtv24x7elemarchana.akamaized.net/hls/live/2003678/ndtv24x7/ndtv24x7master.m3u8",
    "NDTV India":"https://ndtvindiaelemarchana.akamaized.net/hls/live/2003679/ndtvindia/ndtvindiamaster.m3u8",
}

verified = json.load(open(VERIFIED))
pool = collections.defaultdict(list)
for c in verified:
    pool[norm(c["name"]).lower()].append(c)

# ---- rescue pass: brands that fell outside the sampled candidate set ----
import ssl, urllib.request, re as _re
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE

def parse_m3u(path):
    out, cur = [], None
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if line.startswith("#EXTINF"):
            cur = {"name": line.split(",", 1)[-1].strip(),
                   "logo": (_re.search(r'tvg-logo="([^"]*)"', line) or [None, ""])[1]}
        elif line.startswith("http") and cur:
            cur["url"] = line; out.append(cur); cur = None
    return out

raw = []
for p in ("categories_news.m3u", "countries_in.m3u"):
    try:
        raw += parse_m3u(p)
    except FileNotFoundError:
        pass

def alive(c):
    try:
        req = urllib.request.Request(c["url"], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=8, context=CTX) as r:
            if r.status != 200: return None
            body = r.read(50000).decode("utf-8", "replace")
        if "#EXTM3U" not in body: return None
        v = [l.strip() for l in body.splitlines() if l.strip() and not l.startswith("#")]
        if "#EXT-X-STREAM-INF" in body and v:
            base = c["url"].rsplit("/", 1)[0]
            vurl = v[0] if v[0].startswith("http") else (
                _re.sub(r"^(https?://[^/]+).*", r"\1", c["url"]) + v[0] if v[0].startswith("/") else base + "/" + v[0])
            req = urllib.request.Request(vurl, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=8, context=CTX) as r:
                if r.status != 200: return None
                body = r.read(50000).decode("utf-8", "replace")
        if not _re.search(r"\.(?:ts|m4s|aac|mp4)(?:\?|\b)", body): return None
        return c
    except Exception:
        return None

def rescue(canon, keys):
    cands = []
    for k in keys:
        nk = norm(k).lower()
        for c in raw:
            if norm(c["name"]).lower().startswith(nk) or nk in norm(c["name"]).lower():
                cands.append(c)
    if not cands: return None
    seen, uniq = set(), []
    for c in cands:
        if c["url"] in seen: continue
        seen.add(c["url"]); uniq.append(c)
    with ThreadPoolExecutor(max_workers=8) as ex:
        lives = [r for r in ex.map(alive, uniq) if r]
    if not lives: return None
    return max(lives, key=lambda c: q(c["name"]))


out, missing = [], []
for canon, genre, lang, keys in LINEUP:
    cands = []
    for k in keys:
        cands += pool.get(norm(k).lower(), [])
    if not cands:
        got = rescue(canon, keys)
        if got is None:
            missing.append(canon)
            continue
        cands = [got]
    # prefer live, not flagged, highest resolution
    def score(c):
        nm = c["name"]
        return (0 if "Not 24/7" in nm else 1,
                0 if "Geo-blocked" in nm else 1,
                q(nm), c.get("segments", 0))
    best = max(cands, key=score)
    entry = {
        "name": canon,
        "url": OFFICIAL.get(canon, best["url"]),
        "logo": best.get("logo", ""),
        "genre": genre,
        "language": lang,
        "region": "IN" if lang == "Hindi" or canon not in (
            "Al Jazeera English","DW English","France 24 English","Euronews English",
            "TRT World","GB News","CNBC UK","ABC News","i24NEWS English",
            "NHK World Japan","Arirang TV","CNA International","Bloomberg TV+",
            "CNN-News18","NDTV 24x7","India Today","Times Now","Mirror Now","WION",
            "Firstpost","Republic TV","India Ahead","NewsX","DD India","CNBC-TV18",
            "CNBC-TV18 Prime HD","ET Now","NDTV Profit","Movies Now","Colors Infinity",
            "Disney International","Star Sports Select 1","Star Sports Select 2","Ten Cricket",
            "Animal Planet India","National Geographic","Nat Geo Wild","Sony BBC Earth",
            "Discovery India","NDTV Good Times","TLC India") else "INTL",
        "source": "official" if canon in OFFICIAL else "catalog",
        "quality": q(best["name"]),
    }
    out.append(entry)

# ---- channel numbering by genre block, like a real EPG ----
BLOCKS = [("News", 100), ("Business", 200), ("Entertainment", 300), ("Movies", 400),
          ("Sports", 500), ("Kids", 600), ("Music", 700), ("Documentary", 800),
          ("Lifestyle", 900)]
for genre, base in BLOCKS:
    rows = sorted([r for r in out if r["genre"] == genre], key=lambda r: r["name"])
    for i, r in enumerate(rows):
        r["number"] = base + i

out.sort(key=lambda r: r["number"])

json.dump(out, open("channels.json", "w"), indent=1)
with open("channels.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for c in out:
        f.write(f'#EXTINF:-1 tvg-chno="{c["number"]}" tvg-logo="{c["logo"]}" '
                f'group-title="{c["genre"]}",{c["name"]}\n{c["url"]}\n')

g = collections.Counter(c["genre"] for c in out)
l = collections.Counter(c["language"] for c in out)
print(f"LINEUP: {len(out)} channels")
print("genre:", dict(g))
print("language:", dict(l))
print(f"official feeds: {sum(1 for c in out if c['source']=='official')}")
if missing:
    print(f"\nnot available ({len(missing)}): {', '.join(missing)}")
print()
for c in out:
    print(f"  {c['number']}  {c['name']:24} {c['genre']:14} {c['language']:8} "
          f"{c['quality']}p  {c['source']}")
