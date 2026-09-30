import json
from contextlib import contextmanager

import pytest

import turnpy.turn_integrator as turn_integrator


def load_test_config():
    with open("turn_config.json", "r") as file:
        turn_config = json.load(file)

    return {
        "test_line": turn_config["test_line"],
        "test_number": turn_config["test_number"],
        "test_bsuid": turn_config["test_bsuid"],
        "test_journey": turn_config["test_journey"],
        "test_template": turn_config["test_template"],
    }


test_config = load_test_config()

# explicit credentials for non-config-file environments
test_line_credentials = turn_integrator.load_credentials(
    "turn_config.json", test_config["test_line"]
)


# Anything turnpy opens inside this block is a turn_config.json fallback, which
# for those callers means a FileNotFoundError on their first send in production.
@contextmanager
def no_config_file():
    def refuse(name, *_args, **_kwargs):
        raise AssertionError(f"turnpy opened {name} despite being given a token")

    with pytest.MonkeyPatch.context() as patched:
        patched.setattr(turn_integrator, "open", refuse, raising=False)
        yield


def test_eval_credentials():
    config_json = {"token": "ABCD", "expiry": "Apr 2, 2010 1:16 PM"}
    with pytest.raises(Exception) as excinfo:
        turn_integrator.eval_credentials(config_json)

        assert "API key as expired for this Turn line." in str(excinfo.value)

    config_json = {"token": "ABCD", "expiry": "Apr 2, 2030 1:16 PM"}
    assert turn_integrator.eval_credentials(config_json) == "ABCD"


def test_turn_credentials_prefers_an_injected_token():
    with no_config_file():
        assert turn_integrator.turn_credentials("no_such_line", token="ABCD") == "ABCD"


# If a specific number has been claimed by a journey sending a message will have no effect. So ensure the test
# number has been released from any claim before trying to test interaction with it.
def release_any_claim(test_config):
    response = turn_integrator.determine_claim(
        msisdn=test_config.get("test_number", ""),
        bsuid=test_config.get("test_bsuid", ""),
        line_name=test_config["test_line"],
    )
    response_text = json.loads(response.text)

    if response.status_code == 200 and "uuid" in response_text:
        claim_uuid = response_text["uuid"]

        turn_integrator.release_claim(
            msisdn=test_config.get("test_number", ""),
            bsuid=test_config.get("test_bsuid", ""),
            line_name=test_config["test_line"],
            claim_uuid=claim_uuid,
        )


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "msisdn,bsuid",
    [
        (test_config["test_number"], ""),
        ("", test_config["test_bsuid"]),
        (test_config["test_number"], test_config["test_bsuid"]),
    ],
)
def test_obtain_contact_profile(msisdn, bsuid):
    response = turn_integrator.obtain_contact_profile(
        msisdn=msisdn, bsuid=bsuid, line_name=test_config["test_line"]
    )
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text["schema"]
    assert response_text["fields"]


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "msisdn,bsuid",
    [
        (test_config["test_number"], ""),
        ("", test_config["test_bsuid"]),
        (test_config["test_number"], test_config["test_bsuid"]),
    ],
)
def test_update_contact_profile(msisdn, bsuid):
    profile_data = {"opted_in": True}

    response = turn_integrator.update_contact_profile(
        msisdn=msisdn,
        bsuid=bsuid,
        line_name=test_config["test_line"],
        profile_data=profile_data,
    )
    response_text = json.loads(response.text)

    assert response.status_code == 201
    assert response_text["fields"]["opted_in"] == True

    profile_data = {"opted_in": False}
    response = turn_integrator.update_contact_profile(
        msisdn=msisdn,
        bsuid=bsuid,
        line_name=test_config["test_line"],
        profile_data=profile_data,
    )
    response_text = json.loads(response.text)

    assert response.status_code == 201
    assert response_text["fields"]["opted_in"] == False


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "msisdn,bsuid",
    [
        (test_config["test_number"], ""),
        ("", test_config["test_bsuid"]),
        (test_config["test_number"], test_config["test_bsuid"]),
    ],
)
def test_send_text_message(msisdn, bsuid):
    release_any_claim(test_config)

    response = turn_integrator.send_text_message(
        msisdn=msisdn,
        bsuid=bsuid,
        line_name=test_config["test_line"],
        message="Test!",
    )
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text["messages"][0]["id"]


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "msisdn,bsuid",
    [
        (test_config["test_number"], ""),
        ("", test_config["test_bsuid"]),
        (test_config["test_number"], test_config["test_bsuid"]),
    ],
)
def test_send_interactive_message_button(msisdn, bsuid):
    release_any_claim(test_config)

    response = turn_integrator.send_interactive_message(
        msisdn=msisdn,
        bsuid=bsuid,
        line_name=test_config["test_line"],
        interactive_type="button",
        sections={
            "header_text": "Testheader",
            "footer_text": "Testfooter",
            "body_text": "Testbody",
            "buttons": [
                {"callback_id": "1234", "text": "Testbutton 1"},
                {"callback_id": "1235", "text": "Testbutton 2"},
            ],
        },
    )
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text["messages"][0]["id"]


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "msisdn,bsuid",
    [
        (test_config["test_number"], ""),
        ("", test_config["test_bsuid"]),
        (test_config["test_number"], test_config["test_bsuid"]),
    ],
)
def test_send_interactive_message_list(msisdn, bsuid):
    release_any_claim(test_config)

    response = turn_integrator.send_interactive_message(
        msisdn=msisdn,
        bsuid=bsuid,
        line_name=test_config["test_line"],
        interactive_type="list",
        sections={
            "header_text": "Testheader",
            "footer_text": "Testfooter",
            "body_text": "Testbody",
            "list_button": "Click here",
            "list_title": "Interesting list",
            "list_items": [
                {"callback_id": "1234", "text": "Test item 1"},
                {"callback_id": "1235", "text": "Test item 2"},
            ],
        },
    )
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text["messages"][0]["id"]


@pytest.mark.vcr()
def test_save_media():
    with open("test/files/test_image.png", "rb") as file:
        # Read the entire file into a bytes object
        binary_data = file.read()

    response = turn_integrator.save_media(
        line_name=test_config["test_line"], type="image/png", file_binary=binary_data
    )
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text["media"][0]["id"]


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "msisdn,bsuid",
    [
        (test_config["test_number"], ""),
        ("", test_config["test_bsuid"]),
        (test_config["test_number"], test_config["test_bsuid"]),
    ],
)
def test_determine_claim_not_found(msisdn, bsuid):
    release_any_claim(test_config)

    response = turn_integrator.determine_claim(
        msisdn=msisdn, bsuid=bsuid, line_name=test_config["test_line"]
    )
    response_text = json.loads(response.text)

    assert response.status_code == 404
    assert "conversation claim" in response_text["errors"][0]


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "msisdn,bsuid",
    [
        (test_config["test_number"], ""),
        ("", test_config["test_bsuid"]),
        (test_config["test_number"], test_config["test_bsuid"]),
    ],
)
def test_determine_and_release_claim(msisdn, bsuid):
    release_any_claim(test_config)

    if msisdn:
        formatted_msisdn = f"+{msisdn}"
    else:
        formatted_msisdn = ""

    turn_integrator.start_journey(
        msisdn=formatted_msisdn,
        bsuid=bsuid,
        line_name=test_config["test_line"],
        stack_uuid=test_config["test_journey"],
    )

    response = turn_integrator.determine_claim(
        msisdn=msisdn, bsuid=bsuid, line_name=test_config["test_line"]
    )
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text["uuid"]

    claim_uuid = response_text["uuid"]

    response = turn_integrator.release_claim(
        msisdn=msisdn,
        bsuid=bsuid,
        line_name=test_config["test_line"],
        claim_uuid=claim_uuid,
    )
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text["claim_uuid"]


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "msisdn,bsuid",
    [
        (test_config["test_number"], ""),
        ("", test_config["test_bsuid"]),
        (test_config["test_number"], test_config["test_bsuid"]),
    ],
)
def test_start_journey(msisdn, bsuid):
    release_any_claim(test_config)

    if msisdn:
        formatted_msisdn = f"+{msisdn}"
    else:
        formatted_msisdn = ""

    response = turn_integrator.start_journey(
        msisdn=formatted_msisdn,
        bsuid=bsuid,
        line_name=test_config["test_line"],
        stack_uuid=test_config["test_journey"],
    )
    response_text = json.loads(response.text)

    assert response.status_code == 201
    assert response_text["success"]


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "msisdn,bsuid",
    [
        (test_config["test_number"], ""),
        ("", test_config["test_bsuid"]),
        (test_config["test_number"], test_config["test_bsuid"]),
    ],
)
def test_send_template_message(msisdn, bsuid):
    release_any_claim(test_config)

    response = turn_integrator.send_template_message(
        msisdn=msisdn,
        bsuid=bsuid,
        line_name=test_config["test_line"],
        template_name=test_config["test_template"],
        header_params=["Test Header"],
        body_params=["Test Body Param 1"],
        language="en",
    )
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text["messages"][0]["id"]


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "msisdn,bsuid",
    [
        (test_config["test_number"], ""),
        ("", test_config["test_bsuid"]),
        (test_config["test_number"], test_config["test_bsuid"]),
    ],
)
def test_send_text_message_with_an_injected_token(msisdn, bsuid):
    release_any_claim(test_config)

    with no_config_file():
        response = turn_integrator.send_text_message(
            msisdn=msisdn,
            bsuid=bsuid,
            line_name=test_config["test_line"],
            message="Test!",
            token=test_line_credentials["token"],
        )
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text["messages"][0]["id"]


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "msisdn,bsuid",
    [
        (test_config["test_number"], ""),
        ("", test_config["test_bsuid"]),
        (test_config["test_number"], test_config["test_bsuid"]),
    ],
)
def test_send_template_message_with_an_injected_token(msisdn, bsuid):
    release_any_claim(test_config)

    with no_config_file():
        response = turn_integrator.send_template_message(
            msisdn=msisdn,
            bsuid=bsuid,
            line_name=test_config["test_line"],
            template_name=test_config["test_template"],
            header_params=["Test Header"],
            body_params=["Test Body Param 1"],
            language="en",
            token=test_line_credentials["token"],
            namespace=test_line_credentials["template_namespace"],
        )
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text["messages"][0]["id"]
