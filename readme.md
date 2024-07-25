### TurnPy

A package to help you connect to the [Turn.io](https://whatsapp.turn.io/docs/category/turn-api) API from a Python app.

## Setup

Make a copy of the `turn_config.json.example` file and rename to `turn_config.json`. Then for each of your turn lines, fill in the API key details and the expiry date for that line under the `lines` attribute. The date should be saved in the `turn_config.json` file exactly as shown in Turn, so in the format "Apr 2, 2030 1:16 PM".

NOTE: If you run the tests for this Repo, you will need to specify the name of a line and a receiving number to test with details in `turn_config.json`.

## Use

This package currently supports sending text and media messages as well as obtaining a new API key from Turn.io. The following methods are implemented:

* Obtaining a new auth token
* Sending a text message
* Saving a media file
* Sending a media message
* Managing claims on a number
* More to come soon!

Details are in the comments in the code itself.

## Testing

You can run the test suite for this repo at any time if you have pytest installed. Not that the API interactions have been recorded with pytest-vcr. To re-run them you will need to delete or rename the `test/cassettes` folder. Note that test messages will not be sent unless the `test_number` specified in `turn_config.json` has an active conversation window. A new window can be opened by messaging something to the `test_line` from a device using `test_number`. It is recommended that one messages `test_number` first before running the test suite if new cassettes are to be recorded.

## Involvement

Please assist in improving this project! Please open issues, send PRs and suggestions welcome.
