# ApooTV

A small Android TV app for watching free live Indian channels — Hindi and
English only, numbered the way Tata Play numbers them.

Built for a Fire TV Stick 4K Max and a Google TV set. Runs on any Android-based
TV (Fire TV, Google TV, Android TV).

## What it does

- **138 channels**, free-to-air only: news, business, movies, music, sports,
  kids, devotional, lifestyle.
- **Tata Play channel numbers** — Aaj Tak is 508, NDTV India 506, ABP News 504.
- Filter by **genre**, **language** (Hindi/English) and **region**.
- **Surf**: ◀ ▶ changes channel in place with an on-screen OSD.
- **Recent** list and **favourites** (hold OK on a tile).
- **2×2 mosaic** — four feeds at once (MENU, or the on-screen Mosaic chip).

## Install

See [INSTALL.md](INSTALL.md). Grab the APK from the
[Releases](../../releases) page.

## What it deliberately excludes

Subscription channels — Colors, Star Sports, Sony Sports, Cartoon Network,
National Geographic and similar. Their broadcasters do not publish a free
official stream, so any "free" feed of them online is an unauthorised
rebroadcast. The app does not carry those.

News and business channels are included even where a DTH operator charges a
carriage fee, because those broadcasters stream them free on their own sites.

## Channel list

`channels.json` at the repo root is the live channel list. The app fetches it on
launch and falls back to its bundled copy if the fetch fails, so updates can ship
without a new APK.

## Rebuilding the lineup

```
cd data
python3 fetch_meta.py       # pull iptv-org genre + language playlists
python3 build_universe.py   # tag candidates by genre/language
python3 probe_all.py        # liveness-test every candidate
python3 curate_lineup.py    # curated brand allowlist, rescue pass
python3 merge_tp.py         # map to Tata Play numbers
python3 final_lineup.py     # final: union, dedupe by URL, verify, publish
```

`tp_channels.json` holds Tata Play's channel list (number, HD flag, price),
scraped from `tataplay.com/channels/tv-channel-number-list`.

## Build

Requires JDK 17 and Android SDK 34.

```
cd android
./gradlew assembleRelease
```

Release builds are signed from `keystore.properties` (not committed). Use the
same keystore for every release or installed copies cannot upgrade in place.
