#!/usr/bin/env python3
"""Probe free/legal live news HLS streams for real, playable video."""
import re, ssl, sys, json, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

def parse(path):
    """Yield (name, url, group, country) from an m3u file."""
    out, pending = [], None
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if line.startswith("#EXTINF"):
            name = line.split(",", 1)[-1].strip()
            grp = (re.search(r'group-title="([^"]*)"', line) or [None, ""])[1]
            cty = (re.search(r'tvg-country="([^"]*)"', line) or [None, ""])[1]
            pending = (name, grp, cty)
        elif line.startswith("http") and pending:
            out.append((pending[0], line, pending[1], pending[2]))
            pending = None
    return out

def get(url, rng=0, timeout=10):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://" + re.sub(r"^https?://([^/]+).*", r"\1", url) + "/",
    })
    if rng:
        req.add_header("Range", f"bytes=0-{rng}")
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.status, r.read(40000).decode("utf-8", "replace"), r.headers.get("Content-Type", "")

def deep_check(item):
    """Two-stage: master playlist -> variant -> confirm media segments exist."""
    name, url, grp, cty = item
    try:
        st, body, ct = get(url)
        if st != 200 or "#EXTM3U" not in body:
            return None
        # master playlist with variants?
        variants = re.findall(r"^(?!#)(https?://\S+|/\S+|[^#\s].*\.m3u8\S*)$", body, re.M)
        if "#EXT-X-STREAM-INF" in body and variants:
            base = url.rsplit("/", 1)[0]
            v = variants[0].strip()
            if v.startswith("http"):
                vurl = v
            elif v.startswith("/"):
                vurl = re.sub(r"^(https?://[^/]+).*", r"\1", url) + v
            else:
                vurl = base + "/" + v
            st2, body2, _ = get(vurl)
            if st2 != 200:
                return None
            body = body2
        segs = len(re.findall(r"\.(?:ts|m4s|aac)(?:\?|\b)", body))
        seg_ok = segs > 0
        live = "#EXT-X-ENDLIST" not in body
        if not seg_ok:
            # try first media line directly
            lines = [l for l in body.splitlines() if l and not l.startswith("#")]
            if lines:
                seg_ok = True
        return {"name": name, "url": url, "group": grp, "country": cty,
                "segments": segs, "live": live, "ct": ct}
    except Exception:
        return None

PRIORITY_IN = [
    "Aaj Tak", "ABP News", "ABP Ananda", "ABP Majha", "ABP Asmita", "ABP Ganga",
    "CNN News 18", "DD News", "DD India", "NDTV 24x7", "NDTV India", "NDTV Profit",
    "Republic Bharat", "Republic TV", "Times Now", "Mirror Now", "India Today",
    "India TV", "News18 India", "Zee News", "Zee Bharat", "WION", "Firstpost",
    "CNBC Awaaz", "CNBC TV18", "ET Now", "Business Today", "India Ahead",
    "News Nation", "Sudarshan News", "Good News Today", "Bharat Express", "NewsX",
    "TV9 Bharatvarsh", "TV9 Telugu", "TV9 Kannada", "ABN Andhra Jyoti",
    "Asianet News", "Asianet Suvarna News", "Manorama News", "Mathrubhumi News",
    "24 News", "Kairali News", "Reporter TV", "Surya News", "Janam TV",
    "PTC News", "News 24", "Samay", "Tez", "Swaraj Express", "India News",
    "Total TV", "NHK World", "CVR News", "10 TV", "99TV", "ETV News",
]

PRIORITY_INTL = [
    "Sky News", "Al Jazeera English", "DW English", "France 24 English",
    "CNA", "CBS News", "Euronews English", "Bloomberg TV+", "NBC News NOW",
    "CNBC", "ABC News", "TRT World", "i24NEWS English", "Arirang",
    "Africanews", "Channel 4 News", "GB News", "LBC News",
]

def main():
    items = []
    items += [i for i in parse("countries_in.m3u") if i[2] == "News"]
    items += [i for i in parse("categories_news.m3u")]

    def want(item):
        nm = item[0]
        base = re.sub(r"\s*\((?:1080|720|576|480|478|360|400)p\)", "", nm).strip()
        base = re.sub(r"\s*\[Not 24/7\]", "", base).strip()
        for p in PRIORITY_IN + PRIORITY_INTL:
            if base.lower() == p.lower() or base.lower().startswith(p.lower()):
                return True
        return False

    cands = [i for i in items if want(i)]
    seen, uniq = set(), []
    for c in cands:
        key = c[0].lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)

    print(f"testing {len(uniq)} candidates...", file=sys.stderr)
    ok = []
    with ThreadPoolExecutor(max_workers=24) as ex:
        for r in ex.map(deep_check, uniq):
            if r:
                ok.append(r)
    ok.sort(key=lambda r: (r["country"] != "IN", r["name"]))
    json.dump(ok, open("verified.json", "w"), indent=1)
    print(f"\n=== VERIFIED LIVE: {len(ok)}/{len(uniq)} ===\n")
    for r in ok:
        flag = "LIVE" if r["live"] else "VOD "
        print(f"{flag} {r['country'] or '??':2} {r['name'][:44]:46} segs={r['segments']:<3}")

main()
