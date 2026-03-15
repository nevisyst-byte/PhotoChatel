import os
import json

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "cloud_path": os.path.expanduser("~/Pictures"),
    "delay": 3,
    "autostart": False,
    "resolution": "FullHD",
    "camera_mode": "PiCam",
    "event_name": "",
    "kiosk_mode": False,
    "upload_auto": False
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            settings = DEFAULT_SETTINGS.copy()
    else:
        settings = DEFAULT_SETTINGS.copy()
    return {**DEFAULT_SETTINGS, **settings}  # Merge with defaults

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)
