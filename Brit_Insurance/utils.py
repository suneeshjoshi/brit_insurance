import configparser
import os

CONFIG_INI_FILE = 'config.ini'
CONFIG_DIRECTORY = 'config'


def get_config():
    """
    Reads configuration values from 'config.ini'.

    Returns:
        configparser.ConfigParser: Object with configuration values.
    """
    config_dir = os.path.join(os.path.dirname(__file__), CONFIG_DIRECTORY)
    config_path = os.path.join(config_dir, CONFIG_INI_FILE)
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def get_token(token: str):
    """
    Extracts token from a string.

    Args:
        token (str): String with key-value pairs separated by '='.

    Returns:
        str: Extracted token.
    """
    tokenset = set((token.split("=")))
    if "token" in tokenset:
        tokenset.remove("token")
    return tokenset.pop()
