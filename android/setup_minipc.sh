#!/usr/bin/env bash
set -euo pipefail

echo "=== [1/4] apt packages ==="
sudo apt-get update -qq
sudo apt-get install -y -qq openjdk-17-jdk-headless unzip >/dev/null
java -version 2>&1 | head -2

echo "=== [2/4] android cmdline tools ==="
SDK="$HOME/android-sdk"
mkdir -p "$SDK/cmdline-tools"
if [ ! -x "$SDK/cmdline-tools/latest/bin/sdkmanager" ]; then
  cd /tmp
  curl -sSL -o cmdline.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
  unzip -q -o cmdline.zip -d "$SDK/cmdline-tools"
  mv "$SDK/cmdline-tools/cmdline-tools" "$SDK/cmdline-tools/latest" 2>/dev/null || true
fi
export ANDROID_HOME="$SDK"
export PATH="$SDK/cmdline-tools/latest/bin:$SDK/platform-tools:$PATH"
sdkmanager --version

echo "=== [3/4] install sdk components ==="
yes 2>/dev/null | sdkmanager --licenses >/dev/null || true
sdkmanager "platform-tools" "platforms;android-33" "build-tools;33.0.2" >/dev/null
echo "platforms:"; ls "$SDK/platforms"
echo "build-tools:"; ls "$SDK/build-tools"

echo "=== [4/4] env file ==="
cat > "$HOME/.newswall-env" <<EOF
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export ANDROID_HOME=$SDK
export ANDROID_SDK_ROOT=$SDK
export PATH=\$JAVA_HOME/bin:$SDK/cmdline-tools/latest/bin:$SDK/platform-tools:\$PATH
EOF
echo "done"
