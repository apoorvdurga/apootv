# ApooTV — project status

Native Android TV app for the Fire TV Stick 4K Max (`192.168.68.54`, AFTKA, Fire OS 7.6.8.8, API 28, armeabi-v7a).

Package `com.apoo.tv` · APK `~/Developer/NewsWall/ApooTV.apk`

## Current state — working

- Native app (not a web app): Java + ExoPlayer/media3, hardware-decoded HLS.
- **71 channels**, curated: curated brand allowlist ∩ Tata Play free/cheap-news rules.
- Real **Tata Play channel numbers** on the guide tiles and in the player OSD.
- Filters: Genre / Language / Region. **Hindi + English only** by request.
- Surf model: ◀ ▶ change channel in place with OSD
  (`◀ prev — CH n — next ▶`), no trip back to the guide.
- **Recent** list (last 40 played) as a filter chip.
- Favourites (hold OK on a tile), persisted.
- **Mosaic**: MENU shows 2×2 simultaneous feeds, muted; OK opens one fullscreen.
- In-app channel-list updater (`Update.java`) — falls back to bundled catalog.

## Channel policy (important)

- **Paid entertainment/sports/movies excluded** (Colors, Star Sports, Sony Sports,
  Cartoon Network, Nat Geo…). Their "free" web feeds are unauthorised rebroadcasts,
  not official streams.
- **Paid news/business included** (Aaj Tak ₹2.95, NDTV 24x7, Times Now, CNBC-TV18).
  Broadcasters give these away free on their own sites, so the free feed is
  legitimate. DTH carriage fee ≠ paid channel.
- Broadcaster-official feeds preferred where reachable:
  Aaj Tak 1080p (`feeds.intoday.in`), NDTV 24x7 + NDTV India 720p (Akamai).

## Build

Built on the MiniPC (744 GB free vs 16 GB on the Mac), not the Mac.

```bash
rsync -az --delete -e "ssh -i ~/.ssh/id_ed25519" \
  --exclude '.gradle' --exclude 'build' \
  ./ minipc:~/newswall-android/
ssh minipc 'cd ~/newswall-android &&
  JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
  ANDROID_HOME=$HOME/android-sdk \
  ~/gradle-8.2/bin/gradle --no-daemon assembleDebug'
```

Install: `adb connect 192.168.68.54:5555 && adb install -r ApooTV.apk`

## Data pipeline (`data/`)

| script | purpose |
|---|---|
| `fetch_meta.py` | pulls iptv-org genre + language playlists → `meta/` |
| `build_universe.py` | candidate set with genre/language tags |
| `probe_all.py` | liveness-tests candidates → `verified_all.json` |
| `curate_lineup.py` | curated brand allowlist, Hindi/English, rescue pass |
| `match_tp.py` | maps Tata Play FTA channels to working feeds |
| `merge_tp.py` | **final**: allowlist ∩ Tata Play, real numbers, paid rules |

`tp_channels.json` — 662 Tata Play channels scraped with Playwright from
`tataplay.com/channels/tv-channel-number-list` (name, HD, number, price).
330 are ₹0.00 free-to-air.

Regenerate the lineup: `python3 curate_lineup.py && python3 merge_tp.py`

## Open items

- `Update.java` `CHANNEL_URL` still points at a LAN placeholder
  (`http://192.168.68.69:8080/channels.json`). Point it at a static host
  (GitHub raw / S3) for true server independence.
- 5 brands have no free feed anywhere: Republic TV, Republic Bharat,
  Good News Tonight, Sudarshan, Firstpost (app/YouTube only).
- No channel-number entry (Fire TV remote has no keypad); could add a jump grid.
- Screensaver: handled with `keepScreenOn` on the guide; verify it holds.

## Evidence paths

- `/Users/apoorv/Developer/NewsWall/android/app/src/main/java/com/apoo/tv/`
- `/Users/apoorv/Developer/NewsWall/data/channels.json`
- `/Users/apoorv/Developer/NewsWall/ApooTV.apk`
- `/Users/apoorv/Developer/tp-scrape/tp_channels.json`
