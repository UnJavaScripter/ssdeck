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

PORT_MATCH_INPUT=$(pw-link -o | grep "$NAME_OF_THE_INPUT_DEVICE")

if [[ $PORT_MATCH_INPUT == "" ]]; then
    echo ""
    echo " Error: INPUT Port name \"$NAME_OF_THE_INPUT_DEVICE\" not found. To find your system's ports, use:"
    echo "  $ pw-link -o "
    echo ""
    exit 1;
fi

PORT_MATCH_OUTPUT=$(pw-link -i | grep "$NAME_OF_THE_OUTPUT_DEVICE")

if [[ $PORT_MATCH_OUTPUT == "" ]]; then
    echo ""
    echo " Error: OUTPUT Port name \"$NAME_OF_THE_OUTPUT_DEVICE\" not found. To find your system's ports, use:"
    echo "  $ pw-link -o "
    echo ""
    exit 1;
fi

# Search for the "soundbox" string and extract the module IDs
echo "Unloading any previous modules matching the string \"soundbox\"."
ids=$(pactl list modules | grep soundbox -B 2 | grep -Eo '^Module #[0-9]+' | cut -d'#' -f2)

# Loop over the IDs and unload each module
for id in $ids; do
  pactl unload-module "$id"
done

sleep 2 &&

function link_devices() {
    pw-link $1 $2
}

function remove_channel_from_name() {
  echo "$1" | sed -E 's/(.*)_.*/\1/'
}

function get_device_name() {
    input_device_name="$1"
    channel="$2"
    device_name_without_channel=$(remove_channel_from_name "$input_device_name")


    if [[ "$input_device_name" == *"MONO"* ]]; then
        echo "$device_name_without_channel""_MONO"
    else
        echo "$device_name_without_channel""_""$channel"
    fi
}

INPUT_L=$(get_device_name "$NAME_OF_THE_INPUT_DEVICE" "FL")
INPUT_R=$(get_device_name "$NAME_OF_THE_INPUT_DEVICE" "FR")

OUTPUT_L=$(get_device_name "$NAME_OF_THE_OUTPUT_DEVICE" "FL")
OUTPUT_R=$(get_device_name "$NAME_OF_THE_OUTPUT_DEVICE" "FR")



# Create Virtual mic (The communication applications will use this one)
echo "Creating virtual microphone device soundbox-virtualmic"
pactl load-module module-null-sink media.class=Audio/Source/Virtual sink_name=soundbox-virtualmic channel_map=front-left,front-right rate=48000 channels=2 format=s16le

# Create combined sink
echo "Creating soundbox-combine-sink"
pactl load-module module-null-sink media.class=Audio/Sink sink_name=soundbox-combine-sink channel_map=stereo rate=48000 channels=2 format=s16le

# Create Monitor sink
echo "Creating a monitor sink"
pactl load-module module-null-sink media.class=Audio/Sink sink_name=soundbox-monitor-sink channel_map=stereo rate=48000 channels=2 format=s16le

sleep 3 &&

# Link audio source (mic) to `combine sink`
## Get the capture device name with: `pw-link -o`
echo "Linking audio source physical "$NAME_OF_THE_INPUT_DEVICE" > soundbox-combine-sink:playback_FL"
echo "|>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
link_devices "$INPUT_L" soundbox-combine-sink:playback_FL
link_devices "$INPUT_R" soundbox-combine-sink:playback_FR
echo "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<|"

echo "Linking monitor sink -> output device "$NAME_OF_THE_OUTPUT_DEVICE" "
echo "|>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
link_devices soundbox-monitor-sink:monitor_FL "$OUTPUT_L"
link_devices soundbox-monitor-sink:monitor_FR "$OUTPUT_R"
echo "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<|"

echo "Linking soundbox-monitor-sink -> soundbox-combine-sink"
echo "|>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
link_devices soundbox-monitor-sink:monitor_FL soundbox-combine-sink:playback_FL
link_devices soundbox-monitor-sink:monitor_FR soundbox-combine-sink:playback_FR
echo "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<|"

# Link sink and virtual mic
echo "Linking soundbox-combine-sink -> soundbox-virtualmic"
echo "|>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
link_devices soundbox-combine-sink:monitor_FL soundbox-virtualmic:input_FL
link_devices soundbox-combine-sink:monitor_FR soundbox-virtualmic:input_FR
echo "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<|"

# Send sound to soundbox device
# pw-play $PATH_TO_SOUND_FILE --volume 0.5 --target soundbox-monitor-sink

echo "..."
echo " Virtual microphone device successfully created with the name \"/soundbox-virtualmic\" over the sink oundbox-device-sink."
echo " To play a sound file over the virtual microphone, run:"
echo ""
echo "  pw-play \$PATH_TO_SOUND_FILE --volume 0.5 --target soundbox-monitor-sink"
echo ""

exit 0