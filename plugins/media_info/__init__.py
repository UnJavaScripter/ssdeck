import os
import subprocess

MIC_STATUS = 0

def Get_playback_status():
    script_path = os.path.join(os.path.dirname(__file__), "media_info.sh")
    playback_status = subprocess.check_output(f"sh {script_path} PlaybackStatus", shell=True, text=True)
    return playback_status

def Get_mic_status():
    script_path = os.path.join(os.path.dirname(__file__), "mic_status.sh")
    mute_status = subprocess.check_output(f"sh {script_path}", shell=True, text=True)
    if len(mute_status) > 1:
        __Set_last_mic_status_read(1)
        return 1
    else:
        __Set_last_mic_status_read(0)
        return 0

def __Set_last_mic_status_read(status=0):
    global MIC_STATUS
    MIC_STATUS = status

def Get_mic_status_label():
    if MIC_STATUS:
        return "Muted"
    else:
        return ""
