from requests.auth import HTTPBasicAuth
from datetime import datetime
import requests
import json

def turn_credentials(line_name):
    with open('turn_config.json', 'r') as file:
        turn_config = json.load(file)

    token_expiry = datetime.strptime(turn_config[line_name]["expiry"], '%b %d, %Y %I:%M %p')
    if token_expiry > datetime.now():
        return turn_config[line_name]["api_key"]
    else:
        raise Exception("API key as expired for this Turn line.")


def obtain_auth_token(username, password):
    u_pass = HTTPBasicAuth(username, password)
    return requests.post('https://whatsapp.turn.io/v1/users/login', auth=u_pass)

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

def send_media_message(msisdn, media_type, media_id, caption=""):
    message_data = {}
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

    message_data["recipient_type"] = "individual"
    message_data["to"] =  msisdn

    response = print(send_message(message_data))
    print(response.text)
    return response

def save_media(type, file_binary):
    auth_headers = {
        'Authorization': f'Bearer {turn_credentials()}'
    }

    return requests.post('https://whatsapp.turn.io/v1/media', headers=auth_headers, data=file_binary)
