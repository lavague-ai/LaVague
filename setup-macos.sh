#!/bin/bash

# Base URL for downloads
BASE_URL="https://storage.googleapis.com/chrome-for-testing-public/123.0.6312.105"

# Determine OS
OS="unknown"
case "$(uname -s)" in
    Linux*)     OS="linux";;
    Darwin*)    OS="mac";;
    CYGWIN*|MINGW32*|MSYS*|MINGW*) OS="win";;
    *)          OS="unknown";;
esac

# Determine architecture
ARCH="unknown"
case "$(uname -m)" in
    x86_64*)    ARCH="x64";;
    arm64*)     ARCH="arm64";;
    *)          ARCH="unknown";;
esac


if [[ $OS == "mac" ]]; then
    # Special handling for Mac to differentiate between Intel (x64) and Apple Silicon (arm64)
    if sysctl -n machdep.cpu.brand_string | grep -q "Intel"; then
        ARCH="x64"
    else
        ARCH="arm64"
    fi
else
    echo "Unsupported OS or architecture."
    exit 1
fi

# Choose the right download based on your need: chrome, chromedriver, or chrome-headless-shell
DRIVER="chromedriver-${OS}-${ARCH}"
CHROME="chrome-${OS}-${ARCH}"

# Construct the download URLs
DRIVER_FILENAME="${DRIVER}.zip"
DRIVER_URL="${BASE_URL}/${OS}-${ARCH}/${DRIVER_FILENAME}"
echo $DRIVER_URL

CHROME_FILENAME="${CHROME}.zip"
CHROME_URL="${BASE_URL}/${OS}-${ARCH}/${CHROME_FILENAME}"
echo $CHROME_URL


# Download Chromedriver then unzip downloaded files, move to home and clean up
wget $DRIVER_URL
unzip $DRIVER_FILENAME
mv $DRIVER/ ~/
mv ~/$DRIVER ~/chromedriver-testing
rm  $DRIVER_FILENAME


# Download Chrome binary then unzip downloaded files, move to home and clean up
wget $CHROME_URL
unzip $CHROME_FILENAME
mv $CHROME/ ~/
mv ~/$CHROME/ ~/chrome-testing
rm $CHROME_FILENAME


# Update package lists and install necessary packages
sudo apt update
sudo apt install -y ca-certificates fonts-liberation unzip \
libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 libc6 \
libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1 \
libgcc1 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 \
libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 \
libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 \
libxrandr2 libxrender1 libxss1 libxtst6 lsb-release wget xdg-utils

# Install LaVague from main of GitHub repo
git clone https://github.com/lavague-ai/LaVague.git
pip install -e LaVague

# Change directory to LaVague
cd LaVague

# Print success message
echo -e "\e[32mAll steps completed successfully.\e[0m"