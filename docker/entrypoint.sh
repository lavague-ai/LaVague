#!/usr/bin/bash
sudo chmod o+w /home/vscode/lavague-files
cd /home/vscode/lavague-files || exit

case $1 in
  launch)
    echo "Launching..."
    # Execute the launch command
    command="lavague -i instructions.txt -c config.py launch"
    ;;
  build)
    echo "Building..."
    # Execute the build command
    command="lavague -i instructions.txt -c config.py build"
    ;;
  *)
    echo "Executing custom command {$@}"
    # Execute the command as it is
    command="$@"
    ;;
esac

# Execute the command
eval "$command"