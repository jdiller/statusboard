# Status Board Image Generator
For kicks I'm building a small personal status board out of an ESP32 and an e-Ink display. It will run off a battery and be stuffed into a picture frame, all going well.

To reduce the amount of work it needs to do, and because it has a teeny tiny amount of ram, this is a flask app that runs on a server and composes the image for it to display.

The server makes various api calls and composes a black and white image which is then packed into a 1-bit-per-pixel byte array that can be fetched by the ESP32 via polling.

## Authentication
All endpoints except the health check endpoint (`/`) require Bearer token authentication. To authenticate:

1. Set a secure token in your `config.ini` file under the `[security]` section.
2. Include an `Authorization` header with your requests in the format: `Bearer your-token-here`.

Example:
```
curl -H "Authorization: Bearer your-token-here" http://localhost:5000/statusboard
```
