# from tkinter import *
import os
import subprocess
import threading

import json
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")
CURRENT_PAGE_ID = 0
with open('keys.json', 'r') as f:
    KEY_DATA = json.load(f)
    CURRENT_PAGE_KEYS = KEY_DATA['pages'][CURRENT_PAGE_ID]
KEY_STATES = []
VIRTUAL_MIC_SETUP_SUCCESS = False

# window = Tk()


# window.title("Stream Deck Controller")
# window.geometry("500x500")
try:
    streamdecks = DeviceManager().enumerate()
except:
    print("Is hidapi / hidapi-devel installed on your system?")

def check_requirements():
    print("\n")
    try:
        print("xclip found at:")
        subprocess.call(["which", "xclip"])
    except FileNotFoundError:
        print("Missing dependencies:")
        print(" -> Please install xclip on your system.")
        print("\n")
        exit(1)
    try:
        print("xdotool found at:")
        subprocess.call(["which", "xdotool"])
    except FileNotFoundError:
        print("Missing dependencies:")
        print(" -> Please install xdotool on your system.")
        print("\n")
        exit(1)

check_requirements()

###

def action_run(action):
    os.system(action)

def action_media_control(action):
    action_run(f"sh ./media_control.sh '{action}'")

def action_insert_text(text):
    action_run(f"xdotool type '{text}'")

def action_add_to_clipboard(text):
    action_run(f"echo '{text}' | xclip -sel clip")

def action_soundbox_play(file_path):
    # TODO: target device
    output_device_exists = action_run("pw-link -lio | grep soundbox-monitor-sink")
    if not VIRTUAL_MIC_SETUP_SUCCESS and not output_device_exists:
        setup_virtual_mic()
    try:
        action_run(f"pw-play '{file_path}' --volume 0.2 --target soundbox-monitor-sink")
    except:
        action_run("notify-send error setting soundbox virtual microphone")

def perform_actions(actions):
    for action in actions:
        match action["name"]:
            case "run":
                action_run(action["context"])
            case "media_control":
                action_media_control(action["context"])
            case "insert_text":
                action_insert_text(action["context"])
            case "add_to_clipboard":
                action_add_to_clipboard(action["context"])
            case "soundbox_play":
                action_soundbox_play(action["context"])
            case unknown_command:
                print(f"Unknown command '{unknown_command}'")

def setup_virtual_mic():
    try:
        action_run('sh setup-virtual-mic.sh bluez_input.60_AB_D2_3C_9B_11.0:capture_MONO bluez_output.60_AB_D2_3C_9B_11.1:playback_MONO')
        VIRTUAL_MIC_SETUP_SUCCESS= True
    except:
        VIRTUAL_MIC_SETUP_SUCCESS= False



def render_key_image(deck, icon_filename, font_filename, label_text):
    icon = Image.open(icon_filename)
    # Resize the source image asset to best-fit the dimensions of a single key.
    # A margin at the bottom is applied when a label is specified.
    image = PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 20 if label_text else 0, 0])

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # label onto the image a few pixels from the bottom of the key.
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_filename, 14)
    if label_text:
        draw.text((image.width / 2, image.height - 5), text=label_text, font=font, anchor="ms", fill="white")

    return PILHelper.to_native_format(deck, image)

# Returns styling information for a key based on its position and state.
def get_key_style(icon='default.png'):
    return {
        "icon": os.path.join(ASSETS_PATH, "icons", "{}".format(icon)),
        "font": os.path.join(ASSETS_PATH, "fonts", "Roboto-Regular.ttf"),
    }

def update_key_image(deck, key, label='Key', icon='default.png'):
    # Determine what icon and label to use on the generated key.
    key_style = get_key_style(icon)

    # Generate the custom key with the requested image and label.
    image = render_key_image(deck, key_style["icon"], key_style["font"], label)

    # Use a scoped-with on the deck to ensure we're the only thread using it
    # right now.
    with deck:
        # Update requested key with the generated image.
        deck.set_key_image(key, image)


def key_change_callback(deck, key, pressed_state):
    selected_key = CURRENT_PAGE_KEYS[key]
    is_toggle_key = selected_key.get('type', '') == 'toggle'
    label_text = selected_key.get('label', '')
    default_icon = selected_key.get('icon', 'default.png')

    if pressed_state and is_toggle_key:
        if KEY_STATES[CURRENT_PAGE_ID][key] == 0:
            KEY_STATES[CURRENT_PAGE_ID][key] = 1
        else:
            KEY_STATES[CURRENT_PAGE_ID][key] = 0

    if pressed_state:
        if KEY_STATES[CURRENT_PAGE_ID][key] == 0 and is_toggle_key:
            perform_actions(selected_key['actions_release'])
        else:
            perform_actions(selected_key['actions'])
        label = selected_key.get('label_pressed', label_text)
        icon = selected_key.get('icon_pressed', default_icon)
    else:
        if KEY_STATES[CURRENT_PAGE_ID][key] == 1:
            perform_actions(selected_key['actions'])
            # Return and don't change the UI
            return
        else:
            label = selected_key.get('label', label_text)
            icon = selected_key.get('icon', default_icon)

    update_key_image(deck, key, label, icon)



def exit_and_clear(deck):
    with deck:
        # Reset deck, clearing all button images.
        deck.reset()

        # Close deck handle, terminating internal worker threads.
        deck.close()

if __name__ == "__main__":
    if len(streamdecks) == 0:
        print("No stream deck detected!")
    else:
        print("Found {} Stream Deck(s).\n".format(len(streamdecks)))
        deck = streamdecks[0]
        
        if not deck.is_visual():
            print("Something :/ ????????????????????")

        deck.open()
        deck.reset()
        
        print("Opened '{}' device (serial number: '{}', fw: '{}')".format(
            deck.deck_type(), deck.get_serial_number(), deck.get_firmware_version()
        ))

        deck.set_brightness(30)
        
        setup_virtual_mic()
    
        if len(KEY_STATES) <= CURRENT_PAGE_ID:
            KEY_STATES.append([])

        for key in range(len(CURRENT_PAGE_KEYS)):
            KEY_STATES[CURRENT_PAGE_ID].append(0)
            if CURRENT_PAGE_KEYS[key]:
                # key_change_callback(deck, key, state=False)
                selected_key = CURRENT_PAGE_KEYS[key]
                label_text = selected_key.get('label', '')
                icon = selected_key.get('icon', 'default.png')
                update_key_image(deck, key, label_text, icon)
        
        # Register callback function for when a key state changes.
        deck.set_key_callback(key_change_callback)


        # def button_press(key_num, image_path):
        # # Set the image of the key on the stream deck
        #     print('press')
        #     update_key_image(deck, 1, 'pressed!!')
        # button1 = Button(window, text="Button 1", command=lambda: button_press(1, "1.png"))
        # button1.pack()

        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed).
        for t in threading.enumerate():
            try:
                t.join()
            except RuntimeError:
                pass
                # window.mainloop()






##
