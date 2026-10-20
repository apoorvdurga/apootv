#!/usr/bin/env python3
"""Liveness-test every candidate; keep only streams that really serve video."""
import re, ssl, json, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

def get(url, timeout=8):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "*/*",
        "Referer": "https://" + re.sub(r"^https?://([^/]+).*", r"\1", url) + "/",
    })
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.status, r.read(50000).decode("utf-8", "replace")

def check(c):
    url = c["url"]
    try:
        st, body = get(url)
        if st != 200 or "#EXTM3U" not in body:
            return None
        variants = [l.strip() for l in body.splitlines()
                    if l.strip() and not l.startswith("#")]
        if "#EXT-X-STREAM-INF" in body and variants:
            base = url.rsplit("/", 1)[0]
            v = variants[0]
            if v.startswith("http"):
                vurl = v
            elif v.startswith("/"):
                vurl = re.sub(r"^(https?://[^/]+).*", r"\1", url) + v
            else:
                vurl = base + "/" + v
            st2, body2 = get(vurl)
            if st2 != 200:
                return None
            body = body2
        segs = len(re.findall(r"\.(?:ts|m4s|aac|mp4)(?:\?|\b)", body))
        if segs == 0:
            return None
        out = dict(c)
        out["segments"] = segs
        out["live"] = "#EXT-X-ENDLIST" not in body
        return out
    except Exception:
        return None

cands = json.load(open("candidates.json"))
print(f"testing {len(cands)}...", file=sys.stderr)
ok = []
with ThreadPoolExecutor(max_workers=40) as ex:
    for i, r in enumerate(ex.map(check, cands), 1):
        if r:
            ok.append(r)
        if i % 200 == 0:
            print(f"  {i}/{len(cands)}  alive={len(ok)}", file=sys.stderr)

json.dump(ok, open("verified_all.json", "w"), indent=1)
print(f"\nALIVE: {len(ok)}/{len(cands)}")
import collections
print("genres:", dict(collections.Counter(c["genre"] for c in ok).most_common()))
print("region:", dict(collections.Counter(c["region"] for c in ok)))
