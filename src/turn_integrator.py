from requests.auth import HTTPBasicAuth
from datetime import datetime
import requests
import json

### Load and evaluate the cedentials from the turn_config.json file
def load_credentials(file_name, line_name):
    with open(file_name, 'r') as file:
        turn_config = json.load(file)

    return turn_config['lines'][line_name]

def eval_credentials(config_json):
    with open('turn_config.json', 'r') as file:
        turn_config = json.load(file)

    token_expiry = datetime.strptime(config_json["expiry"], '%b %d, %Y %I:%M %p')
    if token_expiry > datetime.now():
        return config_json["api_key"]
    else:
        raise Exception("API key as expired for this Turn line.")

def turn_credentials(line_name):
    config_json = load_credentials('turn_config.json', line_name)

    return eval_credentials(config_json)

### Obtain a new auth token from Turn.io
### TODO Not tested yet
def obtain_auth_token(username, password):
    u_pass = HTTPBasicAuth(username, password)
    return requests.post('https://whatsapp.turn.io/v1/users/login', auth=u_pass)

### Send the different kinds of messages. See documentation here:
### https://whatsapp.turn.io/docs/api/messages
def send_message(message_data, line_name):
    auth_headers = {
        'Authorization': f'Bearer {turn_credentials(line_name)}'
    }

    return requests.post('https://whatsapp.turn.io/v1/messages', headers=auth_headers, json=message_data)

def send_text_message(msisdn, message, line_name):
    message_data = {
        'preview_url': False,
        'recipient_type': 'individual',
        'to': f'{msisdn}',
        'type': 'text',
        'text': {
            'body': message
        }
    }
    response = send_message(message_data, line_name)
    print(response.text)
    return response

def send_media_message(msisdn, media_type, media_id, line_name, caption=""):
    message_data = {
        "to": msisdn,
        "recipient_type": "individual",
    }
    if media_type == "audio":
        message_data["type"] = "audio"
        message_data["audio"] = {"id": media_id}

    elif media_type == "document":
        message_data["type"] = "document"
        message_data["document"] = {
            "id": media_id,
            "caption": caption
        }

    elif media_type == "image":
        message_data["type"] = "image"
        message_data["image"] = {
            "id": media_id,
            "caption": caption
        }

    elif media_type == "sticker":
        message_data["type"] = "sticket"
        message_data["sticket"] = {"id": media_id}

    elif media_type == "video":
        message_data["type"] = "video"
        message_data["video"] = {
            "id": media_id,
            "caption": caption
        }

    response = send_message(message_data, line_name)
    print(response.text)
    return response


### Send an interactive message with a dropdown or buttons.
### The sections argument is a dictionary with a few attrbutes:
### 'header_text' - text, optional
### 'header_image' - id of a saved image, optional
### 'body_text' - text, required
### 'footer_text' - text, optional
### 'buttons' - array, required array of buttons with text and callback_id, used if the interactive_type
### is a button.
### Further details about the API call here:
### https://whatsapp.turn.io/docs/api/messages#interactive-messages

def send_interactive_message(msisdn, interactive_type, line_name, sections):
    message_data = {
        "to": msisdn,
        "type": "interactive",
        "interactive": {
            "type": interactive_type,
            "body": {
                "text": sections['body_text']
            },
            'action': {}
        },
    }

    if sections['header_text']:
        message_data['interactive']['header'] = {
            "type": "text",
            "text": sections['header_text']
        }
    elif sections['header_image']:
        message_data['interactive']['header'] = {
            "type": "image",
            "id": sections['header_image']
        }

    if sections['footer_text']:
        message_data['interactive']['footer'] = {
            "text": sections['footer_text']
        }

    if interactive_type == 'button':
        message_data['interactive']['action']['buttons'] = []
        for button in sections['buttons']:
            message_data['interactive']['action']['buttons'].append(
                {
                    "type": "reply",
                    "reply": {
                        "id": button['callback_id'],
                        "title": button['text']
                    }
                }
            )

    print(message_data)
    response = send_message(message_data, line_name)
    print(response.text)
    return response

### Save media to Turn for sending. See the supported file types on the Turn documentation here:
### https://whatsapp.turn.io/docs/api/media#supported-file-types
def save_media(type, file_binary, line_name):
    auth_headers = {
        'Authorization': f'Bearer {turn_credentials(line_name)}',
        'Content-Type': type
    }
    response = requests.post('https://whatsapp.turn.io/v1/media', headers=auth_headers, data=file_binary)
    print(response.text)
    return response

### Manage claimed numbers, like determining a claim by a Turn process line a Journey,
### or deleting one. See:
### https://whatsapp.turn.io/docs/api/extensions#managing-conversation-claims
def determine_claim(msisdn, line_name):
    auth_headers = {
        'Authorization': f'Bearer {turn_credentials(line_name)}',
        'Accept': 'application/vnd.v1+json'
    }
    response = requests.get(f'https://whatsapp.turn.io/v1/contacts/{msisdn}/claim', headers=auth_headers)
    print(response.text)
    return response

def destroy_claim(msisdn, line_name, claim_uuid):
    claim_data = {"claim_uuid": claim_uuid}

    auth_headers = {
        'Authorization': f'Bearer {turn_credentials(line_name)}',
        'Accept': 'application/vnd.v1+json'
    }
    response = requests.delete(f'https://whatsapp.turn.io/v1/contacts/{msisdn}/claim', headers=auth_headers, json=claim_data)
    print(response.text)
    return response

### Start a journey for a specific user. Details here:
### https://whatsapp.turn.io/docs/api/stacks

def start_journey(msisdn, line_name, stack_uuid):
    journey_data = {"wa_id": msisdn}

    auth_headers = {
        'Authorization': f'Bearer {turn_credentials(line_name)}',
        'Accept': 'application/vnd.v1+json'
    }
    response = requests.post(f'https://whatsapp.turn.io/v1/stacks/{stack_uuid}/start', headers=auth_headers, json=journey_data)
    print(response.text)
    return response