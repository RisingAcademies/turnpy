import src.turn_integrator as turn_integrator
import pytest
import json

def load_test_config():
    with open('turn_config.json', 'r') as file:
        turn_config = json.load(file)

    return { 'test_line': turn_config['test_line'], 'test_number': turn_config['test_number'], 'test_journey': turn_config['test_journey'] }

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
    test_config = load_test_config()
    response = turn_integrator.send_text_message(test_config["test_number"], 'Test!', test_config['test_line'])
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text['messages'][0]['id']

@pytest.mark.vcr()
def test_save_media():
    test_config = load_test_config()
    with open('test/files/test_image.png', 'rb') as file:
        # Read the entire file into a bytes object
        binary_data = file.read()

    response = turn_integrator.save_media('image/png', binary_data, test_config['test_line'])
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text['media'][0]['id']

@pytest.mark.vcr()
def test_determine_claim_not_found():
    test_config = load_test_config()
    response = turn_integrator.determine_claim(test_config['test_number'], test_config['test_line'])
    response_text = json.loads(response.text)

    assert response.status_code == 404
    assert 'conversation claim' in response_text['errors'][0]

@pytest.mark.vcr()
def test_determine_claim_found():
    test_config = load_test_config()
    response = turn_integrator.determine_claim(test_config['test_number'], test_config['test_line'])
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text['uuid']

@pytest.mark.vcr()
def test_destroy_claim():
    test_config = load_test_config()
    response = turn_integrator.determine_claim(test_config['test_number'], test_config['test_line'])
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text['uuid']

    claim_uuid = response_text['uuid']

    response = turn_integrator.destroy_claim(test_config['test_number'], test_config['test_line'], claim_uuid)
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text['claim_uuid']

@pytest.mark.vcr()
def test_start_journey():
    test_config = load_test_config()
    response = turn_integrator.start_journey(f'+{test_config["test_number"]}', test_config['test_line'], test_config['test_journey'])
    response_text = json.loads(response.text)

    assert response.status_code == 201
    assert response_text['success']
