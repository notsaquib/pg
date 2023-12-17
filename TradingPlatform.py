# class for the all-encompassing platform XD
import asyncio

import pubsub.pub
from loguru import logger
from pubsub import pub

import CONFIG
from Agent import Agent
from CC import FCC, BCC
from ECE import ECE
from ExternalMarket import ExternalMarket
from Machine import Machine
from AgentHandler import AgentHandler
from PlatformAgentHandler import PlatformAgentHandler
from PlatformEntity import PlatformEntity
from PlatfromHashTable import PlatformHashTable
from PlatformBiddingModule import PlatformBiddingModule


class Platform:
    def __init__(self):
        self.my_id = CONFIG.ID_PLATFORM

        # Agent Handler
        self.agents_handler = PlatformAgentHandler(self)

        # create platform modules
        self.fcc = FCC(self)
        self.ece = ECE(self)
        self.market = PlatformBiddingModule(self)
        self.bcc = self.market.bcc

        # register platform components
        self.ece.register_in_platform()
        self.market.register_in_platform()

        # register communication controllers
        self.fcc.register_in_platform()
        self.bcc.register_in_platform()

        # create registered_entities HashTable
        self.machine_id = 0  # counter for employer IDs
        self.registered_entities = PlatformHashTable()

        # add internal entities to the registered list
        self.registered_entities.insert(self.fcc)
        self.registered_entities.insert(self.ece)
        self.registered_entities.insert(self.market)
        self.registered_entities.insert(self.bcc)

        # count of machines with ready bids
        self.num_machine_bids_ready = 0
        self.num_bids_ready = 0
        # count of market rounds
        self.num_bidding_rounds = 0

        # system time: start with reference timestamp
        self.time_running = CONFIG.REF_TIMESTAMP
        self.time_final = CONFIG.REF_TIMESTAMP

        # subscribe to notification of machine bids status
        pub.subscribe(self.machine_bids_generated, topicName=CONFIG.TOPIC_PLATFORM_NOTIFY_MACHINE_BIDS_GENERATED)
        pub.subscribe(self.machine_bid_ready, topicName=CONFIG.TOPIC_PLATFORM_NOTIFY_MACHINE_BID_READY)

    # run the TradingPlatform from main
    def run(self):
        self.fcc.run()

    # function to to_destination agent to source_id by CC
    def agent_to_source(self, agent: Agent):
        entity = self.registered_entities.find(agent.source_id)
        # entity.receive_agent(agent=agent)
        pub.sendMessage(topicName=entity.topic, agent=agent)

    # function to to_destination agent to destination
    def agent_to_destination(self, agent: Agent):
        entity = self.registered_entities.find(agent.destination_id)
        # entity.receive_agent(agent=agent)
        pub.sendMessage(topicName=entity.topic, agent=agent)

    # function to be called by machines to signal ready for trading
    def machine_bids_generated(self):
        self.num_machine_bids_ready += 1
        logger.info(f"Platform: {self.num_machine_bids_ready} entities ready to next bid")
        # check if number of bids ready is equal to the number of machines
        if self.num_machine_bids_ready >= self.machine_id:
            logger.info(f"Platform: Machines are ready to bid, Market can start")
            # get final bidding time from machines
            self.find_market_final_time()

            self.bidding_round_end()

    # function to be called by bidding module to signal bidding round end
    def bidding_round_end(self):
        # increment bidding rounds counter
        self.num_bidding_rounds += 1
        # reset bid counters
        self.num_machine_bids_ready = 0
        self.num_bids_ready = 0
        # Move to next time slot
        self.time_running += CONFIG.TIME_INTERVAL_UNIX
        # Check if bidding is still not at end time
        if self.time_running <= self.time_final:
            logger.info(f"Platform: bidding round {self.num_bidding_rounds} start")
            self.signal_market_ready()
        else:
            logger.info(f"Platform: bidding concluded after {self.num_bidding_rounds} rounds")

    def machine_bid_ready(self):
        self.num_machine_bids_ready += 1
        logger.info(f"Platform: {self.num_machine_bids_ready} entities ready to bid")
        self.market_bid_received()

    # function called by bidding module to inform about number of bids received
    def market_bid_received(self):
        self.num_bids_ready += 1
        # check if all bids where submitted
        # checks = (num >= self.machine_id + self.external_market_num_bids - 2)
        # checks = self.num_machine_bids_ready + self.num_bids_ready >= self.machine_id + CONFIG.N_JOBS
        checks = self.num_machine_bids_ready >= self.machine_id
        if checks:
            self.market.start_bidding_round()

    # Helper methods

    # used for giving new registered_entities an ID
    def get_machine_id(self, new_machine):
        # generate new entity_id string with formatting
        self.machine_id += 1
        machine_id = CONFIG.NAME_MACHINE + str(self.machine_id).zfill(CONFIG.NAME_ZERO_FILL)

        # set entity_id before inserting into HashTable
        new_machine.my_id = machine_id

        # add as external entity
        self.register_external_entity(entity=new_machine)

        # return entity_id to employer
        return machine_id

    # notify machines that market is ready for bids at a certain time
    def signal_market_ready(self):
        # publish on market-ready topic
        pub.sendMessage(CONFIG.TOPIC_PLATFORM_MARKET_READY)
        # loop over all registered entities
        # for entity in self.registered_entities.values():
        #     # check if entity is a employer or external market
        #     try:
        #         if isinstance(entity.employer, ExternalMarket) or isinstance(entity, AgentHandler):
        #             if not isinstance(entity, PlatformBiddingModule):
        #                 entity.employer.start_bidding_round()
        #     except AttributeError:
        #         pass
        pass

    # function used to find market end time
    def find_market_final_time(self):
        # loop over all registered entities
        for entity in self.registered_entities.values():
            # check if entity is an ExternalMarket
            try:
                if ExternalMarket is type(entity.employer):
                    pass
                # check if entity is a employer
                elif AgentHandler is type(entity):
                    # get employer final time
                    entity_final_time = entity.employer.bidder.get_last_bidding_time()
                    # check and
                    self.time_final = entity_final_time if self.time_final < entity_final_time else self.time_final
            except AttributeError:
                pass

    # function to register external entities in the platform
    def register_external_entity(self, entity: Machine):
        # add to registered_entities table
        self.registered_entities.insert(entity.agents_handler)

