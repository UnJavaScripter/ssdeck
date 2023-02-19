import os
import subprocess

def Notify(action_context):
    category = action_context.get('category', '')
    message = action_context.get('message', '')
    try:
        subprocess.check_output(f"notify-send -c {category} {message}", shell=True, text=True)
    except:
        script_path = os.path.join(os.path.dirname(__file__), "notify_dbus.sh")
        notification = subprocess.check_output(f"sh {script_path} {message}", shell=True, text=True)
        return notification
        