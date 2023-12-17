import pubsub.pub
from loguru import logger
from pubsub import pub

import CONFIG
from Agent import Agent
from DataPoint import DataPoint, Request
from PlatformQueue import PlatformQueue
from PlatfromHashTable import PlatformHashTable
import TradingPlatform


class PlatformAgentHandler:
    def __init__(self, platform: TradingPlatform):
        # reference to platform
        self.platform = platform

        # agents queue
        self.agents_queue = PlatformQueue()
        self.generate_agents()

        # Hashtable for tracking relevant CC
        self.shadow_agent_cc = PlatformHashTable()

    # function to be called be CC to reserve an agent
    def reserve_agent(self):
        if self.agents_queue.is_empty():
            agent = None
            logger.info("Platform: All agents deployed, No more can be reserved!")
        else:
            # deploy agent
            agent = self.agents_queue.get()
            logger.info(f"Platform: Agent {agent.my_id} deployed, "
                        f"{self.agents_queue.size()} / {CONFIG.N_AGENTS} remain")
        return agent

    def terminate_transaction(self, agent:Agent):
        """"Terminate transaction by agent reset  returning it to the agents_queue"""""
        # log transaction termination
        logger.info(f"Platform: transaction {agent.transaction_id} terminated")
        # create a fresh agent with same name
        reset_agent = Agent(my_id=agent.my_id)
        reset_agent.platform = self.platform
        # delete old agent
        del agent
        # put fresh agent in queue
        self.agents_queue.put(reset_agent)
        # trigger the CCs to check their queue requests now that an agent is free
        pub.sendMessage(CONFIG.TOPIC_CC_CHECK_REQUESTS_QUEUE)

    # Helper Methods

    # method for agents generation
    def generate_agents(self):
        for i in range(1, CONFIG.N_AGENTS):
            # Generate Agent ID
            agent_name = CONFIG.NAME_AGENT + str(i).zfill(CONFIG.NAME_ZERO_FILL)
            # Create Agent instance
            new_agent = Agent(my_id=agent_name)
            new_agent.platform = self.platform
            # Save Agent in Queue
            self.agents_queue.put(new_agent)
