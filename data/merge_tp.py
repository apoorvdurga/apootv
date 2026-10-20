#!/usr/bin/env python3
"""
Final lineup = curated recognizable brands ∩ Tata Play free-to-air (Rs 0.00),
using Tata Play's real channel numbers.

Paid channels are deliberately excluded: their free web feeds are unauthorised
rebroadcasts, not official streams.
"""
import re, json, collections

def norm(s):
    s = s.lower()
    s = re.sub(r"\((1080|720|576|540|480|478|400|396|392|360|288|240)p\)", "", s)
    s = re.sub(r"\[[^\]]*\]", "", s)
    s = re.sub(r"\bhd\+?\b|\bsd\b", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return re.sub(r"\s+", " ", s)

tp = json.load(open("tp_channels.json"))
tp_idx = {}
for c in tp:
    tp_idx[norm(c["name"])] = c

# our canonical name -> name as Tata Play spells it
TP_ALIAS = {
    "ndtv 24x7": "NDTV",
    "al jazeera english": "Al Jazeera",
    "cnbc tv18": "CNBC TV18",
    "cnbc tv18 prime hd": "CNBC TV18 Prime HD",
    "ndtv profit": "NDTV Profit Prime",
    "republic bharat": "R Bharat",
    "goldmines bollywood": "Goldmines Movies",
}

curated = json.load(open("channels.json"))   # from curate_lineup.py

# News and business channels are given away free by their broadcasters even when
# a DTH operator charges carriage. Entertainment/sports/movies that are paid on
# DTH are NOT free anywhere official, so a "free" feed of them is a rebroadcast.
FREE_ANYWAY = {"News", "Business"}

kept, dropped_paid, no_tp = [], [], []
used_numbers = set()
for c in curated:
    n = norm(c["name"])
    hit = tp_idx.get(n)          # exact match only: fuzzy matching produced wrong numbers
    if hit is None and n in TP_ALIAS:
        hit = tp_idx.get(norm(TP_ALIAS[n]))
    if hit is None:
        no_tp.append(c)
        continue
    if hit["price"] > 0.0 and c["genre"] not in FREE_ANYWAY:
        dropped_paid.append((c["name"], hit["price"], hit["number"]))
        continue
    c["number"] = hit["number"]
    c["tp_price"] = hit["price"]
    kept.append(c)

kept.sort(key=lambda c: c["number"])

# channels with no Tata Play listing keep a high block number
for i, c in enumerate(sorted(no_tp, key=lambda x: x["name"])):
    c["number"] = 900 + i
    c["tp_price"] = None
kept += sorted(no_tp, key=lambda c: c["number"])

# guarantee unique numbers
seen = set()
next_free = 950
for c in sorted(kept, key=lambda x: x["number"]):
    if c["number"] in seen:
        while next_free in seen:
            next_free += 1
        c["number"] = next_free
        seen.add(next_free)
    else:
        seen.add(c["number"])
kept.sort(key=lambda c: c["number"])

json.dump(kept, open("channels.json", "w"), indent=1)
with open("channels.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for c in kept:
        f.write(f'#EXTINF:-1 tvg-chno="{c["number"]}" tvg-logo="{c["logo"]}" '
                f'group-title="{c["genre"]}",{c["name"]}\n{c["url"]}\n')

print(f"FINAL: {len(kept)} channels")
print("genre:", dict(collections.Counter(c["genre"] for c in kept)))
print("language:", dict(collections.Counter(c["language"] for c in kept)))
print(f"\nexcluded as paid ({len(dropped_paid)}): "
      + ", ".join(f"{n} (Rs{p:g}, ch{m})" for n, p, m in dropped_paid))
print(f"\nnot in Tata Play, kept separately ({len(no_tp)}): "
      + ", ".join(c["name"] for c in no_tp))
print("\n--- FINAL LINEUP ---")
for c in kept:
    print(f"  {c['number']:5}  {c['name'][:30]:32} {c['genre']:14} {c['language']:8} {c.get('quality',0)}p")
