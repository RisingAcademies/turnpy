import src.turn_integrator as turn_integrator
import pytest

def test_eval_config():
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