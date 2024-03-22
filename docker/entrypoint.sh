#!/usr/bin/bash

# Execute your lavague-launch command
lavague-launch --file_path instructions.txt --config_path config.py

# Keep the container running
tail -f /dev/null