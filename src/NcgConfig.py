"""
Configuration singleton
"""

import yaml

from AppLogger import get_logger

class NcgConfig(object):
    _instance = None
    config = {}

    def __new__(cls, configFile):
        logger = get_logger()

        if cls._instance is None:
            logger.info(f"Reading configuration from {configFile}")
            cls._instance = super(cls, NcgConfig).__new__(cls)

            with open(configFile, "r") as cfgFile:
                cls.config = yaml.safe_load(cfgFile)

        return cls._instance