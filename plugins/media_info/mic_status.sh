#!/bin/bash

CURRENT_SOURCE=$(pactl info | grep "Default Source" | cut -f3 -d" ")
status=$(pactl list sources | grep -A 10 $CURRENT_SOURCE | grep "Mute: yes")
echo $status