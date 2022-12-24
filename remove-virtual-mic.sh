#!/bin/bash

# Search for the "soundbox" string and extract the module IDs
echo "Unloading any previous modules matching the string \"soundbox\"."
ids=$(pactl list modules | grep soundbox -B 2 | grep -Eo '^Module #[0-9]+' | cut -d'#' -f2)

# Loop over the IDs and unload each module
for id in $ids; do
  echo "Unloading module $id"
  pactl unload-module $id
done