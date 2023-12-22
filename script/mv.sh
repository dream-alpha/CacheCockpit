#!/bin/bash

# Source directory
source_dir="$1"

# Destination directory
destination_dir="$2"

# Create destination directory if it doesn't exist
mkdir -p "$destination_dir"

# Move files and links with find while preserving sub-tree structure
find "$source_dir" -type f -exec bash -c '
    dest_subdir="$2/$(dirname "${1#$3}")"
    mkdir -p "$dest_subdir" && mv "$1" "$dest_subdir/"
' _ {} "$destination_dir" "$source_dir" \;

# Delete source directory
rm -rf "$source_dir"
