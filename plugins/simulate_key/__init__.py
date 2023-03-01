import os

def KeyPress(action_context):
    key = action_context.get('key', '')
    print(f'sending key {key}')
    os.system(f"xdotool key '{key}'")