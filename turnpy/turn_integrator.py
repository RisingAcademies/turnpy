import json
import logging
from datetime import datetime

import requests
from requests.auth import HTTPBasicAuth

"""SETUP"""
"""
Load and evaluate the cedentials from the turn_config.json file.
"""

logger = logging.getLogger(__name__)


def load_credentials(file_name: str, line_name: str) -> str:
    with open(file_name, "r") as file:
        turn_config = json.load(file)

    return turn_config["lines"][line_name]

"""
Determine if the Turn credentials are still valid.
"""

def eval_credentials(config_json: json) -> str:
    with open("turn_config.json", "r") as file:
        turn_config = json.load(file)

    token_expiry = datetime.strptime(config_json["expiry"], "%b %d, %Y %I:%M %p")
    if token_expiry > datetime.now():
        return config_json["token"]
    else:
        raise ValueError("API key has expired for this Turn line.")

def turn_credentials(line_name):
    config_json = load_credentials("turn_config.json", line_name)

    return eval_credentials(config_json)

"""CONTACTS"""
"""
Obtain a contact profile.

See documentation here:
https://whatsapp.turn.io/docs/api/contacts#retrieve-a-contact-profile
"""

def obtain_contact_profile(msisdn: str, line_name: str) -> requests.Response:
    auth_headers = {
        "Authorization": f"Bearer {turn_credentials(line_name)}",
        "Accept": "application/vnd.v1+json",
    }

    response = requests.get(
        f"https://whatsapp.turn.io/v1/contacts/{msisdn}/profile", headers=auth_headers
    )
    logging.debug("Obtained contact profile response", response.text)
    return response

"""Update a contact profile.

Supply only the fields that need updating. See documentation here:
https://whatsapp.turn.io/docs/api/contacts#update-a-contact-profile
"""

def update_contact_profile(
    msisdn: str, line_name: str, profile_data: json
) -> requests.Response:
    auth_headers = {
        "Authorization": f"Bearer {turn_credentials(line_name)}",
        "Accept": "application/vnd.v1+json",
    }

    response = requests.patch(
        f"https://whatsapp.turn.io/v1/contacts/{msisdn}/profile",
        headers=auth_headers,
        json=profile_data,
    )
    logging.debug("Updated contact profile response", response.text)
    return response

""" MESSAGES"""
"""
Send the different kinds of messages.

See documentation here: https://whatsapp.turn.io/docs/api/messages
"""

def send_message(line_name: str, message_data: json) -> requests.Response:
    auth_headers = {"Authorization": f"Bearer {turn_credentials(line_name)}"}

    return requests.post(
        "https://whatsapp.turn.io/v1/messages", headers=auth_headers, json=message_data
    )

"""
Send a text message.

The recipient_type is currrently hardcoded to "individual" as there are no API docs pointing to
another type of recipient.
"""

def send_text_message(msisdn: str, line_name: str, message: str) -> requests.Response:
    message_data = {
        "preview_url": False,
        "recipient_type": "individual",
        "to": f"{msisdn}",
        "type": "text",
        "text": {"body": message},
    }

    response = send_message(line_name, message_data)
    logging.debug("Sent text message response", response.text)
    return response

def send_media_message(
    msisdn: str, line_name: str, media_type: str, media_id: str, caption="", message: str=""
) -> requests.Response:
    message_data = {
        "to": msisdn,
        "recipient_type": "individual",
    }
    if media_type == "audio":
        message_data["type"] = "audio"
        message_data["audio"] = {"id": media_id}

    elif media_type == "document":
        message_data["type"] = "document"
        message_data["document"] = {"id": media_id, "caption": caption}

    elif media_type == "image":
        message_data["type"] = "image"
        message_data["image"] = {"id": media_id, "caption": caption}

    elif media_type == "sticker":
        message_data["type"] = "sticket"
        message_data["sticket"] = {"id": media_id}

    elif media_type == "video":
        message_data["type"] = "video"
        message_data["video"] = {"id": media_id, "caption": caption}

    if message:
        message_data["text"] = {"body": message}

    response = send_message(line_name, message_data)
    logging.debug("Sent media message response", response.text)
    return response

"""Send an interactive message with a dropdown or buttons.

The sections argument is a dictionary with a few attrbutes:
'header_text' - text, optional
'header_image' - id of a saved image, optional
'body_text' - text, required
'footer_text' - text, optional
'buttons' - array, required array of buttons with text and callback_id, used if the interactive_type is a 'button'.
'list_button' - text, required text of the list button for interactive_type = 'list'
'list_title' - text, required title text for the list for interactive_type = 'list'
'list_items' - array, required array of items with text and callback_id for interactive_type = 'list'
Further details about the API call here:
https://whatsapp.turn.io/docs/api/messages#interactive-messages
"""

def send_interactive_message(
    msisdn: str, line_name: str, interactive_type: str, sections: json
) -> requests.Response:
    message_data = {
        "to": msisdn,
        "type": "interactive",
        "interactive": {
            "type": interactive_type,
            "body": {"text": sections["body_text"]},
            "action": {},
        },
    }

    if sections["header_text"]:
        message_data["interactive"]["header"] = {
            "type": "text",
            "text": sections["header_text"],
        }
    elif sections["header_image"]:
        message_data["interactive"]["header"] = {
            "type": "image",
            "id": sections["header_image"],
        }

    if sections["footer_text"]:
        message_data["interactive"]["footer"] = {"text": sections["footer_text"]}

    if interactive_type == "button":
        message_data["interactive"]["action"]["buttons"] = []
        for button in sections["buttons"]:
            message_data["interactive"]["action"]["buttons"].append(
                {
                    "type": "reply",
                    "reply": {"id": button["callback_id"], "title": button["text"]},
                }
            )

    if interactive_type == "list":
        message_data["interactive"]["action"]["button"] = sections["list_button"]
        message_data["interactive"]["action"]["sections"] = []
        message_data["interactive"]["action"]["sections"].append({})
        message_data["interactive"]["action"]["sections"][0]["title"] = sections[
            "list_title"
        ]
        message_data["interactive"]["action"]["sections"][0]["rows"] = []
        for list_item in sections["list_items"]:
            message_data["interactive"]["action"]["sections"][0]["rows"].append(
                {"id": list_item["callback_id"], "title": list_item["text"]}
            )

    response = send_message(line_name, message_data)
    logging.debug("Sent interactive message response", response.text)
    return response

"""MEDIA"""
"""
Save media to Turn for sending.

See the supported file types on the Turn documentation here:
https://whatsapp.turn.io/docs/api/media#supported-file-types
"""

def save_media(line_name: str, type: str, file_binary: str) -> requests.Response:
    auth_headers = {
        "Authorization": f"Bearer {turn_credentials(line_name)}",
        "Content-Type": type,
    }
    response = requests.post(
        "https://whatsapp.turn.io/v1/media", headers=auth_headers, data=file_binary
    )
    logging.debug("Saved media response", response.text)
    return response

"""TEMPLATES"""

"""
Send a templated message to a WhatsApp user.

The arguments are:
'msisdn' - string, required WhatsApp ID to send to
'line_name' - string, required Turn line to use
'template_name' - string, required name of the template to use
'header_params' - list, optional list of strings for header placeholders
'body_params' - list, optional list of strings for body placeholders
'language' - string, optional language code for the template (default: 'en')

Further details about the API call here:
https://whatsapp.turn.io/docs/api/messages#template-messages
"""

def send_template_message(
    msisdn: str,
    line_name: str,
    template_name: str,
    header_params: list = None,
    body_params: list = None,
    language: str = "en",
) -> requests.Response:

    # Get credentials and config
    config_json = load_credentials("turn_config.json", line_name)
    template_namespace = config_json["template_namespace"]

    # Build the message data
    message_data = {
        "to": msisdn,
        "type": "template",
        "template": {
            "namespace": template_namespace,
            "name": template_name,
            "language": {"code": language, "policy": "deterministic"},
            "components": [],
        },
    }

    if header_params:
        header_component = {
            "type": "header",
            "parameters": [{"type": "text", "text": param} for param in header_params],
        }
        message_data["template"]["components"].append(header_component)

    if body_params:
        body_component = {
            "type": "body",
            "parameters": [{"type": "text", "text": param} for param in body_params],
        }
        message_data["template"]["components"].append(body_component)

    response = send_message(line_name, message_data)
    logging.debug("Send a template message", response.text)
    return response

"""CLAIMS"""
"""
Manage claimed numbers, like determining a claim by a Turn process line a Journey,
or deleting one.

See: https://whatsapp.turn.io/docs/api/extensions#managing-conversation-claims
"""

def determine_claim(msisdn: str, line_name: str) -> requests.Response:
    auth_headers = {
        "Authorization": f"Bearer {turn_credentials(line_name)}",
        "Accept": "application/vnd.v1+json",
    }
    response = requests.get(
        f"https://whatsapp.turn.io/v1/contacts/{msisdn}/claim", headers=auth_headers
    )
    logging.debug("Determined claim response", response.text)
    return response



def release_claim(msisdn: str, line_name: str, claim_uuid: str) -> requests.Response:
    claim_data = {"claim_uuid": claim_uuid}

    auth_headers = {
        "Authorization": f"Bearer {turn_credentials(line_name)}",
        "Accept": "application/vnd.v1+json",
    }
    response = requests.delete(
        f"https://whatsapp.turn.io/v1/contacts/{msisdn}/claim",
        headers=auth_headers,
        json=claim_data,
    )
    logging.debug("Released claim response", response.text)
    return response

"""JOURNEYS"""
"""
Start a journey for a specific user.

Details here: https://whatsapp.turn.io/docs/api/stacks
"""

def start_journey(msisdn: str, line_name: str, stack_uuid: str) -> requests.Response:
    journey_data = {"wa_id": msisdn}

    auth_headers = {
        "Authorization": f"Bearer {turn_credentials(line_name)}",
        "Accept": "application/vnd.v1+json",
    }
    response = requests.post(
        f"https://whatsapp.turn.io/v1/stacks/{stack_uuid}/start",
        headers=auth_headers,
        json=journey_data,
    )
    logging.debug("Started journey response", response.text)
    return response
