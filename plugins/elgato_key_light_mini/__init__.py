import requests

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
    try:
        lightInfo = Get_info()
        return lightInfo['lights'][0]['on']
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
    try:
        if Is_light_on():
            Turn_off()
        else:
            Set_state_temp_val(brightness, temperature, poweredOnState=True)
    except:
        return None
