#!/usr/bin/env python3
"""Fetch iptv-org genre + language playlists and build url -> metadata maps."""
import os, re, json, urllib.request
from concurrent.futures import ThreadPoolExecutor

GENRES = ["news","sports","entertainment","movies","music","kids","documentary",
          "general","education","culture","business","weather","lifestyle",
          "family","science","comedy","animation","series","religious","travel",
          "cooking","auto","outdoor","shop","relax","legislative","undefined"]

LANGUAGES = {
 "hin":"Hindi","eng":"English","tam":"Tamil","tel":"Telugu","kan":"Kannada",
 "mal":"Malayalam","mar":"Marathi","ben":"Bengali","guj":"Gujarati","pan":"Punjabi",
 "urd":"Urdu","asm":"Assamese","ori":"Odia","san":"Sanskrit","kok":"Konkani",
 "mai":"Maithili","bho":"Bhojpuri","nep":"Nepali","sat":"Santali","man":"Manipuri",
 "brx":"Bodo","dog":"Dogri","kas":"Kashmiri","mni":"Meitei","tcy":"Tulu",
 "ara":"Arabic","fra":"French","deu":"German","spa":"Spanish","rus":"Russian",
 "jpn":"Japanese","kor":"Korean","zho":"Chinese","por":"Portuguese","ita":"Italian",
 "tur":"Turkish","ind":"Indonesian","tha":"Thai","vie":"Vietnamese","sin":"Sinhala",
 "fas":"Persian","heb":"Hebrew","nld":"Dutch","pol":"Polish","ukr":"Ukrainian",
 "swe":"Swedish","dan":"Danish","nor":"Norwegian","fin":"Finnish","ell":"Greek",
 "ron":"Romanian","hun":"Hungarian","ces":"Czech","bul":"Bulgarian","hrv":"Croatian",
 "srp":"Serbian","slk":"Slovak","slv":"Slovenian","lit":"Lithuanian","lav":"Latvian",
 "est":"Estonian","cat":"Catalan","eus":"Basque","gle":"Irish","cym":"Welsh",
}

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        return ""

def parse_urls(text):
    return [l.strip() for l in text.splitlines() if l.strip().startswith("http")]

os.makedirs("meta", exist_ok=True)

jobs = [("genre", g, f"https://iptv-org.github.io/iptv/categories/{g}.m3u") for g in GENRES]
jobs += [("lang", code, f"https://iptv-org.github.io/iptv/languages/{code}.m3u") for code in LANGUAGES]

def do(job):
    kind, key, url = job
    txt = fetch(url)
    if not txt or "#EXT" not in txt:
        return kind, key, []
    urls = parse_urls(txt)
    with open(f"meta/{kind}_{key}.m3u", "w") as f:
        f.write(txt)
    return kind, key, urls

genre_map, lang_map = {}, {}
with ThreadPoolExecutor(max_workers=16) as ex:
    for kind, key, urls in ex.map(do, jobs):
        target = genre_map if kind == "genre" else lang_map
        for u in urls:
            target.setdefault(u, []).append(key)
        print(f"  {kind:5} {key:12} {len(urls):5}")

json.dump(genre_map, open("meta/genre_map.json","w"))
json.dump(lang_map, open("meta/lang_map.json","w"))
json.dump(LANGUAGES, open("meta/language_names.json","w"), indent=1)
print(f"\nurls with genre: {len(genre_map)}   with language: {len(lang_map)}")
