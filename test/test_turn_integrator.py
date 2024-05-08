import src.turn_integrator as turn_integrator
import pytest
import json

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

def test_save_file():
    with open('test/files/test_image.png', 'rb') as file:
        # Read the entire file into a bytes object
        binary_data = file.read()

    response = turn_integrator.save_media('image/png', binary_data, 'Rori Staging')
    response_text = json.loads(response.text)

    assert response.status_code == 200
    assert response_text['media'][0]['id']