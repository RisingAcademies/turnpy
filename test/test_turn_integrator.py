import turnpy.turn_integrator as turn_integrator
import pytest
import json


def load_test_config():
    with open("turn_config.json", "r") as file:
        turn_config = json.load(file)

    return {
        "test_line": turn_config["test_line"],
        "test_number": turn_config["test_number"],
        "test_journey": turn_config["test_journey"],
    }


def test_eval_credentials():
    config_json = {"token": "ABCD", "expiry": "Apr 2, 2010 1:16 PM"}
    with pytest.raises(Exception) as excinfo:
        turn_integrator.eval_credentials(config_json)

        assert "API key as expired for this Turn line." in str(excinfo.value)

    config_json = {"token": "ABCD", "expiry": "Apr 2, 2030 1:16 PM"}
    assert turn_integrator.eval_credentials(config_json) == "ABCD"


# If a specific number has been claimed by a journey sending a message will have no effect. So ensure the test
# number has been released from any claim before trying to test interaction with it.
def release_any_claim(test_config):
    response = turn_integrator.determine_claim(
        test_config["test_number"], test_config["test_line"]
    )
    response_text = json.loads(response.text)

    if response.status_code == 200 and "uuid" in response_text:
        claim_uuid = response_text["uuid"]

        turn_integrator.release_claim(
            test_config["test_number"], test_config["test_line"], claim_uuid
        )


@pytest.mark.vcr()
def test_obtain_contact_profile():
    test_config = load_test_config()

    response = turn_integrator.obtain_contact_profile(
        test_config["test_number"], test_config["test_line"]
    )
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text["schema"]
    assert response_text["fields"]


@pytest.mark.vcr()
def test_update_contact_profile():
    test_config = load_test_config()
    profile_data = {"chat_per_week": "1"}

    response = turn_integrator.update_contact_profile(
        test_config["test_number"], test_config["test_line"], profile_data
    )
    response_text = json.loads(response.text)

    assert response.status_code == 201
    assert response_text["fields"]["chat_per_week"] == "1"


@pytest.mark.vcr()
def test_send_text_message():
    test_config = load_test_config()
    release_any_claim(test_config)

    response = turn_integrator.send_text_message(
        test_config["test_number"], test_config["test_line"], "Test!"
    )
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text["messages"][0]["id"]


@pytest.mark.vcr()
def test_send_interactive_message_button():
    test_config = load_test_config()
    release_any_claim(test_config)

    response = turn_integrator.send_interactive_message(
        test_config["test_number"],
        test_config["test_line"],
        "button",
        {
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
def test_send_interactive_message_list():
    test_config = load_test_config()
    release_any_claim(test_config)

    response = turn_integrator.send_interactive_message(
        test_config["test_number"],
        test_config["test_line"],
        "list",
        {
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
    test_config = load_test_config()
    with open("test/files/test_image.png", "rb") as file:
        # Read the entire file into a bytes object
        binary_data = file.read()

    response = turn_integrator.save_media(
        test_config["test_line"], "image/png", binary_data
    )
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text["media"][0]["id"]


@pytest.mark.vcr()
def test_determine_claim_not_found():
    test_config = load_test_config()
    release_any_claim(test_config)

    response = turn_integrator.determine_claim(
        test_config["test_number"], test_config["test_line"]
    )
    response_text = json.loads(response.text)

    assert response.status_code == 404
    assert "conversation claim" in response_text["errors"][0]


@pytest.mark.vcr()
def test_determine_and_release_claim():
    test_config = load_test_config()
    release_any_claim(test_config)
    turn_integrator.start_journey(
        f'+{test_config["test_number"]}',
        test_config["test_line"],
        test_config["test_journey"],
    )

    response = turn_integrator.determine_claim(
        test_config["test_number"], test_config["test_line"]
    )
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text["uuid"]

    claim_uuid = response_text["uuid"]

    response = turn_integrator.release_claim(
        test_config["test_number"], test_config["test_line"], claim_uuid
    )
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text["claim_uuid"]


@pytest.mark.vcr()
def test_start_journey():
    test_config = load_test_config()
    release_any_claim(test_config)

    response = turn_integrator.start_journey(
        f'+{test_config["test_number"]}',
        test_config["test_line"],
        test_config["test_journey"],
    )
    response_text = json.loads(response.text)

    assert response.status_code == 201
    assert response_text["success"]
