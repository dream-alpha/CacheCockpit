#!/bin/bash

directory_path="$1"

# Check if the directory exists
if [ -d "$directory_path" ]; then
    # Change to the directory
    cd "$directory_path" || exit

    # Check if the directory is empty or contains only a file named ".sort"
    if [ "$(ls -A | grep -E -c '^\.sort$')" -eq 1 ] || [ "$(ls -A | wc -l)" -eq 0 ]; then
        # Delete the directory
        cd ..
        rm -r "$directory_path"
        echo "Directory deleted successfully."
    else
        echo "Directory contains other files besides .sort."
    fi
else
    echo "Directory does not exist."
fi
