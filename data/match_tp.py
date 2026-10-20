#!/usr/bin/env python3
"""
Map Tata Play's free-to-air (Rs 0.00) channels to feeds that actually play.

Keeps Tata Play's real channel numbers. Ships only Hindi + English.
"""
import re, json, glob, collections, ssl, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE

ALIASES = {
    "r bharat": "republic bharat",
    "abn andhra jyothy": "abn andhra jyoti",
    "dd news hd": "dd news",
    "dd india hd": "dd india",
    "cnn news18": "cnn news 18",
    "news18 india": "news18 india",
    "times now navbharat": "times now navbharat",
    "sports18 1": "sports18 1",
}

def norm(s):
    s = s.lower()
    s = re.sub(r"\((1080|720|576|540|480|478|400|396|392|360|288|240)p\)", "", s)
    s = re.sub(r"\[[^\]]*\]", "", s)
    s = re.sub(r"\bhd\+?\b|\bsd\b", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    s = re.sub(r"\s+", " ", s)
    return ALIASES.get(s, s)

def parse_m3u(path):
    out, cur = [], None
    try:
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line.startswith("#EXTINF"):
                cur = {"name": line.split(",", 1)[-1].strip(),
                       "logo": (re.search(r'tvg-logo="([^"]*)"', line) or [None, ""])[1]}
            elif line.startswith("http") and cur:
                cur["url"] = line; out.append(cur); cur = None
    except FileNotFoundError:
        pass
    return out

# ---------- candidate pool ----------
local_pool = collections.defaultdict(list)
verified = json.load(open("verified_all.json"))
for c in verified:
    local_pool[norm(c["name"])].append({"name": c["name"], "url": c["url"],
                                        "logo": c.get("logo",""), "lang": c.get("language"),
                                        "genre": c.get("genre"), "known": True})

remote_cands = []
for p in glob.glob("meta/genre_*.m3u") + ["countries_in.m3u", "categories_news.m3u"]:
    remote_cands += parse_m3u(p)
print(f"local known-good: {sum(len(v) for v in local_pool.values())}   remote candidates: {len(remote_cands)}")

lang_map = json.load(open("meta/lang_map.json"))
genre_map = json.load(open("meta/genre_map.json"))
LANG_NAMES = json.load(open("meta/language_names.json"))

def alive(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=8, context=CTX) as r:
            if r.status != 200: return 0
            body = r.read(50000).decode("utf-8", "replace")
        if "#EXTM3U" not in body: return 0
        v = [l.strip() for l in body.splitlines() if l.strip() and not l.startswith("#")]
        if "#EXT-X-STREAM-INF" in body and v:
            base = url.rsplit("/", 1)[0]
            vurl = v[0] if v[0].startswith("http") else (
                re.sub(r"^(https?://[^/]+).*", r"\1", url) + v[0] if v[0].startswith("/") else base + "/" + v[0])
            req = urllib.request.Request(vurl, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=8, context=CTX) as r:
                if r.status != 200: return 0
                body = r.read(50000).decode("utf-8", "replace")
        return len(re.findall(r"\.(?:ts|m4s|aac|mp4)(?:\?|\b)", body))
    except Exception:
        return 0

def language_for(url, fallback=None):
    langs = lang_map.get(url, [])
    if langs:
        return LANG_NAMES.get(langs[0])
    return fallback

def quality(n):
    m = re.search(r"\((\d{3,4})p\)", n)
    return int(m.group(1)) if m else 0

tp = [c for c in json.load(open("tp_channels.json")) if c["price"] == 0.0]
print(f"Tata Play FTA channels: {len(tp)}")

# ---------- match ----------
matched, unmatched = [], []

def candidates_for(name):
    n = norm(name)
    exact = local_pool.get(n, [])
    if exact: return exact, True
    # fuzzy against the local pool
    fuzzy = []
    for k, v in local_pool.items():
        if k == n or (len(n) > 5 and (k.startswith(n) or n.startswith(k))):
            fuzzy += v
    if fuzzy: return fuzzy, True
    # fuzzy against remote candidates
    rem = []
    for c in remote_cands:
        cn = norm(c["name"])
        if cn == n or (len(n) > 6 and (cn.startswith(n) or n.startswith(cn))):
            rem.append({"name": c["name"], "url": c["url"], "logo": c.get("logo",""),
                        "known": False})
    return rem, False

for ch in tp:
    cands, known = candidates_for(ch["name"])
    if not cands:
        unmatched.append(ch["name"]); continue
    if not known:
        # dedupe and liveness-test remote candidates
        seen, uniq = set(), []
        for c in cands:
            if c["url"] in seen: continue
            seen.add(c["url"]); uniq.append(c)
        with ThreadPoolExecutor(max_workers=6) as ex:
            segs = list(ex.map(lambda c: alive(c["url"]), uniq))
        pairs = [(c, s) for c, s in zip(uniq, segs) if s > 0]
        if not pairs:
            unmatched.append(ch["name"]); continue
        best, _ = max(pairs, key=lambda p: quality(p[0]["name"]))
        lang = language_for(best["url"])
        if not lang:
            unmatched.append(ch["name"]); continue
        cands = [{**best, "lang": lang}]
    else:
        cands = sorted(cands, key=lambda c: (c.get("lang") is None, quality(c["name"])), reverse=False)
        cands = sorted(cands, key=lambda c: quality(c["name"]), reverse=True)

    best = cands[0]
    lang = best.get("lang")
    if lang not in ("Hindi", "English"):
        unmatched.append(ch["name"]); continue

    gl = [g for g in genre_map.get(best["url"], []) if g != "undefined"]
    genre = {"news":"News","sports":"Sports","entertainment":"Entertainment","movies":"Movies",
             "music":"Music","kids":"Kids","documentary":"Documentary","business":"Business",
             "lifestyle":"Lifestyle","education":"Education","culture":"Culture",
             "religious":"Devotional","comedy":"Comedy","animation":"Kids"}.get(
                 gl[0] if gl else "", "General")

    matched.append({
        "number": ch["number"],
        "name": ch["name"].replace(" HD", ""),
        "url": best["url"],
        "logo": best.get("logo", ""),
        "genre": genre,
        "language": lang,
        "region": "IN",
        "quality": quality(best["name"]),
        "source": "catalog" if not known else "verified",
    })

# HD wins over SD for the same channel name
byname = {}
for m in matched:
    k = norm(m["name"])
    if k not in byname or m["quality"] > byname[k]["quality"]:
        byname[k] = m
final = sorted(byname.values(), key=lambda m: m["number"])

json.dump(final, open("channels.json", "w"), indent=1)
with open("channels.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for c in final:
        f.write(f'#EXTINF:-1 tvg-chno="{c["number"]}" tvg-logo="{c["logo"]}" '
                f'group-title="{c["genre"]}",{c["name"]}\n{c["url"]}\n')

print(f"\nMATCHED: {len(final)}   unmatched: {len(unmatched)}")
print("genre:", dict(collections.Counter(c["genre"] for c in final)))
print("language:", dict(collections.Counter(c["language"] for c in final)))
print("\n--- lineup ---")
for c in final:
    print(f"  {c['number']:5}  {c['name'][:30]:32} {c['genre']:14} {c['language']:8} {c['quality']}p")
