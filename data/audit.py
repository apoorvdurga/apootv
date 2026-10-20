import json, re, ssl, urllib.request
from concurrent.futures import ThreadPoolExecutor
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"
CTX=ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
def get(u):
    r=urllib.request.Request(u,headers={"User-Agent":UA})
    with urllib.request.urlopen(r,timeout=9,context=CTX) as x:
        return x.status,x.read(60000).decode("utf-8","replace")
def check(c):
    try:
        st,b=get(c["url"])
        if st!=200 or "#EXTM3U" not in b: return c["number"],c["name"],"HTTP %s"%st
        v=[l.strip() for l in b.splitlines() if l.strip() and not l.startswith("#")]
        if "#EXT-X-STREAM-INF" in b and v:
            base=c["url"].rsplit("/",1)[0]
            vu=v[0] if v[0].startswith("http") else (re.sub(r"^(https?://[^/]+).*",r"\1",c["url"])+v[0] if v[0].startswith("/") else base+"/"+v[0])
            st2,b2=get(vu)
            if st2!=200: return c["number"],c["name"],"variant %s"%st2
            b=b2
        if not re.search(r"\.(?:ts|m4s|aac|mp4)(?:\?|\b)",b): return c["number"],c["name"],"no segments"
        return c["number"],c["name"],"OK"
    except Exception as e:
        return c["number"],c["name"],type(e).__name__
ch=json.load(open("channels.json"))
with ThreadPoolExecutor(max_workers=20) as ex:
    res=list(ex.map(check,ch))
bad=[r for r in res if r[2]!="OK"]
print(f"working {len(res)-len(bad)}/{len(res)}")
print("\n--- FAILING ---")
for n,name,st in sorted(bad): print(f"  {n:5} {name:26} {st}")
json.dump([{"number":n,"name":nm,"status":s} for n,nm,s in res],open("audit.json","w"),indent=1)
