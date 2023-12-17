from enum import Enum
from configparser import ConfigParser


# SIM_PARAM =

class ConfigProfile():
    TEST = 'TEST'
    TEST_LONG = 'LONG'
    CUSTOM = 'CUSTOM'


class SimParam():
    TIME_REF = 'TIME_REF'
    NUM_MACHINES = 'NUM_MACHINES'
    NUM_JOBS = 'NUM_JOBS'
    NUM_AGENTS = 'NUM_AGENTS'


config = ConfigParser()

config[ConfigProfile.CUSTOM] = {
    'TIME_REF': '20230109100000000000',
    'NUM_JOBS': 20,
    'NUM_MACHINES': 6,
    'NUM_AGENTS': 3
}

config[ConfigProfile.TEST] = {
    'TIME_REF': '20230109100000000000',
    'NUM_JOBS': 10,
    'NUM_MACHINES': 2,
    'NUM_AGENTS': 5
}

config[ConfigProfile.TEST_LONG] = {
    'TIME_REF': '20230109100000000000',
    'NUM_JOBS': 150,
    'NUM_MACHINES': 20,
    'NUM_AGENTS': 50
}

with open('CONFIG_PROFILES.ini', 'w') as file:
    config.write(file)
