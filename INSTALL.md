# ApooTV — install instructions

A small TV app with ~138 live Hindi and English channels, laid out on Tata Play
channel numbers. Free channels only — no subscription needed.

**File:** `ApooTV-1.1.apk` (3.5 MB)

Not on the Play Store or Amazon Appstore, so it has to be "sideloaded". That
sounds technical but is about five minutes of tapping. Pick the section for
your device.

---

## Before you start

You need the `.apk` file on the TV. The easiest way is the free **Downloader**
app, which can fetch a file from a web address directly on the TV — no computer
needed.

---

## Amazon Fire TV / Fire TV Stick

1. From the Fire TV home screen, go to **Find → Search** and type
   **Downloader**. Install it (the orange icon, by AFTVnews).
2. Go to **Settings → My Fire TV → Developer Options**.
   - If you don't see *Developer Options*, open **About → Fire TV Stick** and
     click it **7 times**, then go back one screen.
3. Turn **ADB debugging** ON and **Apps from Unknown Sources** ON.
4. Open **Downloader** and allow it to access storage if asked.
5. In the URL box, type the address you were sent, and press Go.
6. When the download finishes, Downloader offers **Install**. Choose it.
7. If Fire TV blocks it, choose **Settings** from the popup and allow the
   install for Downloader, then go back and press Install again.

The app appears on your home row under **Your Apps & Channels → See All**.

---

## Google TV / Android TV (Sony, TCL, Hisense, Chromecast, etc.)

1. From the home screen, open the **Play Store** and install **Downloader**
   (by AFTVnews).
2. Go to **Settings → System → About** and click **Android TV OS build**
   **7 times** until it says you're a developer.
3. Go back to **Settings → System → Developer options** and turn on
   **USB debugging** (some brands call it *Debug over network*).
4. Open **Downloader** and allow it to access files when asked.
5. Type the address you were sent in the URL box, press Go.
6. When the download finishes, press **Install**. Google TV will ask you to
   allow installs from Downloader — allow it, then press Install again.

The app appears in the **Apps** row on the home screen.

---

## Using it

| Button | What it does |
|---|---|
| **D-pad** | Move around the channel grid |
| **OK / Select** | Play the highlighted channel |
| **Hold OK** | Add / remove a favourite (★) |
| **◀ ▶ while playing** | Change channel, no need to go back to the grid |
| **BACK** | Return to the channel grid |
| **MENU** (Fire TV only) | 2×2 mosaic — four channels at once |

Filters along the top narrow by **Genre** (News, Movies, Sports, Music…),
**Language** (Hindi / English) and **Region**. There's also a **Recent** list and
a **Mosaic** button on remotes without a MENU key.

Channel numbers match Tata Play, so if you're used to "508 is Aaj Tak" that
still works.

---

## Honest notes

- **Paid channels are not included.** Colors, Star Sports, Sony Sports, Cartoon
  Network and similar are subscription channels — their free web feeds are
  unauthorised copies, so the app won't carry them. Use JioTV / Airtel Xstream
  / your DTH app for those.
- **Some channels may stop working.** These are free public streams that
  broadcasters occasionally move. A few are also region-locked.
- **This is not an official product.** It's a personal project shared with
  friends. It's not on any store, it doesn't collect any data, and there's no
  support line.
- **It only works on Android-based TVs** — Fire TV, Google TV, Android TV.
  It will not run on an LG (webOS) or Samsung (Tizen) TV.
