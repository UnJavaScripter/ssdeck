#!/bin/bash

MODULE_NAME_MATCHER="soundbox"

if [ $# -eq 0 ]; then
    # If no argument was provided, output the original string
    echo "No module name provided. Using the default: ""$MODULE_NAME_MATCHER"
fi

if [ "$1" == "." ]; then
  echo "Unloading all modules modules."
  ids=$(pactl list modules | grep -Eo '^Module #[0-9]+' | cut -d'#' -f2)
else
  echo "Unloading any previous modules matching the string $MODULE_NAME_MATCHER."
  ids=$(pactl list modules | grep soundbox -B 2 | grep -Eo '^Module #[0-9]+' | cut -d'#' -f2)
fi

if [ ${#ids} -gt 0 ]; then
  echo "Found ${#ids} modules..."
  # Loop over the IDs and unload each module
  for id in $ids; do
    echo " - Unloading module $id"
    pactl unload-module $id
  done
else
  echo "No modules match the pattern" "$MODULE_NAME_MATCHER"
fi
