import requests
import time

retries = 3
last_response = None
last_response_time = 0

def round_value(x, base=5):
    return base * round(x/base)
    
def round_temp_value(temp_val):
    val = round_value(temp_val)
    if val > 344:
        val = 344
    elif val < 143:
        val = 143
    return val

url = 'http://10.11.88.201:9123/elgato'
headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}


def Get_info():
    try:
        response = requests.get(f'{url}/lights', headers=headers, timeout=0.1)
        return response.json()
    except:
        return None

def Turn_off():
    try:
        data = { "lights": [{ "on": 0 }] }
        requests.put(f'{url}/lights', headers=headers, json=data, timeout=0.1)
    except:
        return None


def Turn_on():
    try:
        data = { "lights": [{ "on": 1 }] }
        requests.put(f'{url}/lights', headers=headers, json=data, timeout=0.1)
    except:
        return None

def Set_state_temp_kelvin(brightness=10, temperature = 344, poweredOnState=None):
    try:
        if poweredOnState is not None:
            data = { "numberOfLights": 1, "lights": [ { "on": poweredOnState, "brightness": brightness, "temperature": round_temp_value(temperature) } ] }
        else :
            data = { "numberOfLights": 1, "lights": [ { "brightness": brightness, "temperature": round_temp_value(temperature) } ] }
        requests.put(f'{url}/lights', headers=headers, json=data, timeout=0.1)
    except:
        return None
    

def Set_state_temp_val(brightness=10, temperature = 344, poweredOnState=None):
    print(f'> Elgato key light mini: brightness: {brightness}, temperature: {temperature}, poweredOnState: {poweredOnState}')
    try:
        if poweredOnState is not None:
            data = { "numberOfLights": 1, "lights": [ { "on": poweredOnState, "brightness": brightness, "temperature": round_temp_value(1000000/temperature) } ] }
        else :
            data = { "numberOfLights": 1, "lights": [ { "brightness": brightness, "temperature": round_temp_value(1000000/temperature) } ] }
        requests.put(f'{url}/lights', headers=headers, json=data, timeout=0.1)
    except:
        return None
    

def Is_light_on():
    global last_response
    global last_response_time
    if last_response and last_response_time:
        return last_response['lights'][0]['on']
    else:
        try:
            last_response = Get_info()
            last_response_time = time.time()
            return last_response['lights'][0]['on']
        except:
            return 0


def Key_icon_name():
    try:
        if Is_light_on():
            return "flashlight_on"
        else:
            return "flashlight_off"
    except:
        return "flashlight_on"

def Toggle_lights(brightness, temperature=344):
    global last_response
    global last_response_time
    try:
        if Is_light_on():
            Turn_off()
        else:
            Set_state_temp_val(brightness, temperature, poweredOnState=True)

        last_response = Get_info()
        last_response_time = time.time()
    except:
        return None

def Set_brightness_up(temperature=344):
    global last_response
    global last_response_time
    try:
        light_info = Get_info()
        current_light_info = light_info.get("lights")[0]
        current_brightness = current_light_info.get("brightness")
        if current_brightness < 100:
            Set_state_temp_val(current_brightness + 10, temperature)
            last_response = Get_info()
            print(f"up: {last_response}")
            last_response_time = time.time()
            return current_light_info
        else:
            last_response = light_info
            last_response_time = time.time()
            return current_light_info
    except:
            return None
def Set_brightness_down(temperature=344):
    global last_response
    global last_response_time
    try:
        light_info = Get_info()
        current_light_info = light_info.get("lights")[0]
        current_brightness = current_light_info.get("brightness")
        if current_brightness > 10:
            Set_state_temp_val(current_brightness - 10, temperature)
            last_response = Get_info()
            print(f"down: {last_response}")
            last_response_time = time.time()
            return current_light_info
        else:
            last_response = light_info
            last_response_time = time.time()
            return current_light_info
    except:
        return None