"""
Configuration singleton
"""

import toml


class NcgConfig(object):
    _instance = None
    config = {}

    def __new__(cls,configFile):
        if cls._instance is None:
            print(f'Reading configuration from {configFile}')
            cls._instance = super(cls, NcgConfig).__new__(cls)

            with open(configFile) as cfgFile:
                cls.config = toml.load(cfgFile)

        return cls._instance
