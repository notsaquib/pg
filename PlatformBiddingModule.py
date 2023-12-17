from __future__ import annotations

from enum import Enum
import numpy as np
import pandas as pd
import pymarket as pm
from pandas import DataFrame
from loguru import logger
from pubsub import pub

import CONFIG
import TradingPlatform
from Agent import Drone
from CC import BCC
from DataPoint import BidFeedback
from Enums import CommField, MarketRole, BidStatus
from PlatformEntity import Service


# Enum to represent the market type used
class MarketType(Enum):
    P2P = 'p2p'
    HUANG = 'huang'
    MUDA = 'MUDA'


# some of the market types supported by pyMarket


class PlatformBiddingModule(Service):
    def __init__(self, platform: TradingPlatform):
        # constants used to identify module
        self.logging_key_word = "round"
        self.service_id = CONFIG.NAME_ROUND_BIDDING

        super().__init__(my_id=CONFIG.ID_MARKET, platform=platform)
        self.bcc = BCC(platform)
        self.cc = self.bcc
        self.markets: dict = {}
        self.topic = CONFIG.TOPIC_MARKET

        # user id that is unique for every bid source
        self._user_id = 1
        self.user_dict = {}

    # execute service for each service_to_start
    def on_new_request(self):
        logger.info(self.my_id + f": bid received for time: {self.platform.time_running}")
        self.platform.market_bid_received()  # num=self.services_to_start.size())

    # method to trigger bidding round
    def start_bidding_round(self):
        # create market module
        market = pm.Market()
        self.markets[self.platform.time_running] = market

        #
        while not self.services_to_start.is_empty():
            # get data_drone from to-start queue
            bid_drone = self.services_to_start.get()
            # put agent drone in in-progress table
            self.services_in_progress.insert(bid_drone)
            # add new bid to market_round
            self.add_bid(market=market, bid_drone=bid_drone)

        pass
        # execute market
        transactions, _ = market.run(MarketType.P2P.value)  # , np.random.RandomState(1234))
        # log market
        if transactions.get_df().empty:
            # log no trading
            logger.info(f"Market: No trade, time {self.platform.time_running}")
        else:
            # log trading
            logger.info(f"Market: Trade, time {self.platform.time_running}")
        # extract results to send back
        self.extract_results(market=market)
        # save market
        self.markets[self.platform.time_running] = market
        # purge user dictionary to avoid getting too large
        self.user_dict.clear()
        # send agents with results
        self.on_service_completed()
        # signal to platform that round ended
        self.platform.bidding_round_end()
        pass

    def extract_results(self, market: pm.Market):
        # get market results
        output = market.transactions.get_df()
        # rekey agent to use source for easier access
        output.set_index(keys=output['source'], inplace=True)
        details = []  # list to store information if bid was split
        # set response agent for each drone
        for drone in self.services_in_progress.values():
            # check if result is empty due to no transactions
            if output.empty:
                feedback = BidStatus.NO_TAKERS
            else:
                # extract agent entry related to drone
                result = output['active'].get(key=self.user_dict[drone.data_id])
                # check if feedback is a panda Series instead of simple boolean
                if pd.Series is type(result):
                    # extract all entries related and parse
                    result_data = self.parse_bid_result(output[['quantity', 'active']]
                                                        .loc[self.user_dict[drone.data_id]])
                    # save details as a list of tuples
                    details = [tuple(entry) for entry in result_data.to_numpy()]
                    # if any of the bid splits where accepted, then feedback is ACCEPTED
                    if any(entry is BidStatus.ACCEPTED for entry in [result_data['active'].to_numpy()]):
                        feedback = BidStatus.ACCEPTED
                    else:
                        feedback = BidStatus.REJECTED
                else:
                    feedback = self.parse_bid_result(result)
                # create BidFeedback object for agent response
            response_data = BidFeedback(my_id=drone.data_id, source_id=drone.source_id,
                                        slot=drone.data_to_find[CommField.TIME_SLOT],
                                        feedback=feedback, details=details)
            drone.data_response = response_data
            self.services_in_progress.remove(drone.my_id)
            self.services_completed.put(drone)

    def add_bid(self, market: pm.Market, bid_drone: Drone):
        # extract agent from drone to create bid
        user_str = bid_drone.data_to_find[CommField.BID_ID]
        quantity = bid_drone.data_to_find[CommField.ENERGY]
        price = bid_drone.data_to_find[CommField.PRICE_OFFER]
        role = bid_drone.data_to_find[CommField.MARKET_ROLE].value
        time = 0
        if role is MarketRole.BUYER:
            divisible = False
        else:
            divisible = True

        # save user_id, market user are integers not strings
        user = self.user_id
        self.user_dict[user_str] = user

        # add bid
        market.bm.add_bid(quantity=int(quantity), price=round(price, 2), user=user, buying=role,
                          time=time, divisible=divisible)

    @staticmethod
    def parse_bid_result(data):
        """" function to parse transaction result
             if transaction 'active' is true then bid was rejected and vice, versa """""
        parsed_data = data
        # if agent is a pandas DataFrame parse each entry
        if isinstance(data, pd.DataFrame):
            parsed_data['active'] = np.where(data['active'], BidStatus.REJECTED, BidStatus.ACCEPTED)
        else:  # directly parse boolean values
            parsed_data = BidStatus.REJECTED if data else BidStatus.ACCEPTED
        return parsed_data

    @property
    def user_id(self) -> int:
        self._user_id += 1
        return self._user_id

    def register_in_platform(self):
        pub.subscribe(self.receive_agent, topicName=self.topic)
