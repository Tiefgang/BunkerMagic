# Light Controller
The light controller consists of a banana pi zero with WiFi, Touchscreen, USB-Ports for e.g. Midi interfaces (touchpad light control), an Audio interface (if still necesary)...
It provides several functionalities which are explained below:

## Light Control using QLC+ (currently)

## Server and setup utility
Change configurations of light panels (ESP32, see ArtnetReceiver) that will be automatically received by each ESP32 on startup.
The configs are tracked with each device's MAC address, to be independent of network settings for DHCP leases, only the server needs to have
a fixed address or domain. This can be circumvented using zeroconf or ssdp in the future (didnt get it running yet)

## ideas
- dj set recording
- forward functionality for multiple control panels
- beamer control
- pissetonne fuellstand
- ...
