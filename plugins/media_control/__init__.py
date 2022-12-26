import os

def Control(context):
    action = context.get('media_action', '')
    script_path = os.path.join(os.path.dirname(__file__), "media_control.sh")
    os.system(f"sh '{script_path}' '{action}'")
