"""
POS Application Configuration.
Loads settings from a JSON config file, falling back to built-in defaults.
"""

import json
import os

_DEFAULT_DATABASE = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "imarapos_db",
}

_DEFAULT_APP = {
    "title": "ImaraPOS",
    "version": "1.0.0",
    "width": 1400,
    "height": 750,
    "theme": "clam",
}

DATABASE = dict(_DEFAULT_DATABASE)
APP = dict(_DEFAULT_APP)


def load_config(config_path: str):
    """Load settings from a JSON config file and update DATABASE / APP globals."""
    global DATABASE, APP

    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        data = json.load(f)

    # Database settings
    db_section = data.get("database", {})
    DATABASE = {
        "host": db_section.get("host", _DEFAULT_DATABASE["host"]),
        "port": int(db_section.get("port", _DEFAULT_DATABASE["port"])),
        "user": db_section.get("username", db_section.get("user", _DEFAULT_DATABASE["user"])),
        "password": db_section.get("password", _DEFAULT_DATABASE["password"]),
        "database": db_section.get("name", db_section.get("database", _DEFAULT_DATABASE["database"])),
    }

    # App metadata
    APP = {
        "title": data.get("appName", _DEFAULT_APP["title"]),
        "version": data.get("appVersion", _DEFAULT_APP["version"]),
        "width": _DEFAULT_APP["width"],
        "height": _DEFAULT_APP["height"],
        "theme": _DEFAULT_APP["theme"],
    }
