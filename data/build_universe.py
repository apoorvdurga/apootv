#!/usr/bin/env python3
"""Build a genre/language-tagged candidate universe from the iptv-org catalogs."""
import re, json, collections

def parse(path):
    """-> list of dicts: name, url, group, logo"""
    out, cur = [], None
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if line.startswith("#EXTINF"):
            name = line.split(",", 1)[-1].strip()
            logo = (re.search(r'tvg-logo="([^"]*)"', line) or [None, ""])[1]
            grp = (re.search(r'group-title="([^"]*)"', line) or [None, ""])[1]
            cur = {"name": name, "logo": logo, "group": grp}
        elif line.startswith("http") and cur:
            cur["url"] = line
            out.append(cur)
            cur = None
    return out

genre_map = json.load(open("meta/genre_map.json"))
lang_map = json.load(open("meta/lang_map.json"))
LANG_NAMES = json.load(open("meta/language_names.json"))

INDIAN_LANGS = ["hin","eng","tam","tel","kan","mal","mar","ben","guj","pan","urd",
                "asm","ori","bho","mai","kok","nep","san","sat","man"]

GENRE_LABEL = {
 "news":"News","sports":"Sports","entertainment":"Entertainment","movies":"Movies",
 "music":"Music","kids":"Kids","documentary":"Documentary","general":"General",
 "education":"Education","culture":"Culture","business":"Business","weather":"Weather",
 "lifestyle":"Lifestyle","family":"Family","science":"Science","comedy":"Comedy",
 "animation":"Animation","series":"Series","religious":"Religious","travel":"Travel",
 "cooking":"Cooking","auto":"Auto","outdoor":"Outdoor","shop":"Shopping","relax":"Relax",
 "legislative":"Legislative",
}

cands = collections.OrderedDict()   # url -> record

def add(rec, region, default_genre=None):
    url = rec["url"]
    if url in cands:
        return
    gl = genre_map.get(url, [])
    gl = [g for g in gl if g != "undefined"]
    genre = GENRE_LABEL.get(gl[0], "General") if gl else (default_genre or "General")

    langs = lang_map.get(url, [])
    # prefer an Indian language label when one exists
    order = [l for l in langs if l in INDIAN_LANGS] + [l for l in langs if l not in INDIAN_LANGS]
    language = LANG_NAMES.get(order[0], "Other") if order else None

    cands[url] = {
        "name": rec["name"], "url": url, "logo": rec.get("logo",""),
        "genre": genre, "language": language, "region": region,
    }

# 1) everything Indian, all genres
for rec in parse("countries_in.m3u"):
    add(rec, "IN")

# 2) Indian-language playlists (catches channels filed under other regions)
#    English is excluded here: it is a global playlist, not an India signal.
for code in [c for c in INDIAN_LANGS if c != "eng"]:
    try:
        for rec in parse(f"meta/lang_{code}.m3u"):
            add(rec, "IN")
    except FileNotFoundError:
        pass

# 3) international spread per genre
PICKS = {"news":45,"sports":40,"entertainment":35,"movies":30,"music":25,
         "kids":20,"documentary":25,"business":15,"lifestyle":15,"comedy":15,
         "series":15,"animation":10}
for g, limit in PICKS.items():
    try:
        recs = parse(f"meta/genre_{g}.m3u")
    except FileNotFoundError:
        continue
    n = 0
    for rec in recs:
        if n >= limit:
            break
        if rec["url"] in cands:
            continue
        add(rec, "INTL", default_genre=GENRE_LABEL[g])
        n += 1

out = list(cands.values())
json.dump(out, open("candidates.json","w"), indent=1)

print(f"candidates: {len(out)}")
by_g = collections.Counter(c["genre"] for c in out)
print("genres:", dict(by_g.most_common()))
by_r = collections.Counter(c["region"] for c in out)
print("region:", dict(by_r))
known = sum(1 for c in out if c["language"])
print(f"language known: {known}/{len(out)}")
