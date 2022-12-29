import os
import subprocess

def Get_playback_status():
    script_path = os.path.join(os.path.dirname(__file__), "media_info.sh")
    playback_status = subprocess.check_output(f"sh {script_path} PlaybackStatus", shell=True, text=True)
    return playback_status
