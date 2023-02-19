#!/bin/bash

if [ $# -eq 0 ]; then
    echo "No query provided"
    exit 1
else
    dest=$(dbus-send --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames | grep "string" | awk '{print $2}' | grep "org.mpris.MediaPlayer2" | head -n 1 | sed 's/"//g')
    if [ -n "$dest" ]; then

        status=$(dbus-send --print-reply --dest=$dest /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Get string:org.mpris.MediaPlayer2.Player string:PlaybackStatus | grep "string" | awk '{print $3}')
        trackid=$(dbus-send --print-reply --dest=$dest /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Get string:org.mpris.MediaPlayer2.Player string:Metadata | grep -A 1 "mpris:trackid" | awk '{getline 1; print $4}' | sed 's/"//g')
        metadata=$(dbus-send --print-reply --dest=$dest /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Get string:org.mpris.MediaPlayer2.Player string:Metadata)

        if [ $1 = "PlaybackStatus" ]; then
            echo $status | sed -n 's/.*"\(.*\)".*/\1/p'
            exit 0
        else
            echo "Unrecognized query provided"
        fi
    else
        echo "Not_Playing"
        exit 0
    fi
fi

