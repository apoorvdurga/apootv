#!/usr/bin/env bash
# Install ApooTV on an Android-based TV (Fire TV / Google TV / Android TV).
#
# Usage:
#   ./install.sh                # auto-discover the TV on the local network
#   ./install.sh 192.168.1.50   # target a specific TV
#   ./install.sh --verify       # check the download and checksum only, touch nothing
#
# Requires adb on PATH (https://developer.android.com/tools/releases/platform-tools).
# This script only downloads the APK, verifies it, installs it and launches it.
# It never uninstalls anything and never deletes app data.

set -euo pipefail

APK_URL="https://github.com/apoorvdurga/apootv/releases/download/v1.2/ApooTV-1.2.apk"
EXPECTED_SHA256="2ed7d515d2380b766b5c758a83c17a252a7c870f7f90cadeab0f18119e04ff83"
PKG="com.apoo.tv"
ACTIVITY="com.apoo.tv/.MainActivity"

say() { printf '%s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# ---------- dependency check ----------
command -v adb >/dev/null 2>&1 || die "adb not found. Install Android platform-tools and put adb on PATH."
command -v shasum >/dev/null 2>&1 || command -v sha256sum >/dev/null 2>&1 \
  || die "need shasum (macOS) or sha256sum (Linux) to verify the download."

sha_of() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}';
  else sha256sum "$1" | awk '{print $1}'; fi
}

# ---------- download + verify ----------
fetch_apk() {
  local out="$1"
  say "Downloading $APK_URL"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL --max-time 180 -o "$out" "$APK_URL"
  else
    die "curl not found"
  fi
  local got; got="$(sha_of "$out")"
  if [ "$got" != "$EXPECTED_SHA256" ]; then
    die "checksum mismatch — refusing to install.
  expected: $EXPECTED_SHA256
  got:      $got"
  fi
  say "Checksum OK."
}

if [ "${1:-}" = "--verify" ]; then
  tmp="$(mktemp -d)/ApooTV.apk"
  fetch_apk "$tmp"
  say "APK verified. Nothing installed."
  exit 0
fi

# ---------- find the target ----------
TARGET="${1:-}"

if [ -z "$TARGET" ]; then
  say "Looking for an existing adb device..."
  EXISTING="$(adb devices | awk 'NR>1 && $2=="device" {print $1; exit}')"
  if [ -n "$EXISTING" ]; then
    TARGET="$EXISTING"
    say "Using already-connected device: $TARGET"
  else
    say "No device connected. Browsing the network (adb mdns)..."
    # adb mdns lists wireless-debugging services as: <name> _adb-tls-connect._tcp. <addr>:<port>
    FOUND="$(adb mdns services 2>/dev/null | awk 'NR>1 {print $NF}' | head -1 || true)"
    if [ -z "$FOUND" ]; then
      die "No TV found automatically.
On the TV, enable: Settings > System > Developer options > USB debugging.
(On Fire TV: Settings > My Fire TV > About > click the device name 7x, then
 Developer Options > ADB debugging.)
Then re-run: ./install.sh <TV_IP_ADDRESS>"
    fi
    TARGET="$FOUND"
    say "Found: $TARGET"
  fi
fi

# ---------- connect ----------
case "$TARGET" in
  *:*) ADDR="$TARGET" ;;
  *)   ADDR="$TARGET:5555" ;;
esac

say "Connecting to $ADDR ..."
adb connect "$ADDR" >/dev/null 2>&1 || true

STATE=""
for _ in $(seq 1 10); do
  STATE="$(adb -s "$ADDR" get-state 2>/dev/null || true)"
  [ "$STATE" = "device" ] && break
  sleep 2
done

if [ "$STATE" = "unauthorized" ]; then
  die "The TV is asking for permission.

Look at the TV screen: an 'Allow USB debugging?' dialog should be showing.
Tick 'Always allow from this computer' and choose Allow, then re-run this script."
fi

[ "$STATE" = "device" ] || die "Could not reach the TV at $ADDR (state: ${STATE:-none}).
Check that ADB/USB debugging is enabled and that the TV is on the same network."

# ---------- install ----------
tmp="$(mktemp -d)/ApooTV.apk"
fetch_apk "$tmp"

say "Installing on $ADDR ..."
if ! adb -s "$ADDR" install -r "$tmp" 2>&1 | tee /tmp/apootv_install.log | grep -q "Success"; then
  if grep -q "INSTALL_FAILED_UPDATE_INCOMPATIBLE" /tmp/apootv_install.log; then
    die "A different build of ApooTV is already installed with another signing key.
Uninstall it first (this removes favourites and recents):
  adb -s $ADDR uninstall $PKG
then re-run this script."
  fi
  if grep -qi "INSTALL_FAILED_USER_RESTRICTED\|unknown sources" /tmp/apootv_install.log; then
    die "The TV blocked the install. Allow installs from unknown sources for your
file manager / ADB, then re-run."
  fi
  die "Install failed. See /tmp/apootv_install.log"
fi

# ---------- launch ----------
say "Launching..."
adb -s "$ADDR" shell am start -n "$ACTIVITY" >/dev/null 2>&1 || true
say "Done. ApooTV should now be open on the TV."
say "It also appears in the TV's app list as 'ApooTV'."
