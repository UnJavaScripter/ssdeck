# from tkinter import *
import os
import subprocess
import threading
import importlib

import json
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

PLUGINS = dict()

ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")
CURRENT_PAGE_ID = 0
global KEY_DATA

KEY_STATES = []

with open('keys.json', 'r') as f:
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

def render_page(deck, page_id):
    global CURRENT_PAGE_ID
    CURRENT_PAGE_ID = page_id
    
    current_page_keys = KEY_DATA['pages'][CURRENT_PAGE_ID]

    if len(KEY_STATES) <= CURRENT_PAGE_ID:
        KEY_STATES.append([])

    deck.reset()

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

def run_init_actions(actions):
    for action in actions:
        name = action['name']
        context = action.get('context', None)
        plugin_call_action(name, context)

def action_run_command(action):
    return os.system(action)

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
            context = action.get('context', None)
            plugin_call_action(action['name'], context)
            
        else:
            if action['name'] == 'run':
                action_run_command(action['context'])
            elif action['name'] == 'change_page':
                action_change_page(deck, action['context'])
            else:
                print(f"Unknown command {action['name']}")

def check_key_meets_deps(deps):
    dep_status = []
    for dep in deps:
        dep_status.append(plugin_get_attribute(dep))
    return all(dep_status)


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
        is_disabled = False if check_key_meets_deps(deps) else True
    
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
        deps = selected_key.get('deps', None)
        update_key_image(deck, key, label, icon, deps)

        if KEY_STATES[CURRENT_PAGE_ID][key] == 0 and is_toggle_key:
            perform_actions(deck, selected_key['actions_toggle'])
    else:
        if KEY_STATES[CURRENT_PAGE_ID][key] == 1:
            perform_actions(deck, selected_key['actions'])
            # Return and don't change the UI
            return
        else:
            label = selected_key.get('label', label_text)
            icon = selected_key.get('icon', default_icon)
            deps = selected_key.get('deps', None)
            
            # update_key_image needs to happen before perform_actions in order to avoid updating keys afterwards.
            update_key_image(deck, key, label, icon, deps)
            perform_actions(deck, selected_key['actions'])
            



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

        render_page(deck, 0)
        
        # Register callback function for when a key state changes.
        deck.set_key_callback(key_change_callback)
    
        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed).
        for t in threading.enumerate():
            try:
                t.join()
            except RuntimeError:
                pass
