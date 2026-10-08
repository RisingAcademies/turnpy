### TurnPy

A package to help you connect to the [Turn.io](https://whatsapp.turn.io/docs/category/turn-api) API from a Python app.

## Setup

Make a copy of the `turn_config.json.example` file and rename to `turn_config.json`. Then for each of your turn lines, fill in the API key details and the expiry date for that line under the `lines` attribute. The date should be saved in the `turn_config.json` file using the format "Apr 2, 2030 1:16 PM".

To install the dependencies of this project, run `poetry install`.


NOTE: If you run the tests for this Repo, you will need to specify the name of a line and a receiving number to test with details in `turn_config.json`.  For further information about test setup, see the "Testing" section below.

## Use

This package currently supports sending text and media messages as well as obtaining a new API key from Turn.io. The following methods are implemented:

* Obtaining a new auth token
* Sending a text message
* Saving a media file
* Sending a media message
* Managing claims on a number
* More to come soon!

Details are in the comments in the code itself.

## Use without a config file

`turn_config.json` suits a long-running process that owns its filesystem. Somewhere
that cannot provide one - a Lambda with a read-only bundle, holding its credential in
a secrets manager - pass the token straight in instead, and `line_name` is ignored:

```python
from turnpy.turn_integrator import send_text_message, send_template_message

send_text_message(msisdn, None, "hello", token=my_token)

send_template_message(
    msisdn, None, "analysis_ready",
    body_params=["Ada", "Fractions"],
    token=my_token,
    namespace=my_template_namespace,
)
```

## Testing
### Setup
The Turnpy tests require a full turn_config.json.  This includes values for `template_name`, `test_journey`, and `test_template`.  Tests can be run against both an authenticated WhatsApp line as well as against Turn virtual lines.  However, message templates are only available on authenticated WhatsApp lines, so tests related to message templates will fail when run against a virtual line. 

The `test_journey` value should be a UUID for a journey that you have created in the Turn platform.  You may get that UUID by clicking on the 3-dot menu next to the journey name and selecting "Copy ID".


The `test_template` should be the name of a template that has been set up and approved.  The template must include variables in both the header and body.  Below is a sample template.

```
Header:
Test Template: {{1}} - Test

Body:
Hi there, this is a test.  

Here is some test content: {{1}}.  

The test message is over.
```

Additionally, ensure that you have the repository dependencies from pyproject.toml installed.  `pytest-vcr` records the API interactions from the tests to a cassettes folder for your review.  These recordings should not be added to the repo.  The tests will run successfully without `pytest-vcr`, so it is an optional package.


### Running the tests
The tests run against the actual WhatsApp line that your config points to.  Test messages will not be sent unless the `test_number` specified in `turn_config.json` has an active conversation window with the line with the given `token`.  Send a test message to the targeted line from a device with the `test_number` before running the tests.

To run the tests, type `pytest`.

## Involvement

Please assist in improving this project! Please open issues, send PRs and suggestions welcome.
