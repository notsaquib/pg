# main employer class
import pubsub.pub
from loguru import logger
from pubsub import pub

# all employer submodules and intelligence happen here
import CONFIG
from Enums import EcoInfo
from DataPoint import Mayfly
from AgentHandler import AgentHandler
from MachineEventListener import MachineEventListener
from MachineRecordKeeper import MachineRecordKeeper
from MachineScheduleGenerator import MachineScheduleGenerator
from MachineStrategyBlock import MachineStrategyBlock
from PlatfromHashTable import PlatformHashTable
from PlatformEntity import PlatformEntity


class Machine(PlatformEntity):
    def __init__(self, platform):
        super().__init__()
        # register platform
        self.platform = platform

        # Declare employer sub-modules
        self.agents_handler = AgentHandler(employer=self, super_topic=CONFIG.TOPIC_SUPER_MACHINES)
        self.events_listener = MachineEventListener(self)
        self.records_keeper = MachineRecordKeeper(self)
        self.scheduler = MachineScheduleGenerator(self)
        self.bidder = MachineStrategyBlock(self)

        # Tables for shadowing agent requests
        self.price_requests_table = PlatformHashTable()

        # request_id count
        self._request_id = 0

        # subscribe to topic that indicates when market is ready
        pub.subscribe(self.start_bidding_round, topicName=CONFIG.TOPIC_PLATFORM_MARKET_READY)

    # event response functions

    # function to respond to job_id addition event
    def on_job_added(self):
        pass

    # function to respond to missing offer estimation event
    def on_missing_estimation(self):
        pass

    # function to respond to offer estimation acquired event
    def on_estimation_acquired(self):
        pass

    def on_estimation_added(self):
        # calculate schedule energy costs using newly acquired info
        self.records_keeper.calculate_all_schedule_energy_costs()
        # evaluate schedules using nominal evaluation
        self.bidder.eval_nominal_schedules()
        # generate bids
        self.bidder.implement_strategy_bidding()

    def on_schedules_generated(self):
        # figure out the missing time-offer information
        # get the earliest and latest time in all schedules
        time_start = min(
            [schedule.get_time_first() for schedule in list(self.records_keeper.schedules_record.values())])
        time_finish = max(
            [schedule.get_time_last() for schedule in list(self.records_keeper.schedules_record.values())])

        price_mayfly = Mayfly(request_id=self.request_id, data_id="ALL_PRICES", priority=CONFIG.PRIORITY_DEFAULT)
        price_mayfly.create_factory_params(time_start=time_start, time_finish=time_finish, data_type=EcoInfo.WHOLESALE)
        price_mayfly.set_action_return(self.records_keeper.add_prices)

        self.agents_handler.request_factory_agent(request_data=price_mayfly)

    # event triggered when bids are generated
    @staticmethod
    def on_bids_generated():
        # notify platform that bids are ready
        pub.sendMessage(topicName=CONFIG.TOPIC_PLATFORM_NOTIFY_MACHINE_BIDS_GENERATED)
        # self.platform.machine_bids_generated()
        pass

    # method called when no more bids available

    # method called when next bidding round is ready
    def start_bidding_round(self):
        # check if bid is available at current time
        time_current = self.platform.time_running
        # inform platform that bids are ready
        # self.platform.machine_bid_ready()
        pub.sendMessage(topicName=CONFIG.TOPIC_PLATFORM_NOTIFY_MACHINE_BID_READY)
        # check if bid exists for current bidding time
        if self.bidder.is_bid_time(time=time_current):
            # log bid submission
            logger.info(self.my_id + f": bid submitted for time: {time_current}")
            # prepare bid agent
            bid_mayfly = self.bidder.get_bid_mayfly(time=time_current, request_id=self.request_id)
            # agent bidding agent
            self.agents_handler.request_bidding_agent(request_data=bid_mayfly)
        else:
            # log no bid submission
            logger.info(self.my_id + f": no bid submitted for time: {time_current}")

    # function to register employer with platform
    def register_in_platform(self):
        self.my_id = self.platform.get_machine_id(self)

        # pass platform (part of self) to agent handler
        self.agents_handler.register_platform_modules(self)

    # Helper Methods

    @property
    def request_id(self):
        self._request_id += 1
        return CONFIG.NAME_REQUEST_MACHINE + str(self._request_id)
