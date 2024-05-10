### TurnPy

A package to help you connect to the [Turn.io](https://whatsapp.turn.io/docs/category/turn-api) API from a Python app.

## Setup

Make a copy of the `turn_config.json.example` file and rename to `turn_config.json`. Then for each of your turn lines, fill in the key details and the expiry date for that line. The date should be saved in the `turn_config.json` file exactly as shown in Turn, so in the format "Apr 2, 2030 1:16 PM".

## Use

This package currently supports sending text and media messages as well as obtaining a new API key from Turn.io. The following methods are implemented:

* Obtaining a new auth token
* Sending a text message
* Saving a media file
* Sending a media message
* Determining if another process has a claim on a number (if a number is claimed you will not be able to sent text messages to it from the API).
