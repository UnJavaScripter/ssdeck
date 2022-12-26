# from tkinter import *
import os
import subprocess
import threading
import importlib

import json
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

from audio_device_selector import AudioDeviceSelector

PLUGINS = dict()

ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")
CURRENT_PAGE_ID = 0
global KEY_DATA

KEY_STATES = []
VIRTUAL_MIC_SETUP_SUCCESS = False

with open('keys.json', 'r') as f:
    KEY_DATA = json.load(f)

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


def render_page(deck, page_id):
    global CURRENT_PAGE_ID
    CURRENT_PAGE_ID = page_id
    
    current_page_keys = KEY_DATA['pages'][CURRENT_PAGE_ID]

    if len(KEY_STATES) <= CURRENT_PAGE_ID:
        KEY_STATES.append([])

    deck.reset()

    # for key in range(deck.key_count()):
    #     deck.set_key_image(key, None)
    
    KEY_STATES[CURRENT_PAGE_ID] = []
    for key in range(len(current_page_keys)):
        KEY_STATES[CURRENT_PAGE_ID].append(0)
        if current_page_keys[key]:
            # key_change_callback(deck, key, state=False)
            selected_key = current_page_keys[key]
            label_text = selected_key.get('label', '')
            icon = selected_key.get('icon', 'default.png')
            deps = selected_key.get('deps', None)
            update_key_image(deck, key, label_text, icon, deps)

def action_run(action):
    return os.system(action)

def action_soundbox_play(file_path):
    # TODO: target device
    # output_device_exists = action_run("pw-link -lio | grep soundbox-monitor-sink")
    # if not VIRTUAL_MIC_SETUP_SUCCESS and not output_device_exists:
    if not VIRTUAL_MIC_SETUP_SUCCESS:
        setup_virtual_mic()
    try:
        action_run(f"pw-play '{file_path}' --volume 0.2 --target soundbox-monitor-sink")
    except:
        action_run("notify-send error setting soundbox virtual microphone")

def action_change_page(deck, page):
    global CURRENT_PAGE_ID
   
    if page == "next":
        if CURRENT_PAGE_ID == len(KEY_DATA['pages']) -1:
            render_page(deck, 0)
        else:
            render_page(deck, CURRENT_PAGE_ID + 1)

def initialize_plugins(plugins):
    for plugin in plugins:
        if plugin not in PLUGINS:
            PLUGINS[plugin] = importlib.import_module(f'plugins.{plugin}')

def perform_actions(deck, actions):
    for action in actions:
        if action['name'].startswith('plugin:'):
            action_name = action['name'].replace('plugin:', '')
            action_components = action_name.split('.')
            plugin_module = PLUGINS[action_components[0]]
            method = plugin_module.__getattribute__(action_components[1])
            method.__call__(action["context"])
            
        else:
            if action['name'] == 'run':
                action_run(action['context'])
            elif action['name'] == 'soundbox_play':
                action_soundbox_play(action['context'])
            elif action['name'] == 'change_page':
                action_change_page(deck, action['context'])
            else:
                print(f"Unknown command {action['name']}")

def setup_virtual_mic(input_device_name = None, output_device_name = None):
    global VIRTUAL_MIC_SETUP_SUCCESS
    lines = []
    if not input_device_name and not output_device_name:
        # Check if the input file exists
        if not os.path.exists('target_soundbox_audio_devices.txt'):
            print("Error: Input file 'target_soundbox_audio_devices.txt' does not exist")
            AudioDeviceSelector()

        with open('target_soundbox_audio_devices.txt', 'r') as input_file:
            # Read all the lines of the file into a list
            lines = input_file.readlines()

            # Check if the input file has at least two lines of text
        if len(lines) < 2:
            print("Error: Input file 'target_soundbox_audio_devices.txt' must have at least two lines. The first line defines the input device, and the second one, the output device")
            print("  -> Deleting inconsistent file")
            os.remove("target_soundbox_audio_devices.txt")
            VIRTUAL_MIC_SETUP_SUCCESS= False
            setup_virtual_mic()
            return
        else:
            # Set the variable "second_line" to the second line of the file
            input_device_name = lines[0].splitlines()[0]
            output_device_name = lines[1].splitlines()[0]
    print(f"\nAttempting to set audio devices: \n - input: {input_device_name} \n - output: {output_device_name}")
    if action_run(f"sh setup-virtual-mic.sh --input-device={input_device_name} --output-device={output_device_name}") == 0:
        VIRTUAL_MIC_SETUP_SUCCESS= True
    else:
        VIRTUAL_MIC_SETUP_SUCCESS= False


def check_meets_deps(deps):
    for dep in deps:
        if dep == "soundbox":
            return True if VIRTUAL_MIC_SETUP_SUCCESS else False


def render_key_image(deck, icon_filename, font_filename, label_text, is_disabled=False):
    if is_disabled:
        icon = Image.open(icon_filename).convert('LA')
    else:
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

def update_key_image(deck, key, label='Key', icon='default.png', deps=None):
    is_disabled = False
    if deps:
        is_disabled = False if check_meets_deps(deps) else True
    
    # Determine what icon and label to use on the generated key.
    key_style = get_key_style(icon)

    # Generate the custom key with the requested image and label.
    image = render_key_image(deck, key_style["icon"], key_style["font"], label, is_disabled)

    # Use a scoped-with on the deck to ensure we're the only thread using it
    # right now.
    with deck:
        # Update requested key with the generated image.
        deck.set_key_image(key, image)


def key_change_callback(deck, key, pressed_state):
    try:
        current_page_keys = KEY_DATA['pages'][CURRENT_PAGE_ID]
        current_page_keys[key]
        current_page_keys[key]['actions']
    except:
        return

    selected_key = current_page_keys[key]
    is_toggle_key = selected_key.get('type', '') == 'toggle'
    label_text = selected_key.get('label', '')
    default_icon = selected_key.get('icon', 'default.png')

    if pressed_state and is_toggle_key:
        if KEY_STATES[CURRENT_PAGE_ID][key] == 0:
            KEY_STATES[CURRENT_PAGE_ID][key] = 1
        else:
            KEY_STATES[CURRENT_PAGE_ID][key] = 0

    if pressed_state:
        label = selected_key.get('label_pressed', label_text)
        icon = selected_key.get('icon_pressed', default_icon)
        deps = selected_key.get('deps', [])
        update_key_image(deck, key, label, icon, deps)

        if KEY_STATES[CURRENT_PAGE_ID][key] == 0 and is_toggle_key:
            perform_actions(deck, selected_key['actions_release'])
    else:
        if KEY_STATES[CURRENT_PAGE_ID][key] == 1:
            perform_actions(deck, selected_key['actions'])
            # Return and don't change the UI
            return
        else:
            label = selected_key.get('label', label_text)
            icon = selected_key.get('icon', default_icon)
            deps = selected_key.get('deps', [])
            perform_actions(deck, selected_key['actions'])
            update_key_image(deck, key, label, icon, deps)
            



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

        print("Opened '{}' device (serial number: '{}', fw: '{}')".format(
            deck.deck_type(), deck.get_serial_number(), deck.get_firmware_version()
        ))

        deck.set_brightness(30)
        
        if KEY_DATA["plugins"] != None:
            initialize_plugins(KEY_DATA["plugins"])

        # setup_virtual_mic()
    
        render_page(deck, 0)
        
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
