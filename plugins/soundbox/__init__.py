import os
from audio_device_selector import AudioDeviceSelector

VIRTUAL_MIC_SETUP_SUCCESS = False

def Dummy_init_reqs():
    return True

def Setup_virtual_mic(input_device_name = None, output_device_name = None):
    global VIRTUAL_MIC_SETUP_SUCCESS
    lines = []
    if not input_device_name and not output_device_name:
        # Check if the input file exists
        if not os.path.exists('target_soundbox_audio_devices.txt'):
            print("Error: Input file 'target_soundbox_audio_devices.txt' does not exist")
            AudioDeviceSelector()

        with open('target_soundbox_audio_devices.txt', 'r') as input_file:
            # Read all the lines of the file into a list
            lines = input_file.readlines()

            # Check if the input file has at least two lines of text
        if len(lines) < 2:
            print("Error: Input file 'target_soundbox_audio_devices.txt' must have at least two lines. The first line defines the input device, and the second one, the output device")
            print("  -> Deleting inconsistent file")
            os.remove("target_soundbox_audio_devices.txt")
            VIRTUAL_MIC_SETUP_SUCCESS= False
            setup_virtual_mic()
            return
        else:
            # Set the variable "second_line" to the second line of the file
            input_device_name = lines[0].splitlines()[0]
            output_device_name = lines[1].splitlines()[0]
    print(f"\nAttempting to set audio devices: \n - input: {input_device_name} \n - output: {output_device_name}")
    script_path = os.path.join(os.path.dirname(__file__), "setup-virtual-mic.sh")
    if os.system(f"sh '{script_path}' --input-device={input_device_name} --output-device={output_device_name}") == 0:
        VIRTUAL_MIC_SETUP_SUCCESS= True
    else:
        VIRTUAL_MIC_SETUP_SUCCESS= False

def Get_Virtual_Mic_Setup_Sucess():
    global VIRTUAL_MIC_SETUP_SUCCESS
    return VIRTUAL_MIC_SETUP_SUCCESS

def Remove_virtual_mic():
    script_path = os.path.join(os.path.dirname(__file__), "setup-virtual-mic.sh")
    os.system(f"sh '{script_path}'")

def Play(action_context):
    file_path = action_context.get('file_path', '')
    # TODO: target device
    # output_device_exists = action_run("pw-link -lio | grep soundbox-monitor-sink")
    # if not VIRTUAL_MIC_SETUP_SUCCESS and not output_device_exists:
    if not VIRTUAL_MIC_SETUP_SUCCESS:
        Setup_virtual_mic()
    try:
        os.system(f"pw-play '{file_path}' --volume 0.2 --target soundbox-monitor-sink")
    except:
        os.system("notify-send error setting soundbox virtual microphone")
