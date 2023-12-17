from __future__ import annotations

from enum import Enum


# Job Datapoint fields
class JobRecField(Enum):
    JOB_ID = "JOB_ID"
    PRIORITY = "PRIORITY"
    STATUS = "STATUS"
    DATA = "DATA"


# Job constraints
class JobConstraint(Enum):
    TIME_READY = 'TIME_READY'
    TIME_DEADLINE = 'TIME_DEADLINE'
    TIME_PROCESSING = 'TIME_PROCESSING'
    ENERGY_DEMAND = 'ENERGY_DEMAND'


# job_id status enumeration
class JobStatus(Enum):
    ENERGY_NEEDED = "ENERGY_NEEDED"
    ENERGY_RESERVED = "ENERGY_RESERVED"


# objectives (minimize) for job
class ObjectiveJob(Enum):
    COST = "COST"
    EARLY = "EARLY"
    NO_TARDY = "NON_TARDY"


# objectives (minimize) for employer/strategies
class ObjectiveGeneral(Enum):
    MAKESPAN = "MAKESPAN"
    MAX_PASTDUE = "MAX_PASTDUE"
    SUM_PASTDUE = "SUM_PASTDUE"
    NUM_PASTDUE = "NUM_PASTDUE"
    COST = "COST"


# enumeration of objectives eval_profile method
# use only one type of prefix
class ObjectiveEval(Enum):
    GENERAL_SELECTIVE = "SELECTIVE"  # consider only specified objectives
    GENERAL_COMPREHENSIVE = "GENERAL_COMPREHENSIVE"  # consider all objectives with emphasis on specified objectives
    JOB_INCLUSIVE = "JOB_INCLUSIVE"  # include job objective as addition to general objective eval_profile
    JOB_EXCLUSIVE = "JOB_EXCLUSIVE"  # job objective eval_profile separate from general objective eval_profile
    PRIORITY_LINEAR = "PRIORITY_LINEAR"  # increasing priority increases weight linearly
    PRIORITY_EXPONENTIAL = "PRIORITY_EXPONENTIAL"  # increasing priority increases weight with exponentially
    PRIORITY_FACTORIAL = "PRIORITY_FACTORIAL"  # increasing weight priority increases weight by weight-factorial


class CommField(Enum):
    DATA_ID = "DATA_ID"
    TIME_START = "TIME_START"
    TIME_FINISH = "TIME_FINISH"
    ECO_INFO = "ECO_INFO"
    BID_ID = "BID_ID"
    TIME_SLOT = "TIME_SLOT"
    ENERGY = "ENERGY"
    PRICE_OFFER = "PRICE_OFFER"
    MARKET_ROLE = "MARKET_ROLE"

    @staticmethod
    def factory():
        return [CommField.DATA_ID, CommField.TIME_START, CommField.TIME_FINISH, CommField.ECO_INFO]

    @staticmethod
    def bidding():
        return [CommField.BID_ID, CommField.TIME_SLOT, CommField.ENERGY, CommField.PRICE_OFFER, CommField.MARKET_ROLE]


# Enum to represent the type of information that can be taken from the ECE
class EcoInfo(Enum):
    WHOLESALE = 4169  # 4169: Wholesale market offer for region DE-LU
    OVERALL_GEN = 122  # 122:  Forecasted overall generation
    RENEWABLE_GEN = 5097  # 5097: Forecasted renewable generation
    CONVENTIONAL_GEN = 715  # 715:  Forecasted conventional generation


# The role of the bid issuer
class MarketRole(Enum):
    BUYER = True
    SELLER = False
    # values follow the pyMarket convention


# The status of the bid placed
class BidStatus(Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    NOT_YET = "NOT_YET"
    NO_TAKERS = "NO_TAKERS"


class ScheduleSrc(Enum):
    FIFO = 'FIFO'  # First-in, First-out
    EDD = 'EDD'  # Earliest due-date first
    LIFO = 'LIFO'  # Last-in, First-out
    SPT = 'SPT'  # Shortest processing-time
    PYOMO_MAKESPAN = 'PYOMO_MAKESPAN'  # Pyomo obj: makespan
    PYOMO_EARLY = 'PYOMO_EARLY'  # Pyomo obj: early
    PYOMO_PD = 'PYOMO_PD'  # Pyomo obj: past-due
    COST_MIN = 'COST_MIN'  # Cost minimization recursive scheduling
    NONE = 'NONE'  # source_id not specified
