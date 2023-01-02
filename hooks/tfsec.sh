#!/usr/bin/env bash

set -e

# OSX GUI apps do not pick up environment variables the same way as Terminal apps and there are no easy solutions,
# especially as Apple changes the GUI app behavior every release (see https://stackoverflow.com/q/135688/483528). As a
# workaround to allow GitHub Desktop to work, add this (hopefully harmless) setting here.
export PATH=$PATH:/usr/local/bin

# echo "======== FILES:"
directories=()
for file in "$@"; do
  echo "file: $file"
  if [ -d "$file" ]; then
    directories+=("$file")
  else
    directories+=("$(dirname "$file")")
  fi
  echo "directories: ${directories[*]}"
done

unique_directories=$(printf "%s\n" "${directories[@]}" | sort -u)
unique_directories=($unique_directories)
echo "$unique_directories"

echo "========= START SCAN ==========="

for d in "${unique_directories[@]}"; do
  echo "RUN tfsec on: $d"
  if [ "$d" = "." ]; then
    echo "SKIP $d"
    continue
  fi
  tfsec "$d"
done
