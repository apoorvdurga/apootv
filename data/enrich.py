import json, re, glob

# url -> tvg-logo, harvested from the raw catalogs
logos = {}
for path in glob.glob("*.m3u"):
    if path == "channels.m3u":
        continue
    pending = None
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if line.startswith("#EXTINF"):
            m = re.search(r'tvg-logo="([^"]*)"', line)
            pending = m.group(1) if m else ""
        elif line.startswith("http") and pending is not None:
            if pending:
                logos.setdefault(line, pending)
            pending = None

ch = json.load(open("channels.json"))
hit = 0
for c in ch:
    lg = logos.get(c["url"], "")
    c["logo"] = lg
    if lg:
        hit += 1
json.dump(ch, open("channels.json", "w"), indent=1)
print(f"{hit}/{len(ch)} channels have logos")

# Tag region: was this URL sourced from the India catalog?
india = set()
pending = None
for line in open("countries_in.m3u", encoding="utf-8", errors="replace"):
    line = line.strip()
    if line.startswith("http"):
        india.add(line)

ch = json.load(open("channels.json"))
for c in ch:
    c["region"] = "IN" if c["url"] in india else "INTL"
json.dump(ch, open("channels.json", "w"), indent=1)
inr = sum(1 for c in ch if c["region"] == "IN")
print(f"region tagged: {inr} IN / {len(ch)-inr} INTL")
