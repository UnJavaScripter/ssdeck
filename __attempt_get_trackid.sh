#!/bin/bash

printf '%s\n ---'
dbus-send --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames | grep "string" | awk '{print $2}' | grep "org.mpris.MediaPlayer2" | sed 's/"//g' | while read -r dest
do
    printf '%s\n'
    printf '%s\n' "$dest"

    interface=org.mpris.MediaPlayer2.Player

    # Check if the GetMetadata method exists
    result=$(dbus-send --print-reply --dest=$dest /org/mpris/MediaPlayer2 $interface.Introspect | grep "GetMetadata")

    # If the GetMetadata method exists, get the metadata for the currently playing track
    if [ -n "$result" ]; then
        track=$(dbus-send --print-reply --dest=$dest /org/mpris/MediaPlayer2 $interface.GetMetadata)

        # Extract the track ID from the metadata
        trackid=$(echo $track | grep "mpris:trackid" | awk '{print $3}' | sed 's/"//g')

    # If the GetMetadata method does not exist, use an alternative method to get the track ID
    else
    # TODO: Add code here to get the track ID using an alternative method
        trackid=$(dbus-send --print-reply --dest=$dest /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Get string:org.mpris.MediaPlayer2.Player string:Metadata | grep -A 1 "mpris:trackid" | awk '{getline 1; print $4}' | sed 's/"//g')
    fi

    # Print the track ID
    printf " -> Track ID: $trackid"
    printf '%s\n'
done
printf '%s\n'