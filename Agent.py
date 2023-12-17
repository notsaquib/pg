from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field

import CONFIG
from Enums import CommField
from DataPoint import DataPoint, Request, Mayfly


# internal agent used in service to shadow an agent
@dataclass
class Drone(DataPoint):
    request_id: str = ""
    source_id: str = ""

    # unique identifier for data_response
    data_id: str = ""

    # data_response that the role is trying to find
    data_to_find: dict = field(default_factory=dict)

    # data_response that the agent should return with
    data_response: DataPoint = None

    # method to get data_response when agent returns
    def get_data(self):
        return self.data_response

    def copy_agent(self, agent: Drone):
        """mirror agent data to start service internal usage"""
        self.request_id = agent.request_id
        self.source_id = agent.source_id
        self.data_to_find = agent.data_to_find
        self.data_from_drone(agent=agent)

    def data_from_drone(self, agent: Drone):
        """set agent data for dispatch, without changing communication parameters"""
        self.priority = agent.priority
        self.data_id = agent.data_id
        self.data_response = agent.data_response

    def __lt__(self, agent: Agent):
        return self.priority < agent.priority

    def __le__(self, agent: Agent):
        return self.priority <= agent.priority

    def __gt__(self, agent: Agent):
        return self.priority > agent.priority

    def __ge__(self, agent: Agent):
        return self.priority >= agent.priority

    def __eq__(self, agent: Agent):
        try:
            return self.priority == agent.priority
        except AttributeError:
            pass


# Enum of possible Agent Roles
class AgentRole(Enum):
    FACTORY = "FACTORY"
    BIDDING = "BIDDING"
    TRADING = "TRADING"
    IDLE = "IDLE"


@dataclass
class Agent(Drone):
    platform = None
    my_id: str = CONFIG.NAME_AGENT + str(0).zfill(CONFIG.NAME_ZERO_FILL)
    transaction_id: str = ""

    destination_id: str = ""

    # role to be performed by agents
    role: AgentRole = AgentRole.IDLE

    def to_source(self):
        """to_destination agent from CC to source_id"""
        self.platform.agent_to_source(agent=self)

    def to_destination(self):
        """to_destination agent to destination"""
        self.platform.agent_to_destination(agent=self)

    def set_role(self, role: AgentRole):
        # set role
        self.role = role
        # configure data_to_find according to role
        if role is AgentRole.FACTORY:
            self.data_to_find = dict.fromkeys(CommField.factory())
        if role is AgentRole.BIDDING:
            self.data_to_find = dict.fromkeys(CommField.bidding())

    # method to fill data_response-fields that need to found
    def request_data_to_find(self, mayfly: Mayfly):
        for comm_field in self.data_to_find:
            self.data_to_find[comm_field] = mayfly.get_data(comm_field)

    def terminate(self):
        self.platform.agents_handler.terminate_transaction(agent=self)

    def prepare_from_request(self, request: Request):
        self.priority = request.priority
        self.request_id = request.request_id
        self.source_id = request.source_id
        self.destination_id = request.destination_id
        self.data_id = request.data_id

    # function to reset agent
    def reset_assignment(self):
        # reset transaction_id
        self.transaction_id = ""
        self.my_id = ""
        self.data_id = ""

        # remove contained data_response
        self.data = None
