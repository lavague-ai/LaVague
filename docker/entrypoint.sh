#!/usr/bin/bash

echo "Received command: $@"
echo "Navigating to /home/vscode/lavague-files"

cd /home/vscode/lavague-files || exit

echo "Current directory: $(pwd)"
echo "Executing command: $@"
eval "$@"