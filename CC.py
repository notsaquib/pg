from abc import abstractmethod

from loguru import logger
from pubsub import pub

# Communication Controller Class inherits from Communication controller class
import CONFIG
from Agent import Agent, AgentRole
from DataPoint import Request, DataPoint
from PlatformQueue import PlatformQueue
from PlatfromHashTable import PlatformHashTable


# General Communication Controller Class
class CC:
    def __init__(self, platform, my_id: str, topic: str):
        self.my_id = my_id
        self.platform = platform
        self.service = None
        self.agents_handler = None
        self.topic = topic

        # Create hash tables and Queues
        # save unfulfilled agent requests by employer
        self.machine_requests_queue = PlatformQueue()

        # save unfulfilled agent requests by service
        self.service_requests_queue = PlatformQueue()

        # table to track agents deployed
        self.shadow_agents_table = PlatformHashTable()

        # event loop for running internal coroutines
        # self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        # topics to subscribe to
        pub.subscribe(self.on_new_agent_requested, CONFIG.TOPIC_CC_CHECK_REQUESTS_QUEUE)

    # monitor resources and requests before assigning agents

    # function to listen to data_response addition events
    def on_new_agent_requested(self):
        # check on service requests first due to higher priority

        # TODO: (Real-time Scheduling) manage granting of agents to either machine or ECE
        while not self.service_requests_queue.is_empty():
            request = self.service_requests_queue.get()
            # if no agent is granted then there is not enough agents
            if not self.grant_request(request=request):
                # leave the loop
                break

        while not self.machine_requests_queue.is_empty():
            # retrieve data_response from requests queue
            request = self.machine_requests_queue.get()
            # if no agent is granted then there is not enough agents
            if not self.grant_request(request=request):
                # leave the loop
                break

    # functions for CC-to-any communications

    # function called by employer to data_response an agent
    def request_agent(self, request: Request):
        if request.source_id is self.service.my_id:
            self.service_requests_queue.put(item=request)
        else:
            # put data_response in queue
            self.machine_requests_queue.put(item=request)

        # log data_response
        logger.info(self.my_id + ' ' + f'agent requested by {request.source_id}')

        # call CC events listener
        self.on_new_agent_requested()

    # function for granting requests
    def grant_request(self, request: Request):
        agent = self.reserve_agent(request=request)
        # check if agent is granted
        if agent is not None:
            # prepare and grant agent
            agent.prepare_from_request(request=request)
            self.set_agent_role(agent=agent)
            logger.info(self.my_id + ' ' + f'agent request {request.request_id} granted to {request.source_id}')
            agent.to_source()
            dispatch_status = True
        else:
            logger.info(self.my_id + ' ' + f'agent request {request.request_id} failed, returned to queue')
            # return data_response to queue
            self.service_requests_queue.put(request)
            dispatch_status = False
        return dispatch_status

    # reserve agent to grant a data_response
    def reserve_agent(self, request: Request):
        request_id = request.request_id
        entity_id = request.source_id

        # generate transaction_id
        transaction_id = self.generate_transaction_id(entity_id=entity_id, request_id=request_id)

        # attempt to reserve agent
        agent = self.agents_handler.reserve_agent()
        agent.transaction_id = transaction_id

        return agent

    # method to set agent role (dependent on CC module)
    @abstractmethod
    def set_agent_role(self, agent: Agent):
        raise NotImplementedError

    # method to generate transaction_id
    @staticmethod
    def generate_transaction_id(entity_id: str, request_id: str):
        # TODO: find suitable generation method
        return entity_id + ":" + str(request_id)

    # method to register relevant entities
    def register_in_platform(self):
        self.agents_handler = self.platform.agents_handler


# ===============================================================================================================
# ===============================================================================================================


class FCC(CC):
    def __init__(self, platform):
        super().__init__(platform, my_id=CONFIG.ID_FCC, topic=CONFIG.TOPIC_FCC)

    def set_agent_role(self, agent: Agent):
        agent.set_role(AgentRole.FACTORY)

    # method to register relevant entities
    def register_in_platform(self):
        CC.register_in_platform(self)
        self.service = self.platform.ece
        pub.subscribe(self.request_agent, topicName=self.topic)


class BCC(CC):
    def __init__(self, platform):
        super().__init__(platform, my_id=CONFIG.ID_BCC, topic=CONFIG.TOPIC_BCC)

    def set_agent_role(self, agent: Agent):
        agent.set_role(AgentRole.BIDDING)

    # method to register relevant entities
    def register_in_platform(self):
        CC.register_in_platform(self)
        self.service = self.platform.market
        pub.subscribe(self.request_agent, topicName=self.topic)
