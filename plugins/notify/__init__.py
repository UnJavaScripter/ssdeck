import os

def Notify(action_context):
    category = action_context.get('category', '')
    message = action_context.get('message', '')

    os.system(f"notify-send -c {category} {message}")