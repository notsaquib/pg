# class for temporary ECE
import pubsub.pub
from loguru import logger
from pubsub import pub

import CONFIG
from Enums import CommField
from Agent import Drone
from DataPoint import EstimationDataPoint
from PlatformEntity import Service
import smard_de


class ECE(Service):
    def __init__(self, platform):
        # constants used to identify module
        self.logging_key_word = "estimation"
        self.service_id = CONFIG.NAME_REQUEST_ESTIMATION
        super().__init__(platform=platform, my_id=CONFIG.ID_ECE)

        self.topic = CONFIG.TOPIC_ECE

        # create table ECE table
        self.price_estimates = {}

    def execute_service(self, data_drone: Drone):
        self.get_estimates(data_drone=data_drone)

    # execute service for each service_to_start
    def on_new_request(self):
        while not self.services_to_start.is_empty():
            # get data_drone from to-start queue
            service_drone = self.services_to_start.get()
            # put agent drone in in-progress table
            self.services_in_progress.insert(service_drone)
            # execute service on agent
            self.execute_service(data_drone=service_drone)

    # Get estimates from sources
    def get_estimates(self, data_drone: Drone):
        # return agent is EstimationDatapoint
        data = EstimationDataPoint.create_from_interval(start=data_drone.data_to_find[CommField.TIME_START],
                                                        finish=data_drone.data_to_find[CommField.TIME_FINISH])
        data.data_id = data_drone.data_id
        data.priority = data_drone.priority
        # timestamp when estimation data_response was generated
        data.timestamp = CONFIG.get_time_key()

        # get agent for each time slot
        for slot in data.time_slots:
            week_stamp = smard_de.smard_timestamp(slot)
            # check whether data_response for needed timeslots has already been requested
            if week_stamp in self.price_estimates:
                pass
            else:
                # logging
                logger.info(self.my_id + ' ' + f'requesting data from smard.de for timestamp {week_stamp}')
                # data_response prices from smard
                self.price_estimates[week_stamp] = \
                    smard_de.get_wholesale_prices(week_stamp)  # data_drone.data_to_find[CommField.ECO_INFO].value)

            # check if timeslot has data_response available
            if slot in self.price_estimates[week_stamp]:
                # insert data_response according to current period into prices list with same index
                data.prices[data.time_slots.index(slot)] = self.price_estimates[week_stamp][slot]
            else:
                # logging
                logger.info(self.my_id + ' ' + f'cannot provide data for timestamp {slot}')

        # save new estimation in data_drone
        data_drone.data_response = data

        # remove data_drone from in-progress table
        self.services_in_progress.remove(data_drone.my_id)

        # put data_drone in completed queue
        self.services_completed.put(data_drone)

        # trigger completed-estimation event
        self.on_service_completed()

    def register_in_platform(self):
        self.cc = self.platform.fcc
        pub.subscribe(self.receive_agent, topicName=self.topic)
