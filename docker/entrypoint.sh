#!/usr/bin/bash
chown -R 1000:1000 /home/vscode/lavague-files
cd /home/vscode/lavague-files || exit

case $1 in
  launch)
    echo "Launching..."
    # Execute the launch command
    command="lavague-launch --file_path hf.txt --config_path openai.py"
    ;;
  build)
    echo "Building..."
    # Execute the build command
    command="lavague-build --file_path hf.txt --config_path openai.py"
    ;;
  *)
    echo "Executing custom command {$@}"
    # Execute the command as it is
    command="$@"
    ;;
esac

# Execute the command
eval "$command"