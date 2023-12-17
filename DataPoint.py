from __future__ import annotations

from dataclasses import dataclass, field

import CONFIG
from CONFIG import PRIORITY_DEFAULT, get_time_key, create_time_list
from Enums import JobConstraint, JobStatus, ObjectiveJob, ObjectiveGeneral, CommField, EcoInfo,\
                  ScheduleSrc, MarketRole, BidStatus

# Datapoints are used inside Tables in Queues and always keyed by their 'my_id'

# class for all employer datapoints
@dataclass
class DataPoint:
    my_id: str = "DefaultDataPoint"
    priority: int = PRIORITY_DEFAULT

    def __post_init__(self):
        self._my_id = self.my_id
        if not isinstance(self.my_id, str):
            raise ValueError('value not a string')

    @property
    def my_id(self):
        return self._my_id

    @my_id.setter
    def my_id(self, value):
        self._my_id = value


# class for a single job_id entry
@dataclass
class JobDataPoint(DataPoint):
    constraints: dict = field(default_factory=dict)
    objectives: list[ObjectiveJob] = field(default_factory=list)
    status: JobStatus = JobStatus.ENERGY_NEEDED

    # TODO: implement naming lists in CONFIG
    @property
    def time_ready(self):
        return self.constraints[JobConstraint.TIME_READY]

    @property
    def time_deadline(self):
        return self.constraints[JobConstraint.TIME_DEADLINE]

    @property
    def time_processing(self):
        return self.constraints[JobConstraint.TIME_PROCESSING]

    @property
    def energy_demand(self):
        return self.constraints[JobConstraint.ENERGY_DEMAND]

    # @property
    # def objectives(self):
    #     return self.objectives


# class for estimated list of prices
# this is used for estimation in employer to FCA agent and ECE
@dataclass
class EstimationDataPoint(DataPoint):
    timestamp: str = get_time_key()  # store the time of estimation
    data_id: str = ""
    time_slots: [str] = field(default_factory=list)
    prices: [float] = field(default_factory=list)
    info_type: EcoInfo = EcoInfo.WHOLESALE

    def __post_init__(self):
        self.my_id = self.timestamp

    # create new EstimationDataPoint based on job_id data_response
    @staticmethod
    def create_from_job(job: JobDataPoint):
        estimation = EstimationDataPoint()
        estimation.priority = job.priority  # priority same as job_id priority
        estimation.time_slots = create_time_list(job.time_ready, job.time_deadline +
                                                 (CONFIG.MARGIN_PRICE_TIME * CONFIG.TIME_INTERVAL_UNIX))
        estimation.prices = [0.0 for i in range(len(estimation.time_slots))]
        estimation.my_id = job.my_id
        return estimation

    @staticmethod
    def create_from_interval(start: int, finish: int):
        estimation = EstimationDataPoint()
        estimation.priority = PRIORITY_DEFAULT
        estimation.time_slots = create_time_list(start, finish +
                                                 (CONFIG.MARGIN_PRICE_TIME * CONFIG.TIME_INTERVAL_UNIX))
        estimation.prices = [0.0 for i in range(len(estimation.time_slots))]
        return estimation

    def get_price(self, time: int):
        index = self.time_slots.index(time)
        return self.prices[index]


# class for a single live agent entry in AgentHandler
# used to shadow offer and agent requests
@dataclass
class Request(DataPoint):
    request_id: str = ""
    source_id: str = ""
    destination_id: str = ""
    data_id: str = ""

    def __post_init__(self):
        if not isinstance(self.request_id, str):
            self.request_id = str(self.request_id)
        self.my_id: str = self.request_id


# class for schedule-slot
@dataclass
class ScheduleSlot:
    job_id: str = ""
    priority: int = CONFIG.PRIORITY_DEFAULT
    time_start: int = 0
    time_finish: int = 0
    cost: float = 0.0
    energy: float = 0.0

    def __str__(self):
        return f"slot: {self.job_id}: [start: {self.time_start}, finish: {self.time_finish}, " \
               f"energy: {self.energy}kWh, cost: {self.cost}] "


# class for Key Performance Indicators
class KPI:
    makespan: float = 0.0
    max_pastdue: float = 0.0
    sum_pastdue: float = 0.0
    num_pastdue: float = 0.0
    num_on_time: float = 0.0
    fraction_on_time: float = 0.0
    priority_job_pastdue: float = 0.0

    # method to relate general-objectives to KPI values
    def value(self, objective: ObjectiveGeneral) -> float:
        value = 0.0

        if objective is ObjectiveGeneral.MAKESPAN:
            value = self.makespan
        elif objective is ObjectiveGeneral.MAX_PASTDUE:
            value = self.max_pastdue
        elif objective is ObjectiveGeneral.SUM_PASTDUE:
            value = self.sum_pastdue

        return value

    def __str__(self):
        return f"Makespan: {self.makespan}, Maximum Past-due: {self.max_pastdue}, Sum Past-due: {self.sum_pastdue}," \
               f" No. Past-Due: {self.num_pastdue}, No. On-time: {self.num_on_time}," \
               f" Frac On-time: {self.fraction_on_time}, No. Priority-job Past-due: {self.priority_job_pastdue}"


# dataclass representing a schedule
@dataclass
class Schedule:
    # save which kind of scheduling created this schedule
    source: ScheduleSrc = ScheduleSrc.NONE
    # save the jobs inside this schedule
    jobs: [str] = field(default_factory=list)
    # total cost for this schedule
    total_cost: float = 0
    # key-performance-indicators
    kpi: KPI = KPI()
    # table of all schedule slots
    table: [ScheduleSlot] = field(default_factory=list)

    def add_slot(self, slot: ScheduleSlot):
        self.table.append(slot)
        self.jobs.append(slot.job_id)
        self.total_cost = sum([slot.cost for slot in self.table])

    def add_entry(self, job_id: str, priority: int, start: int, finish: int, energy: float):
        self.jobs.append(job_id)
        self.total_cost = sum([slot.cost for slot in self.table])

        self.table.append(ScheduleSlot(job_id=job_id, priority=priority, time_start=start, time_finish=finish,
                                       energy=energy))

    def add_cost_entry(self, job_id: str, cost: float):
        # get index of job
        index = self.jobs.index(job_id)
        # add cost entry to job slot
        self.table[index].cost = cost
        # update schedule total cost
        self.total_cost = sum([slot.cost for slot in self.table])

    def get_time_start(self, job):
        index = self.jobs.index(job)
        return self.table[index].time_start

    def get_time_finish(self, job):
        index = self.jobs.index(job)
        return self.table[index].time_finish

    def get_cost(self, job):
        index = self.jobs.index(job)
        return self.table[index].cost

    def get_total_cost(self):
        return self.total_cost

    # method to get the start time in the schedule (start-of-schedule)
    # used for time information needed for offer estimation
    def get_time_first(self):
        return min([slot.time_start for slot in self.table])

    # method to get the latest time in the schedule (end-of-schedule)
    # used for time information needed for offer estimation
    def get_time_last(self):
        return max([slot.time_finish for slot in self.table])

    def __str__(self):
        # create header
        string = f"Schedule {self.source.value}\n"

        # append slots printout
        for slot in self.table:
            string += "\t" + str(slot) + "\n"

        # append costs and kpi
        string += f"\tKPI: {self.kpi}\n"
        string += f"\tTotal cost: {self.total_cost}\n"

        return string


@dataclass
class BidFeedback(DataPoint):
    bid_id: str = ""
    source_id: str = ""
    slot: int = 0
    feedback: BidStatus = BidStatus.NOT_YET
    details: list = field(default_factory=list)

    def __post_init__(self):
        self.my_id = self.bid_id

    def __eq__(self, bid: BidSlot):
        return (self.slot == bid.slot) and (self.source_id == bid.source_id)


# class to encapsulate a bidding object
@dataclass
class BidSlot(BidFeedback):
    source_id: str = ""
    source_data: str = ""
    slot: int = 0
    offer: float = 0.0
    energy: float = 0.0

    def take_feedback(self, bid_fb: BidFeedback):
        if self is bid_fb:
            self.feedback = bid_fb.feedback
        else:
            raise NameError

    def __str__(self):
        return f"{self.slot}: {self.offer}"


# class to encapsulate job bids
@dataclass
class BidJob(DataPoint):
    my_id: str = CONFIG.NAME_BID_JOB + str(0).zfill(CONFIG.NAME_ZERO_FILL)
    job_id: str = ""
    time_start: int = 0
    time_finish: int = 0
    source_entity: str = ""
    source_strategy: str = ""
    source_schedule: ScheduleSrc = ScheduleSrc.NONE
    bid_priority: int = 0
    bids: [BidSlot] = field(default_factory=list)

    def get_bid(self, time: int) -> BidSlot:
        for bid in self.bids:
            if bid.slot == time:
                return bid

    def is_time_inside(self, time: int):
        return any([bid.slot == time for bid in self.bids])

    def bids_from_schedule_slot(self, slot: ScheduleSlot, markup):
        # update time_start and time_finish
        self.time_start = slot.time_start if self.time_start >= -slot.time_start else self.time_start
        self.time_finish = slot.time_finish if self.time_finish <= slot.time_finish else self.time_finish

        # create time_list to generate bid times
        time_list = create_time_list(time_start=slot.time_start, time_end=slot.time_finish)
        # Generate bid per time-slot
        bid_counter = 0
        for index in range(len(time_list)):
            bid_counter += 1
            self.bids.append(BidSlot(bid_id=self.my_id + CONFIG.NAME_BID_SLOT
                                           + str(bid_counter).zfill(CONFIG.NAME_ZERO_FILL),
                                     priority=self.priority,
                                     source_id=self.source_entity, energy=slot.energy, slot=time_list[index],
                                     source_data=self.job_id,
                                     offer=slot.cost + (slot.cost * markup)))

    def __str__(self):
        return f"Job-Bids Job: {self.job_id}\n\tschedule: {self.source_schedule}, priority:{self.priority}," \
               f" start: {self.time_start}, finish: {self.time_finish}\n" +\
               "\t" + " ".join([str(bid) + " " for bid in self.bids])



# class used to save data_response that agent needs to perform its role
@dataclass
class Mayfly(DataPoint):
    request_id: str = ""
    data_id: str = ""

    data: dict = field(default_factory=dict)
    response_data: DataPoint = None
    return_action: callable = None

    def __post_init__(self):
        self.my_id = self.request_id

    def get_response_data(self, agent):
        """get return agent from agent"""
        self.response_data = agent.data_response

    def get_data(self, data_field: CommField):
        """method called by agent to get necessary agent"""
        return self.data[data_field]

    def set_data(self, data_field: CommField, data):
        """method used by creator to set agent parameters"""
        self.data[data_field] = data

    def set_action_return(self, action: callable):
        """set action to be implemented when agent returns with agent"""
        self.return_action = action

    def implement_return_action_arg(self, arg: DataPoint):
        """implement return action with an argument"""
        self.return_action(arg)

    def implement_return_action(self):
        """implement return action with return agent as parameter"""
        self.return_action(self.response_data)

    def create_factory_params(self, time_start: int,
                              time_finish: int, data_type: EcoInfo):
        self.data[CommField.TIME_START] = time_start
        self.data[CommField.TIME_FINISH] = time_finish
        self.data[CommField.ECO_INFO] = data_type
        self.data[CommField.DATA_ID] = self.data_id

    def create_bidding_params(self, bid_id: str, time_slot: int, energy: float, price: float, role: MarketRole):
        self.data[CommField.BID_ID] = bid_id
        self.data_id = bid_id
        self.data[CommField.TIME_SLOT] = time_slot
        self.data[CommField.ENERGY] = energy
        self.data[CommField.PRICE_OFFER] = price
        self.data[CommField.MARKET_ROLE] = role
