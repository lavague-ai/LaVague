#!/bin/bash

set -e

# install chromium and chrome-driver
read -p "

Please check the following dependencies are installed :

ca-certificates fonts-liberation unzip\
libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 libc6\
libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1\
libgcc1 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0\
libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1\
libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6\
libxrandr2 libxrender1 libxss1 libxtst6 lsb-release wget xdg-utils

You can Quit this installer if needed.
Press Enter to continue."

wget https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chrome-linux64.zip
wget https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.94/linux64/chromedriver-linux64.zip
unzip chrome-linux64.zip
unzip chromedriver-linux64.zip
rm chrome-linux64.zip chromedriver-linux64.zip
