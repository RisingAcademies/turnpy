import json
import logging
from datetime import datetime

import httpx
import requests


class AsyncTurnClient:
    def __init__(self):
        self._client = None

    async def get_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://whatsapp.turn.io/v1", timeout=30.0
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


turn_client = AsyncTurnClient()


"""SETUP"""
"""
Load and evaluate the credentials from the turn_config.json file.
"""

logger = logging.getLogger(__name__)


async def load_credentials(file_name: str, line_name: str) -> str:
    with open(file_name, "r") as file:
        turn_config = json.load(file)

    return turn_config["lines"][line_name]


"""
Determine if the Turn credentials are still valid.
"""


async def eval_credentials(config_json: json) -> str:
    with open("turn_config.json", "r") as file:
        turn_config = json.load(file)

    token_expiry = datetime.strptime(config_json["expiry"], "%b %d, %Y %I:%M %p")
    if token_expiry > datetime.now():
        return config_json["token"]
    else:
        raise ValueError("API key has expired for this Turn line.")


async def turn_credentials(line_name):
    config_json = await load_credentials("turn_config.json", line_name)

    credentials = await eval_credentials(config_json)
    return credentials


"""CONTACTS"""
"""
Obtain a contact profile.

See documentation here:
https://whatsapp.turn.io/docs/api/contacts#retrieve-a-contact-profile
"""


async def obtain_contact_profile(
    msisdn: str, line_name: str, client: httpx.AsyncClient = None
) -> requests.Response:
    turn_creds = await turn_credentials(line_name)
    auth_headers = {
        "Authorization": f"Bearer {turn_creds}",
        "Accept": "application/vnd.v1+json",
    }
    if not client:
        client = await turn_client.get_client()
    response = await client.get(f"contacts/{msisdn}/profile", headers=auth_headers)

    logging.debug(f"Obtained contact profile response: {response.text}")
    return response


"""Update a contact profile.

Supply only the fields that need updating. See documentation here:
https://whatsapp.turn.io/docs/api/contacts#update-a-contact-profile
"""


async def update_contact_profile(
    msisdn: str, line_name: str, profile_data: json, client: httpx.AsyncClient = None
) -> requests.Response:
    turn_creds = await turn_credentials(line_name)
    auth_headers = {
        "Authorization": f"Bearer {turn_creds}",
        "Accept": "application/vnd.v1+json",
    }

    if not client:
        client = await turn_client.get_client()
    response = await client.patch(
        f"contacts/{msisdn}/profile",
        headers=auth_headers,
        json=profile_data,
    )
    logging.debug(f"Updated contact profile response: {response.text}")
    return response


""" MESSAGES"""
"""
Send the different kinds of messages.

See documentation here: https://whatsapp.turn.io/docs/api/messages
"""


async def send_message(
    line_name: str, message_data: json, client: httpx.AsyncClient = None
) -> requests.Response:
    turn_creds = await turn_credentials(line_name)
    auth_headers = {"Authorization": f"Bearer {turn_creds}"}

    if not client:
        client = await turn_client.get_client()
    response = await client.post("messages", headers=auth_headers, json=message_data)
    logger.info("Sent a message...")
    return response


"""
Send a text message.

The recipient_type is currrently hardcoded to "individual" as there are no API docs pointing to
another type of recipient.
"""


async def send_text_message(
    msisdn: str, line_name: str, message: str
) -> requests.Response:
    message_data = {
        "preview_url": False,
        "recipient_type": "individual",
        "to": f"{msisdn}",
        "type": "text",
        "text": {"body": message},
    }

    response = await send_message(line_name, message_data)
    logger.debug(f"Sent text message response: {response.text}")
    return response


async def send_media_message(
    msisdn: str,
    line_name: str,
    media_type: str,
    media_id: str,
    caption="",
    message: str = "",
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

    response = await send_message(line_name, message_data)
    logger.debug(f"Sent media message response: {response.text}")
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


async def send_interactive_message(
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

    response = await send_message(line_name, message_data)
    logger.debug(f"Sent interactive message response: {response.text}")
    return response


"""MEDIA"""
"""
Save media to Turn for sending.

See the supported file types on the Turn documentation here:
https://whatsapp.turn.io/docs/api/media#supported-file-types
"""


async def save_media(
    line_name: str, type: str, file_binary: str, client: httpx.AsyncClient = None
) -> requests.Response:
    turn_creds = await turn_credentials(line_name)
    auth_headers = {
        "Authorization": f"Bearer {turn_creds}",
        "Content-Type": type,
    }

    if not client:
        client = await turn_client.get_client()
    response = await client.post("media", headers=auth_headers, data=file_binary)
    logger.info(f"Saved media response {response.text}")
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


async def send_template_message(
    msisdn: str,
    line_name: str,
    template_name: str,
    header_params: list = None,
    body_params: list = None,
    language: str = "en",
) -> requests.Response:
    # Get credentials and config
    config_json = await load_credentials("turn_config.json", line_name)
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

    response = await send_message(line_name, message_data)
    logger.debug(f"Send a template message: {response.text}")
    return response


"""CLAIMS"""
"""
Manage claimed numbers, like determining a claim by a Turn process line a Journey,
or deleting one.

See: https://whatsapp.turn.io/docs/api/extensions#managing-conversation-claims
"""


async def determine_claim(
    msisdn: str, line_name: str, client: httpx.AsyncClient = None
) -> requests.Response:
    turn_creds = await turn_credentials(line_name)
    auth_headers = {
        "Authorization": f"Bearer {turn_creds}",
        "Accept": "application/vnd.v1+json",
    }

    if not client:
        client = await turn_client.get_client()
    response = await client.get(f"contacts/{msisdn}/claim", headers=auth_headers)
    logger.debug(f"Determined claim response: {response.text}")
    return response


async def release_claim(
    msisdn: str, line_name: str, claim_uuid: str, client: httpx.AsyncClient = None
) -> requests.Response:
    claim_data = {"claim_uuid": claim_uuid}

    turn_creds = await turn_credentials(line_name)
    auth_headers = {
        "Authorization": f"Bearer {turn_creds}",
        "Accept": "application/vnd.v1+json",
    }

    if not client:
        client = await turn_client.get_client()
    response = await client.delete(
        f"contacts/{msisdn}/claim",
        headers=auth_headers,
        json=claim_data,
    )
    logger.debug(f"Released claim response: {response.text}")
    return response


"""JOURNEYS"""
"""
Start a journey for a specific user.

Details here: https://whatsapp.turn.io/docs/api/stacks
"""


async def start_journey(
    msisdn: str, line_name: str, stack_uuid: str, client: httpx.AsyncClient = None
) -> requests.Response:
    journey_data = {"wa_id": msisdn}

    turn_creds = await turn_credentials(line_name)
    auth_headers = {
        "Authorization": f"Bearer {turn_creds}",
        "Accept": "application/vnd.v1+json",
    }

    if not client:
        client = await turn_client.get_client()

    response = await client.post(
        f"stacks/{stack_uuid}/start",
        headers=auth_headers,
        json=journey_data,
    )
    logger.debug(f"Started journey response: {response.text}")
    return response
