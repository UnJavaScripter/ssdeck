#!/bin/bash

# Based on the response from user Pujianto over https://superuser.com/questions/1675877/how-to-create-a-new-pipewire-virtual-device-that-to-combines-an-real-input-and-o

while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
        --input-device=*)
            # The first parameter is the input file
            NAME_OF_THE_INPUT_DEVICE="${key#*=}"
            shift # past argument
            ;;
        --output-device=*)
            # The second parameter is the output file
            NAME_OF_THE_OUTPUT_DEVICE="${key#*=}"
            shift # past argument
            ;;
    esac
done

PORT_MATCH_INPUT=$(pw-link -o | grep $NAME_OF_THE_INPUT_DEVICE)

if [[ $PORT_MATCH_INPUT == "" ]]; then
    echo ""
    echo " INPUT Port name \"$NAME_OF_THE_INPUT_DEVICE\" not found. To find your system's ports, use:"
    echo "  $ pw-link -o "
    echo ""
    exit 1;
fi

PORT_MATCH_OUTPUT=$(pw-link -i | grep $NAME_OF_THE_OUTPUT_DEVICE)

if [[ $PORT_MATCH_OUTPUT == "" ]]; then
    echo ""
    echo " OUTPUT Port name \"$NAME_OF_THE_OUTPUT_DEVICE\" not found. To find your system's ports, use:"
    echo "  $ pw-link -o "
    echo ""
    exit 1;
fi

# Search for the "soundbox" string and extract the module IDs
echo "Unloading any previous modules matching the string \"soundbox\"."
ids=$(pactl list modules | grep soundbox -B 2 | grep -Eo '^Module #[0-9]+' | cut -d'#' -f2)

# Loop over the IDs and unload each module
for id in $ids; do
  pactl unload-module $id
done

# Create combined sink
echo "Creating soundbox-combined-sink"
pactl load-module module-null-sink media.class=Audio/Sink sink_name=soundbox-combined-sink channel_map=stereo

# Link audio source (mic) to `combined sink`
## Get the capture device name with: `pw-link -o`
echo "Linking audio source physical device $NAME_OF_THE_INPUT_DEVICE -> soundbox-combined-sink"
pw-link $NAME_OF_THE_INPUT_DEVICE  soundbox-combined-sink:playback_FL
pw-link $NAME_OF_THE_INPUT_DEVICE  soundbox-combined-sink:playback_FR

# Create Virtual mic (The communication applications will use this one)
echo "Creating virtual microphone device soundbox-virtualmic"
pactl load-module module-null-sink media.class=Audio/Source/Virtual sink_name=soundbox-virtualmic channel_map=front-left,front-right

# Link sink and virtual mic
echo "Linking soundbox-combined-sink -> soundbox-virtualmic"
pw-link soundbox-combined-sink:monitor_FL soundbox-virtualmic:input_FL
pw-link soundbox-combined-sink:monitor_FR soundbox-virtualmic:input_FR

#### Monitor

echo "Creating a monitor sink"
pactl load-module module-null-sink media.class=Audio/Sink sink_name=soundbox-monitor-sink channel_map=stereo

echo "Linking monitor sink -> output device"
pw-link soundbox-monitor-sink:monitor_FL $NAME_OF_THE_OUTPUT_DEVICE
pw-link soundbox-monitor-sink:monitor_FR $NAME_OF_THE_OUTPUT_DEVICE

echo "Linking soundbox-monitor-sink -> soundbox-combined-sink"
pw-link soundbox-monitor-sink:monitor_FL soundbox-virtualmic:input_FL
pw-link soundbox-monitor-sink:monitor_FR soundbox-virtualmic:input_FR

# Send sound to soundbox device
# pw-play $PATH_TO_SOUND_FILE --volume 0.5 --target soundbox-device-sink

echo "..."
echo " Virtual microphone device successfully created with the name \"soundbox-virtualmic\" over the sink oundbox-device-sink."
echo " To play a sound file over the virtual microphone, run:"
echo ""
echo "  pw-play \$PATH_TO_SOUND_FILE --volume 0.5 --target soundbox-device-sink"
echo ""

exit 0