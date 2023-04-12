import json
import requests

def SendRequest(action_context):
    method = action_context.get('method', '')
    url = action_context.get('url', '')
    body = action_context.get('body', '')
    headers = action_context.get('headers', '')

    if method == 'get':
        res = requests.get(url, headers=headers)
    elif method == 'post':
        res = requests.post(url, headers=headers, data=json.dumps(body))
    return res.status_code


