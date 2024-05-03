from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import os
import requests

def turn_credentials():
    return os.getenv('TURN_API_KEY')

def obtain_auth_token(username, password):
    u_pass = HTTPBasicAuth(username, password)
    response = requests.post('https://whatsapp.turn.io/v1/users/login', auth=u_pass)

def send_text_message(line_number, msisdn, message):
    message_data = {
        'preview_url': false,
        'recipient_type': 'individual',
        'to': f'{msisdn}',
        'type': 'text',
        'text': {
            'body': message
        }
    }

    send_message(message_data)

def send_message(message_data):
    auth_headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {turn_credentials()}'
    }

    requests.post('https://whatsapp.turn.io/v1/messages', headers=auth_headers, data=message_data)
