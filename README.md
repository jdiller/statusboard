# Status Board Image Generator
For kicks I'm building a small personal status board out of an ESP32 and an e-Ink display. It will run off a battery and be stuffed into a picture frame, all going well.

To reduce the amount of work it needs to do, and because it has a teeny tiny amount of ram, this is a flask app that runs on a server and composes the image for it to display. 

The server makes various api calls and composes a black and white image which is then packed into a 1-bit-per-pixel byte array that can be fetched by the ESP32 via polling. 
