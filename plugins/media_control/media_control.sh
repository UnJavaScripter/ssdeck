#!/bin/bash

if [ "$*" == "" ]; then
    echo "No action provided"
    exit 1
    else
        dest=$(dbus-send --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames | grep "string" | awk '{print $2}' | grep "org.mpris.MediaPlayer2" | head -n 1 | sed 's/"//g')
        status=$(dbus-send --print-reply --dest=$dest /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Get string:org.mpris.MediaPlayer2.Player string:PlaybackStatus | grep "string" | awk '{print $3}')
        trackid=$(dbus-send --print-reply --dest=$dest /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Get string:org.mpris.MediaPlayer2.Player string:Metadata | grep -A 1 "mpris:trackid" | awk '{getline 1; print $4}' | sed 's/"//g')
        metadata=$(dbus-send --print-reply --dest=$dest /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Get string:org.mpris.MediaPlayer2.Player string:Metadata)

        # If no additional arguments are passed, execute the action
        if [[ $2 == "" ]]; then
            dbus-send --print-reply --dest=$dest /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.$1
        fi
        if [[ $1 == "Seek" && $2 != "" ]]; then
            seek="int64:$2"
            dbus-send --print-reply --dest=$dest /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.$1 $seek
        fi
fi

