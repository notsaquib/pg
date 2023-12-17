import random
from abc import ABC
from enum import Enum
from loguru import logger
from pubsub import pub

import CONFIG
from Enums import EcoInfo, MarketRole
from DataPoint import EstimationDataPoint, BidSlot, Mayfly, BidFeedback
from AgentHandler import AgentHandler
from MachineEventListener import MachineEventListener
from PlatformEntity import PlatformEntity


# class for enumerating entries of external market data_response generation
class ExtMarketData(Enum):
    LIST_ENERGY = "LIST_ENERGY"
    TIME_SUPPLY_PERIOD_FINISH = "TIME_SUPPLY_PERIOD_FINISH"


# External market player generation and implementation
class ExternalMarket(PlatformEntity):
    def __init__(self, platform):
        self.my_id = CONFIG.ID_EXTERNAL_MARKET
        self.platform = platform
        self.fcc: PlatformEntity = None
        self.bcc: PlatformEntity = None

        self.suppliers: [Supplier] = []
        self.events_listener = MachineEventListener(self)
        self.agents_handler = AgentHandler(self, super_topic=self.my_id)

        self.data_energy = []
        self.data_supply_period_start = CONFIG.REF_TIMESTAMP
        self.data_supply_period_finish = 0
        self.data_prices: dict = {}  # EstimationDataPoint = None

        # variable to track bidding requests
        self._request_id: int = 0

        # subscribe to topic that indicates when market is ready
        pub.subscribe(self.start_bidding_round, topicName=CONFIG.TOPIC_PLATFORM_MARKET_READY)

    # function to take supplier data_response and generate requests for market estimations
    # determine beginning and end time for energy supply period
    # what distribution of energy supply and related supplier repetitions needed
    def create_suppliers(self, data: dict):
        # save data_response
        self.data_energy = data[ExtMarketData.LIST_ENERGY]
        self.data_supply_period_finish = data[ExtMarketData.TIME_SUPPLY_PERIOD_FINISH] \
                                         + (CONFIG.MARGIN_PRICE_TIME * CONFIG.TIME_INTERVAL_UNIX)

        # retrieve market estimations from ECE
        # create EstimationDataPoint
        request_data = Mayfly(request_id="Supplier_Request", data_id="Supplier_Create")
        request_data.create_factory_params(time_start=self.data_supply_period_start,
                                           time_finish=self.data_supply_period_finish,
                                           data_type=EcoInfo.WHOLESALE)
        request_data.set_action_return(self.add_prices)

        # log data_response data_response
        logger.info("External market offer estimation requested")
        self.agents_handler.request_factory_agent(request_data=request_data)

    # function called by platform to start bidding rounds
    def start_bidding_round(self):
        # check if bid is available at current time
        time_current = self.platform.time_running
        bid_mayflys = []
        # extract bids from each supplier
        for supplier in self.suppliers:
            bids = supplier.get_bids_time(time=time_current)
            bid_mayflys.extend(self.bids_to_mayflys(bids))
        # agent bidding agent for each bid
        for mayfly in bid_mayflys:
            self.agents_handler.request_bidding_agent(request_data=mayfly)
        pass

    # Helper Methods

    # method to convert list of bids to list of mayflys
    def bids_to_mayflys(self, bids: [BidSlot]) -> [Mayfly]:
        mayflys = []
        for bid in bids:
            mayfly = Mayfly(request_id=self.request_id, priority=bid.priority)
            mayfly.create_bidding_params(bid_id=bid.my_id, time_slot=bid.slot, role=MarketRole.SELLER,
                                         energy=bid.energy, price=bid.offer)
            mayfly.set_action_return(self.set_bid_feedback)
            mayflys.append(mayfly)
        return mayflys

    # function to callback when bid returns
    def set_bid_feedback(self, bid_fb: BidFeedback):
        for supplier in self.suppliers:
            for bid in supplier.bids:
                if bid_fb is bid:
                    bid.see_market_results(bid_fb)

    # method to add acquired prices using EstimationDatapoints
    def add_prices(self, estimates: EstimationDataPoint):
        self.data_prices = {estimates.time_slots[i]: estimates.prices[i] for i in range(len(estimates.prices))}

        self.on_estimation_acquired()

    # function to generate a supplier based on data_response from the data_response generator
    def on_estimation_acquired(self):
        # log data_response data_response fulfillment
        logger.info("External market: Estimations acquired")

        # create suppliers based on energy
        # each supplier provides energy at all the time slots for a given energy
        # offer offers by each supplier vary on around +-5% by supplier
        for i in range(len(self.data_energy)):
            # create supplier with unique_id
            margin = round(random.uniform(CONFIG.PRICE_SUPPLY_MARGIN_MIN, CONFIG.PRICE_SUPPLY_MARGIN_MAX), 4)
            supplier = Supplier(market=self, energy=self.data_energy[i], margin=margin)
            supplier.register_with_external_market(my_id=CONFIG.NAME_SUPPLIER + str(i + 1).zfill(CONFIG.NAME_ZERO_FILL))
            self.suppliers.append(supplier)

            # loop for bid generation in supplier
            for j in range(len(self.data_prices.keys())):
                supplier.add_bid(time=list(self.data_prices.keys())[j], price=list(self.data_prices.values())[j])
                pass

    # register related services
    def register_in_platform(self):
        self.platform.register_external_entity(self)
        self.fcc = self.platform.fcc
        self.bcc = self.platform.bcc
        self.agents_handler.register_platform_modules(self)

    @property
    def request_id(self):
        self._request_id += 1
        return CONFIG.NAME_REQUEST_EXT_MARKET + str(self._request_id)


# class for suppliers
class Supplier:
    def __init__(self, market, energy, margin):
        self.my_id = CONFIG.NAME_SUPPLIER + str(0).zfill(CONFIG.NAME_ZERO_FILL)
        self.market = market
        self.energy = energy
        self.pricing = 1 + margin  # deviation from nominal pricing
        # self.time_generation: ScheduleSlot = None  # supply availability time in a day
        self.bids: [BidSlot] = []
        self.bid_counter = 0

    # function to get bids at certain time
    def get_bids_time(self, time: int):
        bids = []
        for bid in self.bids:
            if bid.slot == time:
                bids.append(bid)
        return bids

    def add_bid(self, time, price):
        self.bid_counter += 1
        self.bids.append(BidSlot(bid_id=self.my_id + CONFIG.NAME_BID_SLOT + str(self.bid_counter),
                                 priority=CONFIG.PRIORITY_DEFAULT,
                                 source_id=self.my_id, energy=self.energy, slot=time,
                                 offer=price * self.pricing))

    # register useful components of the external markets
    def register_with_external_market(self, my_id: str):
        self.my_id = my_id
