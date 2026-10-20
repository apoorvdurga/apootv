#!/usr/bin/env python3
"""Dedupe verified streams into the final channels.json consumed by the app."""
import re, json, collections

ok = json.load(open("verified_all.json"))

QUALITY = re.compile(r"\s*\((1080|720|576|540|480|478|400|392|360|288|240)p\)")
TAGS = re.compile(r"\s*\[[^\]]*\]")

# Obvious noise / non-channels
JUNK = re.compile(r"^(test|demo|unknown|undefined)\b", re.I)

def clean_name(n):
    n = TAGS.sub("", n)
    n = QUALITY.sub("", n).strip()
    n = re.sub(r"\s+HD$", "", n, flags=re.I)
    return re.sub(r"\s+", " ", n).strip()

def quality(n):
    m = QUALITY.search(n)
    return int(m.group(1)) if m else 0

best = {}
for c in ok:
    nm = clean_name(c["name"])
    if not nm or JUNK.match(nm):
        continue
    key = nm.lower()
    score = (
        1 if c.get("segments", 0) >= 5 else 0,
        1 if c.get("live") else 0,
        quality(c["name"]),
    )
    prev = best.get(key)
    if prev is None or score > prev[0]:
        best[key] = (score, {**c, "name": nm})

rows = [v[1] for v in best.values()]

# Re-split channels that were double-filed into several genres: keep the most
# specific one, preferring content genres over "General".
PRIORITY = ["News","Sports","Entertainment","Movies","Music","Kids","Documentary",
            "Business","Lifestyle","Culture","Education","Comedy","Series",
            "Animation","Family","Religious","Travel","Science","Cooking","Auto",
            "Weather","Legislative","General"]
by_url = {}
for r in rows:
    by_url.setdefault(r["url"], []).append(r)

final = []
for url, group in by_url.items():
    group.sort(key=lambda r: PRIORITY.index(r["genre"]) if r["genre"] in PRIORITY else 99)
    final.append(group[0])

final.sort(key=lambda c: (PRIORITY.index(c["genre"]) if c["genre"] in PRIORITY else 99,
                          c["name"].lower()))

# tidy fields
for c in final:
    c.pop("segments", None)
    c.pop("live", None)
    if not c.get("language"):
        c["language"] = "Unknown"

json.dump(final, open("channels.json", "w"), indent=1)

with open("channels.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for c in final:
        f.write(f'#EXTINF:-1 tvg-logo="{c["logo"]}" group-title="{c["genre"]}",'
                f'{c["name"]}\n{c["url"]}\n')

g = collections.Counter(c["genre"] for c in final)
l = collections.Counter(c["language"] for c in final)
print(f"FINAL: {len(final)} channels")
print("\ngenre:", dict(g.most_common()))
print("\nlanguage:", dict(l.most_common(14)))
