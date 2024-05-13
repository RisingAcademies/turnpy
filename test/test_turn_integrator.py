import src.turn_integrator as turn_integrator
import pytest
import json

def load_test_config():
    with open('turn_config.json', 'r') as file:
        turn_config = json.load(file)

    return { 'test_line': turn_config['test_line'], 'test_number': turn_config['test_number'] }

def test_eval_credentials():
    config_json = {
      "api_key": "ABCD",
      "expiry": "Apr 2, 2010 1:16 PM"
    }
    with pytest.raises(Exception) as excinfo:
        turn_integrator.eval_credentials(config_json)

        assert "API key as expired for this Turn line." in str(excinfo.value)

    config_json = {
      "api_key": "ABCD",
      "expiry": "Apr 2, 2030 1:16 PM"
    }
    assert turn_integrator.eval_credentials(config_json) == 'ABCD'

@pytest.mark.vcr()
def test_send_text_message():
    text_config = load_test_config()
    response = turn_integrator.send_text_message(f'+{text_config["test_number"]}', 'Test!', text_config['test_line'])
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text['messages'][0]['id']

@pytest.mark.vcr()
def test_determine_claim_not_found():
    text_config = load_test_config()
    response = turn_integrator.determine_claim(text_config['test_number'], text_config['test_line'])
    response_text = json.loads(response.text)

    assert response.status_code == 404
    assert 'conversation claim' in response_text['errors'][0]

@pytest.mark.vcr()
def test_save_file():
    text_config = load_test_config()
    with open('test/files/test_image.png', 'rb') as file:
        # Read the entire file into a bytes object
        binary_data = file.read()

    response = turn_integrator.save_media('image/png', binary_data, text_config['test_line'])
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text['media'][0]['id']