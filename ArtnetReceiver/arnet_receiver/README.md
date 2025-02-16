# Artnet Receiver
The artnet receiver is based on an ESP32. Please connect to any WS2812b light strip and flash the software on your ESP

## Setup
Connect ground and VCC (external power supply necesary for longer strips, otherwise your ESP32 will be grilled!)
Data Pin is set to GPIO 12 (you can change it in the code, but for consistency, I recommend using the same pin for all controllers and setups)

## Installation
Compile and flash the .ino file (after installing the dependencies), the controller will boot automatically and contact the server to receive it's configuration (rows and columns)

### Config
The config for each ESP32 module is stored in the LightController (server). This is especially important for rows and columns identification of a light system.
So we are sending and receiving the right amount of artnet packages and universes and automatic light control generation. Further information can be found in the .py code.
