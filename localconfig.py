import os
import sys

from configparser import ConfigParser
def get_config() -> ConfigParser:
    config = ConfigParser()
    # repo defaults
    config.read(os.path.join(sys.path[0], 'config.ini'))
    return config


