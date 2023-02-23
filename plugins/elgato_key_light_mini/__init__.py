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


def GetInfo():
    response = requests.get(f'{url}/lights', headers=headers)
    return response.json()

def TurnOff():
    data = { "lights": [{ "on": 0 }] }
    requests.put(f'{url}/lights', headers=headers, json=data)


def TurnOn():
    data = { "lights": [{ "on": 1 }] }
    requests.put(f'{url}/lights', headers=headers, json=data)

def Set_state_temp_kelvin(brightness=10, temperature = 344, poweredOnState=None):
    # data = { "numberOfLights": 1, "lights": [ { "temperature": 500 } ] }
    if poweredOnState is not None:
        data = { "numberOfLights": 1, "lights": [ { "on": poweredOnState, "brightness": brightness, "temperature": round_temp_value(temperature) } ] }
    else :
        data = { "numberOfLights": 1, "lights": [ { "brightness": brightness, "temperature": round_temp_value(temperature) } ] }
    
    requests.put(f'{url}/lights', headers=headers, json=data)

def Set_state_temp_val(brightness=10, temperature = 344, poweredOnState=None):
    # data = { "numberOfLights": 1, "lights": [ { "temperature": 500 } ] }
    if poweredOnState is not None:
        data = { "numberOfLights": 1, "lights": [ { "on": poweredOnState, "brightness": brightness, "temperature": round_temp_value(1000000/temperature) } ] }
    else :
        data = { "numberOfLights": 1, "lights": [ { "brightness": brightness, "temperature": round_temp_value(1000000/temperature) } ] }
    
    requests.put(f'{url}/lights', headers=headers, json=data)

def Is_light_on():
    lightInfo = GetInfo()
    return lightInfo['lights'][0]['on']

def Key_icon_name():
    if Is_light_on():
        return "flashlight_off"
    else:
        return "flashlight_on"

def Toggle_lights():
    if Is_light_on():
        TurnOff()
    else:
        Set_state_temp_val(poweredOnState=True)
