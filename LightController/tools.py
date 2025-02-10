import subprocess
import os
import json
import re
from config import devices_file

# Function to load devices from the JSON file
def load_devices():
    if os.path.exists(devices_file):
        with open(devices_file, "r") as f:
            try:
                os.fsync(f.fileno())  # Force sync with disk
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


# Function to save devices back to the JSON file
def save_devices(devices):
    with open(devices_file, "w") as f:
        json.dump(devices, f, indent=4)


# Function to get MAC address of a device
def get_mac_address(ip):
    try:
        result = subprocess.run(["/usr/sbin/arp", "-n", ip], capture_output=True, text=True)
        match = re.search(
            r"([0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})",
            result.stdout)
        return match.group(1) if match else None
    except Exception:
        return None


# Function to ping a device
def ping_device(ip):
    try:
        result = subprocess.run(["ping", "-c", "1", "-W", "1", ip], stdout=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception:
        return False
