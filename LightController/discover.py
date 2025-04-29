import ssdpy

def discover_ssdp():
    devices = ssdpy.discover()
    for device in devices:
        print(f"Found device: {device}")

discover_ssdp()
