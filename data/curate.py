#!/usr/bin/env python3
"""Curate verified streams into a clean, deduped M3U playlist."""
import re, json, collections

ok = json.load(open("verified.json"))

# Brands we deliberately exclude: unrelated country homonyms, non-news, low value.
EXCLUDE = re.compile(
    r"\bAlbania\b|Sky News Arabia Vertical|Arirang UN|CBS News (Baltimore|Miami|Sacramento)"
    r"|News 24 Albania|CNA \(Albania\)|Sky News Extra", re.I)

# Canonical display names + ordering priority for known brands.
RENAME = {
    "aaj tak": "Aaj Tak", "abp news": "ABP News", "abp ananda": "ABP Ananda",
    "abp majha": "ABP Majha", "abp asmita": "ABP Asmita", "abp ganga": "ABP Ganga",
    "cnn news 18": "CNN-News18", "dd news": "DD News", "dd india": "DD India",
    "ndtv 24x7": "NDTV 24x7", "ndtv india": "NDTV India",
    "india today": "India Today", "india tv": "India TV", "news18 india": "News18 India",
    "zee news": "Zee News", "zee bharat": "Zee Bharat", "wion": "WION",
    "times now": "Times Now", "times now navbharat": "Times Now Navbharat",
    "mirror now": "Mirror Now", "news nation": "News Nation", "newsx world": "NewsX",
    "tv9 bharatvarsh": "TV9 Bharatvarsh", "tv9 telugu": "TV9 Telugu",
    "asianet news": "Asianet News", "asianet suvarna news": "Asianet Suvarna News",
    "mathrubhumi news": "Mathrubhumi News", "kairali news": "Kairali News",
    "reporter tv": "Reporter TV", "janam tv": "Janam TV", "ptc news": "PTC News",
    "etc news": "ETV News", "etv news": "ETV News", "cvr news": "CVR News",
    "india ahead": "India Ahead", "bharat express": "Bharat Express",
    "sudarshan news": "Sudarshan News", "swaraj express smbc": "Swaraj Express",
    "samay kolkata": "Samay Kolkata", "news 24 mp & chhattisgarh": "News 24 MP-CG",
    "al jazeera english": "Al Jazeera English", "dw english": "DW English",
    "france 24 english": "France 24 English", "sky news": "Sky News",
    "euronews english hd": "Euronews English", "euronews english": "Euronews English",
    "trt world": "TRT World", "gb news": "GB News", "africanews english": "Africanews",
    "i24news english world": "i24NEWS English", "arirang tv": "Arirang TV",
    "nhk world-japan": "NHK World Japan", "cna international": "CNA International",
    "cnbc uk": "CNBC UK", "bloomberg tv+": "Bloomberg TV+",
}

QUALITY = re.compile(r"\((1080|720|576|540|480|478|400|392|360|1280)p\)")
TAGS = re.compile(r"\[[^\]]*\]")

def norm(name):
    n = TAGS.sub("", QUALITY.sub("", name)).strip()
    n = re.sub(r"\s+HD$", "", n, flags=re.I)   # collapse "X HD" into "X"
    return re.sub(r"\s+", " ", n).strip().lower()

def quality(name):
    m = QUALITY.search(name)
    return int(m.group(1)) if m else 0

# Group by canonical brand, keep best-quality live variant.
groups = collections.defaultdict(list)
for r in ok:
    if EXCLUDE.search(r["name"]):
        continue
    key = norm(r["name"])
    groups[key].append(r)

chosen = []
for key, variants in groups.items():
    # Prefer: has segments, is live, higher resolution, not flagged Not 24/7
    def score(r):
        return (
            1 if r.get("segments", 0) >= 3 else 0,
            1 if r.get("live") else 0,
            0 if "Not 24/7" in r["name"] else 1,
            quality(r["name"]),
        )
    best = max(variants, key=score)
    if best.get("segments", 0) < 3:
        continue  # unproven streams don't ship
    chosen.append({
        "name": RENAME.get(key, re.sub(r"\s*\((?:1080|720|576|540|480|478|400|392|360)p\)", "",
                                        re.sub(r"\s+HD$", "", TAGS.sub("", best["name"]), flags=re.I)).strip()),
        "url": best["url"],
        "group": "News",
        "segments": best.get("segments", 0),
        "flagged": "geo-blocked" if "Geo-blocked" in best["name"] else "",
    })

chosen.sort(key=lambda c: c["name"].lower())

# Write M3U
with open("channels.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for c in chosen:
        f.write(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]}\n{c["url"]}\n')

json.dump(chosen, open("channels.json", "w"), indent=1)
print(f"{len(chosen)} channels written\n")
for c in chosen:
    flag = f"  <-- {c['flagged']}" if c["flagged"] else ""
    print(f"  {c['name']:32} segs={c['segments']:<4}{flag}")
