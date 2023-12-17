# Configuration file
# imports
from __future__ import annotations

from datetime import datetime
from inputimeout import TimeoutOccurred
from configparser import ConfigParser
import numpy as np

from CONFIG_PROFILES import ConfigProfile, SimParam
from Enums import JobRecField, JobConstraint, JobStatus, ObjectiveJob, ObjectiveGeneral, ObjectiveEval, EcoInfo

# Read simulation parameters from a config.ini
config_sim = ConfigParser()
config_sim.read('CONFIG_PROFILES.ini')

# take input about chosen test profile
try:
    # test_profile = inputimeout(prompt=f'Choose test profile({list(ConfigProfile.__dict__.values())[1:4]}): ', timeout=5)
    test_profile = input(f'Choose test profile({list(ConfigProfile.__dict__.values())[1:4]}): ')
    sim_profile = config_sim[test_profile]
except (TimeoutOccurred, KeyError):
    test_profile = ConfigProfile.TEST
    sim_profile = config_sim[test_profile]

print(f'Running profile: {test_profile}')

# Simulation Parameters
N_MACHINES = int(sim_profile[SimParam.NUM_MACHINES])
N_JOBS = int(sim_profile[SimParam.NUM_JOBS])
REF_DATETIME = str(sim_profile[SimParam.TIME_REF])
N_AGENTS = int(sim_profile[SimParam.NUM_AGENTS])  # Maximum number of agents created per Platform
N_SUPPLIERS = N_MACHINES
WEIGHT_OBJECTIVE_SPECIFIED = 10  # emphasis weight for specified objectives vs unspecified ones
DEFAULT_BIDDING_MARKUP = 1  # in %
N_BIDS_DEFAULT = 1  # number of bids that can be submitted by a employer for a single time-slot
FACTOR_AGENTS_MIN = 0.1  # fraction of agents that are deployed before a market round is triggered
N_AGENTS_MIN = 1 if int(N_AGENTS * FACTOR_AGENTS_MIN) <= 0 else int(N_AGENTS * FACTOR_AGENTS_MIN)
DEFAULT_ECO_INFO = EcoInfo.WHOLESALE
N_INITIAL_CAPACITY = N_JOBS * 20  # Initial number of buckets in all the HashTables and Queues

# Priority
# number of priority levels including zero. The lower priority value, the higher the priority.
PRIORITY_LEVELS = 3
# Default priority level
PRIORITY_DEFAULT = PRIORITY_LEVELS - 1  # Default priority is the lowest priority
PRIORITY_WEIGHT_NOMINAL = 1  # additional weight factored over the profile-calculated weight (see PriorityProfile)
# PRIORITY_PROFILE = PriorityProfile.EXPONENTIAL (see below)

# Supplier Parameters
PRICE_SUPPLY_MARGIN_MAX = 0.05  # maximum margin over ECE data_response that a supplier can charge
PRICE_SUPPLY_MARGIN_MIN = -0.05  # minimum margin below ECE data_response that a supplier can charge

# constants
# PlatformEntity IDs
ID_ECE = "ECE"
ID_FCC = "FCC"
ID_BCC = "BCC"
ID_MARKET = "BiddingModule"  # name of bidding module
ID_PLATFORM = "Platform"
ID_EXTERNAL_MARKET = "ExternalMarket"  # Energy suppliers module name

# Naming conventions
NAME_REQUEST_ESTIMATION = "RE"
NAME_REQUEST_MACHINE = "RM"
NAME_REQUEST_EXT_MARKET = "RK"
NAME_ROUND_BIDDING = "BR"
NAME_MACHINE = "M"
NAME_AGENT = "A"
NAME_JOB = "J"
NAME_SUPPLIER = "S"
NAME_BID_SLOT = "BS"
NAME_BID_JOB = "BJ"
NAME_PLATFORM_ENTITY = "PE"
NAME_STRATEGY_EVALUATION = "SE"
NAME_STRATEGY_BIDDING = "SB"
NAME_ZERO_FILL = int(np.log10(N_JOBS)) + 3 if N_JOBS >= N_MACHINES else int(np.log10(N_MACHINES)) + 3

# Time Parameters
TIME_KEY_FORMAT = "%Y%m%d%H%M%S%f"  # Formatting datetime instances
TIME_INTERVAL = 60  # time slot size in minutes
TIME_INTERVAL_UNIX = 60 * TIME_INTERVAL
TIME_INT_INTERVAL = 60  # every increment by 1-integer converted to minutes e.g. 60 mins in 1 (deprecated)
TIME_RELEASE_MAX = 50  # in units of TIME_INT_INTERVAL
TIME_DEADLINE_MAX = 100  # in units of TIME_INT_INTERVAL
REF_TIMESTAMP = int(datetime.strptime(REF_DATETIME, TIME_KEY_FORMAT).timestamp())
JOB_ENERGY_MIN = 50  # in kWh
JOB_ENERGY_MAX = 200  # in kWh
MARGIN_PRICE_TIME = 24  # in units of TIME_INT_INTERVAL used for extra offer info after job_id due-time

# Commmunication Topics
TOPIC_PLATFORM = ID_PLATFORM
TOPIC_SEPARATOR = "."
TOPIC_PLATFORM_SUPER = TOPIC_PLATFORM + TOPIC_SEPARATOR
TOPIC_SUPER_MACHINES = "Machines"
TOPIC_FCC = TOPIC_PLATFORM + TOPIC_SEPARATOR + ID_FCC
TOPIC_BCC = TOPIC_PLATFORM + TOPIC_SEPARATOR + ID_BCC
TOPIC_EXTERNAL_MARKET = ID_EXTERNAL_MARKET
TOPIC_ECE = TOPIC_PLATFORM + TOPIC_SEPARATOR + ID_ECE
TOPIC_MARKET = TOPIC_PLATFORM + TOPIC_SEPARATOR + ID_MARKET
TOPIC_PLATFORM_NOTIFY_MACHINE_BIDS_GENERATED = TOPIC_PLATFORM_SUPER + "MACHINE_BIDS_GENERATED"
TOPIC_PLATFORM_NOTIFY_MACHINE_BID_READY = TOPIC_PLATFORM_SUPER + "MACHINE_BID_READY"
TOPIC_PLATFORM_MARKET_READY = TOPIC_PLATFORM_SUPER + "MARKET_READY"
TOPIC_CC_CHECK_REQUESTS_QUEUE = "CC." + "Check_Requests_Queue"

LIST_JOB_RECORD_FIELDS = list(JobRecField)

# Dict of nominal objectives weights before specialization
DICT_WEIGHTS_JOB_NOMINAL = {ObjectiveJob.COST: 1, ObjectiveJob.EARLY: 20, ObjectiveJob.NO_TARDY: 20}
DICT_WEIGHTS_GENERAL_NOMINAL = {ObjectiveGeneral.COST: 1, ObjectiveGeneral.MAKESPAN: 10,
                                ObjectiveGeneral.MAX_PASTDUE: 10, ObjectiveGeneral.SUM_PASTDUE: 10,
                                ObjectiveGeneral.NUM_PASTDUE: 20}
DICT_WEIGHTS_NOMINAL = DICT_WEIGHTS_GENERAL_NOMINAL
DICT_WEIGHTS_NOMINAL.update(DICT_WEIGHTS_JOB_NOMINAL)

# Evaluation profile to be used
LIST_EVALUATION_PROFILE = [ObjectiveEval.GENERAL_COMPREHENSIVE, ObjectiveEval.JOB_INCLUSIVE,
                           ObjectiveEval.PRIORITY_EXPONENTIAL]

# list of all possible objectives
LIST_JOB_OBJECTIVES_ALL = list(ObjectiveJob)
LIST_GENERAL_OBJECTIVES_ALL = list(ObjectiveGeneral)

# Job Price estimation fields
LIST_PRICE_ESTIMATION = ['PERIOD_START', 'TIMESTAMP/PRICE']

# Useful Methods

# Function to return current time for key generation
def get_time_key():
    now = datetime.now()
    return now.strftime(TIME_KEY_FORMAT)


# Function to convert time integer from time string
def time_str_to_int(time_string: str):
    # convert relevant times to datetime instances
    ref_time = datetime.strptime(REF_DATETIME, TIME_KEY_FORMAT)
    time = datetime.strptime(time_string, TIME_KEY_FORMAT)

    # calculate time difference and get timedelta instance
    time_delta = time - ref_time

    # convert timedelta instance to integer value
    time_int = int((time_delta.total_seconds() / 60) / TIME_INT_INTERVAL)

    return time_int


# Function to create list of times between time and end time using TIME_INTERVAL
def create_time_list(time_start, time_end):
    time_list = []

    delta_intervals = int((time_end - time_start) / TIME_INTERVAL_UNIX)
    for i in range(delta_intervals):
        time_list.append(time_start + (i * TIME_INTERVAL_UNIX))
    return time_list


print('CONFIG imported')
