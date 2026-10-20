# AGENTS.md — installing ApooTV on a TV

Instructions for an AI agent asked to install this app on someone's TV.

## What you are installing

A single Android APK (`com.apoo.tv`, v1.2) onto an **Android-based** TV:
Fire TV, Google TV, or Android TV. It is **not** for LG (webOS) or Samsung
(Tizen) sets — check first, and stop if the TV is neither.

The app streams free-to-air live channels. It collects no data, requests only
`INTERNET` and `ACCESS_NETWORK_STATE`, and has no accounts, telemetry or ads.

## The one step you cannot do

ADB must be enabled **by the person holding the remote**, and the TV will show
an on-screen `Allow USB debugging?` prompt that they must accept. There is no
way to do this remotely. If it is not already enabled, hand these steps to the
user and wait:

- **Google TV / Android TV:** Settings → System → About → click
  *Android TV OS build* 7×, then Settings → System → Developer options →
  **USB debugging** on.
- **Fire TV:** Settings → My Fire TV → About → click the device name 7×, then
  My Fire TV → **Developer options** → **ADB debugging** on.

## Preferred path

```bash
git clone https://github.com/apoorvdurga/apootv
cd apootv
./install.sh <TV_IP_ADDRESS>
```

The script connects over ADB, downloads the APK from the latest release,
verifies its SHA-256, installs it, and launches it. Run `./install.sh --verify`
to check the download without touching any device.

If the TV is already connected via ADB, `./install.sh` with no argument uses it.
Otherwise pass the TV's LAN IP.

## Manual path

```bash
adb connect <TV_IP>:5555
adb -s <TV_IP>:5555 install -r ApooTV-1.2.apk
adb -s <TV_IP>:5555 shell am start -n com.apoo.tv/.MainActivity
```

## Verify what you installed

| Check | Expected |
|---|---|
| Package | `com.apoo.tv` |
| Version | `1.2` (versionCode 3) |
| APK SHA-256 | `2ed7d515d2380b766b5c758a83c17a252a7c870f7f90cadeab0f18119e04ff83` |
| Signer SHA-256 | `A3:6D:FA:D6:78:84:86:89:F8:AA:97:58:0D:20:E0:14:CC:4F:61:31:9D:45:66:5D:64:0D:15:9A:AA:72:2C:5D` |

```bash
adb shell dumpsys package com.apoo.tv | grep versionName
adb shell pm list packages | grep com.apoo.tv
```

Reject the download and stop if the checksum does not match.

## Failure modes

| Symptom | Cause | Action |
|---|---|---|
| `Connection refused` on :5555 | ADB not enabled | Ask the user to enable it (above). |
| State `unauthorized` | RSA prompt unanswered | Ask the user to accept it on the TV. |
| No device on `adb mdns services` | TV on another network / guest Wi-Fi | Ask the user to join the same LAN. |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | A build signed with a different key is installed | Only with the user's explicit consent: `adb uninstall com.apoo.tv` (this deletes their favourites and recents), then reinstall. |
| `INSTALL_FAILED_USER_RESTRICTED` | Unknown sources blocked | User must allow installs from unknown sources. |
| Installs fine, nothing on screen | TV asleep / another app in front | `adb shell input keyevent 224` then relaunch. |

## Do not

- Do not uninstall `com.apoo.tv` without explicit confirmation — it destroys the
  user's favourites and recent-channel history.
- Do not install from any mirror or fork. Use only the URLs in this repository;
  verify the checksum.
- Do not enable or change other TV settings beyond what is required.
- Do not treat a screenshot as proof of failure on TCL/Google TV panels: those
  firmware builds exclude the video plane from `screencap` and `screenrecord`,
  so playback appears black in captures even when it is working. Confirm with
  the user instead.

## Updating later

The app fetches its channel list from
`https://raw.githubusercontent.com/apoorvdurga/apootv/main/channels.json` on
launch and falls back to its bundled copy if that fails. Channel changes
therefore reach installed copies without reinstalling. Only a new APK (new
version) needs `install.sh` again.
