import os

def Add(action_context):
    text = action_context.get('text', '')

    os.system(f"echo '{text}' | xclip -sel clip")
