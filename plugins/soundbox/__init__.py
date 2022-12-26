import os

def Play(action_context):
    file_path = action_context.get('file_path', '')
    # TODO: target device
    # output_device_exists = action_run("pw-link -lio | grep soundbox-monitor-sink")
    # if not VIRTUAL_MIC_SETUP_SUCCESS and not output_device_exists:
    # if not VIRTUAL_MIC_SETUP_SUCCESS:
    #     setup_virtual_mic()
    # try:
    os.system(f"pw-play '{file_path}' --volume 0.2 --target soundbox-monitor-sink")
    # except:
    #     action_run("notify-send error setting soundbox virtual microphone")
