from __future__ import annotations
from pubsub import pub
from loguru import logger

# Machine sub-module classes
import CONFIG
from Agent import Agent
from DataPoint import Request, DataPoint, EstimationDataPoint, BidJob, Mayfly
from PlatformEntity import PlatformEntity
from PlatfromHashTable import PlatformHashTable
from CC import CC


# Agent handler Module
class AgentHandler:
    # manage agent references
    def __init__(self, employer, super_topic: str):
        # Agent_Handler_ID is the same as Machine_ID
        self.employer = employer

        # topic for subscribing to
        self.topic = super_topic

        # create agents hashtable
        self.requests_table = PlatformHashTable()
        self.data_ref_table = PlatformHashTable()

        # register FCC
        self.fcc: CC = None
        self.bcc: CC = None
        self.platform = None

    # functions to be called by the employer

    # function to data_response an agent
    def request_factory_agent(self, request_data: Mayfly):
        # create a shadow data_response for tracking
        request = Request(request_id=request_data.request_id, source_id=self.employer.my_id,
                          destination_id=self.platform.ece.my_id, data_id=request_data.data_id)
        self.requests_table.insert(datapoint=request_data)

        # log data_response
        logger.info(self.my_id + ' ' + f'factory agent request {request_data.request_id}')

        # data_response an agent from FCC and get a response
        # self.fcc.request_agent(agent=request)
        pub.sendMessage(topicName=CONFIG.TOPIC_FCC, request=request)

    def request_bidding_agent(self, request_data: Mayfly):
        # create a shadow data_response for tracking
        request = Request(request_id=request_data.request_id, source_id=self.employer.my_id,
                          destination_id=self.platform.market.my_id, data_id=request_data.data_id)
        self.requests_table.insert(datapoint=request_data)

        # log data_response
        logger.info(self.my_id + ' ' + f'factory agent request {request_data.request_id}')

        # data_response an agent from FCC and get a response
        # self.bcc.request_agent(agent=request)
        pub.sendMessage(topicName=CONFIG.TOPIC_BCC, request=request)

    # functions to handle agents received

    # function called by platform
    def receive_agent(self, agent:Agent):
        # check agent source_id, if same then it is granted by a agent
        if agent.source_id is self.my_id:
            self.handle_agent_granted(agent=agent)
        else:
            # agent is returning with a response to employer or requesting a service from a service
            self.handle_agent_returned(agent=agent)

    def handle_agent_granted(self, agent: Agent):
        # log agent granted
        logger.info(self.my_id + ' ' +
                    f'agent transaction {agent.transaction_id} granted by request {agent.request_id}')
        # get original request_data to set agent data parameters
        request_data = self.requests_table.remove(agent.request_id)
        # set request_data my_id to data_id
        request_data.my_id = request_data.data_id
        # save request_data indexed by data_id for return agent handling
        self.data_ref_table.insert(request_data)
        # agent to get relevant agent parameters
        agent.request_data_to_find(mayfly=request_data)
        # to_destination agent destination
        agent.to_destination()

    def handle_agent_returned(self, agent: Agent):
        # log agent returned
        logger.info(self.my_id + ' ' + f'agent return transaction {agent.transaction_id}')
        # get original request_data to set return agent
        request_data = self.data_ref_table.remove(agent.data_id)
        # copy agent response from agent to mayfly
        request_data.get_response_data(agent=agent)
        # order agent to terminate
        agent.terminate()
        # implement return action on return agent
        request_data.implement_return_action()

    # function to register agent handler with employer ID
    def register_platform_modules(self, machine):
        self.fcc = machine.platform.fcc
        self.bcc = machine.platform.bcc
        self.platform = machine.platform
        self.topic = self.topic + CONFIG.TOPIC_SEPARATOR + self.my_id
        pub.subscribe(self.receive_agent, topicName=self.topic)

    # method to return entity_id
    @property
    def my_id(self):
        return self.employer.my_id
