import os

def Insert(action_context):
    text = action_context.get('text', '')

    os.system(f"xdotool type '{text}'")