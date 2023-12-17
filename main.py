from loguru import logger
import asyncio
import sys

import CONFIG
import DataGenerator
from DataAnalyzer import DataAnalyzer
from ExternalMarket import ExternalMarket
from TradingPlatform import Platform
from Machine import Machine


async def run():
    # create logger
    logger.add('log/log' + CONFIG.get_time_key())

    # instantiate platform and other modules
    platform = Platform()
    external_market = ExternalMarket(platform)
    external_market.register_in_platform()

    # create registered_entities
    machines = []
    for _ in range(CONFIG.N_MACHINES):
        machine = Machine(platform)
        machine.register_in_platform()
        machines.append(machine)

    # generate data_response
    machine_jobs, suppliers_data, duration_list = DataGenerator.generate_data()
    external_market.create_suppliers(data=suppliers_data)

    # add jobs to the registered_entities
    for machine, job in machine_jobs:
        machines[machine].records_keeper.add_job(job)

    # generate schedules for jobs that were added to the registered_entities
    for machine in machines:
        machine.scheduler.generate_schedules()

        # # evaluate schedule output
        machine.scheduler.print_schedules()
        # # machine.scheduler.plot_schedules()
        machine.bidder.print_bids()

        # DataAnalyzer.box_plot(duration_list)
        pass

    # platform.run()


if __name__ == "__main__":
    # sys.setrecursionlimit(10000)
    asyncio.run(run())
