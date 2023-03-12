#!/bin/bash
#                                                                                                                                                ... "App Name" "ID" "Icon" "Title" "Message"
echo "Sending notification: $1"
gdbus call --session --dest org.freedesktop.Notifications --object-path /org/freedesktop/Notifications --method org.freedesktop.Notifications.Notify "SSDeck" "0" "" "SSDeck" "$1" [] {} 1000 | awk -F ' ' '{print $2}' | tr -d ',()'
