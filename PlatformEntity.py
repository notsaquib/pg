# class for Platform entities
from abc import abstractmethod

from loguru import logger
from pubsub import pub

from Agent import Agent, Drone
import CONFIG
from CC import CC
from DataPoint import Request
from PlatformQueue import PlatformQueue
from PlatfromHashTable import PlatformHashTable


class PlatformEntity:
    def __init__(self, my_id=CONFIG.NAME_PLATFORM_ENTITY + str(0).zfill(CONFIG.NAME_ZERO_FILL)):
        self._my_id = my_id

    # functions to handle receiving agent

    # function called by platform
    def receive_agent(self, agent: Agent):
        # check agent source_id, if same then it is granted by a agent
        if agent.source_id is self.my_id:
            self.handle_agent_granted(agent=agent)
        else:
            # agent is returning with a response to employer or requesting a service from a service
            self.handle_agent_returned(agent=agent)

    @abstractmethod
    def handle_agent_granted(self, agent: Agent):
        """handle agent granted by agent"""
        raise NotImplementedError

    @abstractmethod
    def handle_agent_returned(self, agent: Agent):
        """handle agent returning with agent (employer) or asking for service (ECE)"""
        raise NotImplementedError

    @abstractmethod
    def register_in_platform(self):
        raise NotImplementedError

    @property
    def my_id(self):
        return self._my_id

    @my_id.setter
    def my_id(self, value):
        self._my_id = value


class Service(PlatformEntity):
    def __init__(self, platform, my_id: str):
        # relate to relevant entities
        # self.my_id = CONFIG.ID_ECE
        self.platform = platform
        self.cc: CC = None
        self.service_name: str = ""
        super().__init__(my_id=my_id)

        self._request_id = 0
        self._service_id = 0

        # unique word used for logging
        self.logging_key_word = ""

        # queues for tracking service stages
        self.services_completed = PlatformQueue()
        self.services_in_progress = PlatformHashTable()
        self.services_to_start = PlatformQueue()

        # table of agent-agent requests
        self.requests_table = PlatformHashTable()

    # method for action triggered every new agent added
    @abstractmethod
    def on_new_request(self):
        raise NotImplementedError

    # request agent for each completed service
    def on_service_completed(self):
        # while there is still completed services, submit agent requests
        while not self.services_completed.is_empty():
            # get agent from completed_services queue
            data = self.services_completed.get()
            # create a new response agent
            current_request_id = self.request_id
            agent_request = Request(request_id=current_request_id, source_id=self.my_id, destination_id=data.source_id,
                                    data_id=data.data_id, priority=data.priority)

            # save agent until agent is granted
            data.my_id = current_request_id
            self.requests_table.insert(data)

            # logging
            logger.info(self.my_id + ' ' + f'service {self.logging_key_word}: {data.data_id} completed')

            # request agent from FCC
            self.cc.request_agent(request=agent_request)
            # pub.sendMessage(topicName=self.cc.topic, request=agent_request)

    # function to handle incoming agents and trigger service
    def handle_agent_returned(self, agent: Agent):
        # create drone and copy agent
        service_drone = Drone(my_id=self.service_id)
        service_drone.copy_agent(agent=agent)

        # terminate agent
        agent.terminate()

        # save service agent in a queue
        self.services_to_start.put(item=service_drone)

        # logging
        logger.info(self.my_id + ' ' + f'{self.cc.my_id} service {self.logging_key_word}'
                                       f'transaction {agent.transaction_id} agent received')

        # trigger service start
        self.on_new_request()

    def handle_agent_granted(self, agent: Agent):
        # get agent from requests table
        data_drone = self.requests_table.remove(agent.request_id)
        # set agent data as data_drone
        agent.data_from_drone(data_drone)
        # send agents to destination
        agent.to_destination()

    # register with platform
    @abstractmethod
    def register_in_platform(self):
        raise NotImplementedError

    @property
    def request_id(self):
        self._request_id += 1
        return self.service_name + str(self._request_id)

    @property
    def service_id(self):
        try:
            self._service_id += 1
            temp = self.service_name + "S" + str(self._service_id)
            return temp
        except RecursionError:
            pass

    @request_id.setter
    def request_id(self, value):
        self._request_id = value

    @service_id.setter
    def service_id(self, value):
        self._service_id = value
