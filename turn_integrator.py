from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import os
import requests

def turn_credentials():
    load_dotenv()
    return os.getenv('TURN_API_KEY')

def obtain_auth_token(username, password):
    u_pass = HTTPBasicAuth(username, password)
    return requests.post('https://whatsapp.turn.io/v1/users/login', auth=u_pass)

def send_message(message_data):
    auth_headers = {
        'Authorization': f'Bearer {turn_credentials()}'
    }

    return requests.post('https://whatsapp.turn.io/v1/messages', headers=auth_headers, json=message_data)

def send_text_message(msisdn, message):
    message_data = {
        'preview_url': False,
        'recipient_type': 'individual',
        'to': f'{msisdn}',
        'type': 'text',
        'text': {
            'body': message
        }
    }
    response = send_message(message_data)
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