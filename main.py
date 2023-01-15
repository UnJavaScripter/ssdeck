# from tkinter import *
import os
import subprocess
import threading
import importlib
import time

import json
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

PLUGINS = dict()

KEYS_FILE_PATH = os.path.join(os.path.dirname(__file__), "./keys.json")
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")
CURRENT_PAGE_ID = 0
global KEY_DATA

ACTIVE_KEY_STATES = []

with open(KEYS_FILE_PATH, 'r') as f:
    KEY_DATA = json.load(f)

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
# Plugin handling

def plugin_get_attribute(name):
    action_name = name.replace('plugin:', '')
    action_components = action_name.split('.')
    plugin_module = PLUGINS[action_components[0]]
    method = plugin_module.__getattribute__(action_components[1])
    return method.__call__()

def plugin_call_action(name, context=None):
    action_name = name.replace('plugin:', '')
    action_components = action_name.split('.')
    plugin_module = PLUGINS[action_components[0]]
    method = plugin_module.__getattribute__(action_components[1])
    if context is None:
        method.__call__()
    else:
        method.__call__(context)

###

def set_key_states(deck, key_number, selected_key, pressed_state=0):
    # key_change_callback(deck, key, state=False)
    label_text = selected_key.get('label', '')
    icon = selected_key.get('icon', 'default.png')
    disabled_state = False
    state_modifiers = selected_key.get("state_modifiers")
    if state_modifiers is not None:
        if state_modifiers.get("label"):
            label_text = plugin_get_attribute(state_modifiers["label"]).replace("_", " ")
        if state_modifiers.get("icon"):
            modified_icon_name = plugin_get_attribute(state_modifiers["icon"]).strip()
            if len(modified_icon_name) > 0:
                icon = f'{modified_icon_name}.png'
        if state_modifiers.get("disabled_state"):
            disabled_state = not plugin_get_attribute(state_modifiers["disabled_state"])
        if state_modifiers.get("pressed"):
            pressed_state = plugin_get_attribute(state_modifiers["pressed"])
        
    ui_changes(deck, key_number, pressed_state, selected_key, disabled_state, icon, label_text)

def render_page(deck):
    while True:
        global CURRENT_PAGE_ID
        try:
            current_page_keys = KEY_DATA['pages'][CURRENT_PAGE_ID]

            if len(ACTIVE_KEY_STATES) <= CURRENT_PAGE_ID:
                ACTIVE_KEY_STATES.append([])

            ACTIVE_KEY_STATES[CURRENT_PAGE_ID] = []
            for key_number in range(len(current_page_keys)):
                ACTIVE_KEY_STATES[CURRENT_PAGE_ID].append(0)
                if current_page_keys[key_number]:
                    # key_change_callback(deck, key, state=False)
                    selected_key = current_page_keys[key_number]
                    set_key_states(deck, key_number, selected_key)
            time.sleep(0.5)
        except IndexError:
            pass
        continue

def run_init_actions(actions):
    for action in actions:
        name = action['name']
        context = action.get('context', None)
        plugin_call_action(name, context)

def action_run_command(action):
    return os.system(action)

def action_change_page(deck, page):
    deck.reset()
    global CURRENT_PAGE_ID
    if page == "next":
        if CURRENT_PAGE_ID == len(KEY_DATA['pages']) -1:
            CURRENT_PAGE_ID = 0
        else:
            CURRENT_PAGE_ID = CURRENT_PAGE_ID + 1

def initialize_plugins(plugins):
    for plugin in plugins:
        if plugin not in PLUGINS:
            PLUGINS[plugin] = importlib.import_module(f'plugins.{plugin}')

def perform_actions(deck, actions):
    for action in actions:
        if action['name'].startswith('plugin:'):
            context = action.get('context', None)
            plugin_call_action(action['name'], context)
            
        else:
            if action['name'] == 'run':
                action_run_command(action['context'])
            elif action['name'] == 'change_page':
                action_change_page(deck, "next")
            else:
                print(f"Unknown command {action['name']}")

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

def update_key_image(deck, key, label, icon='default.png', disabled_state=False):
    # Determine what icon and label to use on the generated key.
    key_style = get_key_style(icon)

    # Generate the custom key with the requested image and label.
    image = render_key_image(deck, key_style["icon"], key_style["font"], label, disabled_state)

    # Use a scoped-with on the deck to ensure we're the only thread using it
    # right now.
    with deck:
        # Update requested key with the generated image.
        deck.set_key_image(key, image)

def ui_changes(deck, key_number, pressed_state, selected_key, disabled_state=False, icon=None, label=None):
    global CURRENT_PAGE_ID
    
    try:
        is_toggle_key = selected_key.get('type', '') == 'toggle'
        
        if label:
            label_text = label
        else:
            label_text = selected_key.get('label', '')
        if icon:
            default_icon = icon
        else:
            default_icon = selected_key.get('icon', 'default.png')
        
        if pressed_state and is_toggle_key:
            if ACTIVE_KEY_STATES[CURRENT_PAGE_ID][key_number] == False:
                ACTIVE_KEY_STATES[CURRENT_PAGE_ID][key_number] = True
            else:
                ACTIVE_KEY_STATES[CURRENT_PAGE_ID][key_number] = False

        if ACTIVE_KEY_STATES[CURRENT_PAGE_ID][key_number]:
            if label == None:
                label = selected_key.get('label_pressed', label_text)
            if icon == None:
                icon = selected_key.get('icon_pressed', default_icon)
            update_key_image(deck, key_number, label, icon, disabled_state)
        else:
            if label == None:
                label = selected_key.get('label', label_text)
            if icon == None:
                icon = selected_key.get('icon', default_icon)
            update_key_image(deck, key_number, label, icon, disabled_state)
    except IndexError:
        pass

def key_change_callback(deck, key_number, pressed_state):
    global CURRENT_PAGE_ID
    try:
        current_page_keys = KEY_DATA['pages'][CURRENT_PAGE_ID]
        current_page_keys[key_number]
        current_page_keys[key_number]['actions']
    except:
        return

    selected_key = current_page_keys[key_number]
    is_toggle_key = selected_key.get('type', '') == 'toggle'


    set_key_states(deck, key_number, selected_key, pressed_state)
    # ui_changes(deck, key_number, pressed_state, selected_key)

    if pressed_state:
        if is_toggle_key:
            if ACTIVE_KEY_STATES[CURRENT_PAGE_ID][key_number] == False:
                perform_actions(deck, selected_key['actions_toggle'])
            else:
                perform_actions(deck, selected_key['actions'])
        else:
            perform_actions(deck, selected_key['actions'])
    # else:
        # capture release action

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
        
        deck.open()

        print("Opened '{}' device (serial number: '{}', fw: '{}')".format(
            deck.deck_type(), deck.get_serial_number(), deck.get_firmware_version()
        ))

        deck.set_brightness(30)
        
        if KEY_DATA["plugins"] != None:
            initialize_plugins(KEY_DATA["plugins"])
        
        if KEY_DATA["init"] != None:
            if KEY_DATA["init"]["actions"] != None:
                run_init_actions(KEY_DATA["init"]["actions"])

        deck.reset()
        thread = threading.Thread(target=render_page, args=(deck,))
        thread.start()
        
        # Register callback function for when a key state changes.
        deck.set_key_callback(key_change_callback)
    
        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed).
        for t in threading.enumerate():
            try:
                t.join()
            except RuntimeError:
                pass
