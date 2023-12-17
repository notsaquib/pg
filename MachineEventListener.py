from loguru import logger

import CONFIG


# Machine Event Listener
# contains necessary methods to handle employer events
class MachineEventListener:
    def __init__(self, machine):
        self.machine = machine

    # event triggered when a new job is added
    def on_job_added(self):
        pass

    # event triggered when time slot energy cost estimation is missing
    def on_missing_estimation(self):
        pass

    # event triggered when a new estimation is returned from the ECE
    def on_estimation_acquired(self):
        pass

    # event triggered when a new estimation is added to the record keeper
    def on_estimation_added(self, data_id: str):
        # log event to console
        logger.info(self.machine.my_id + ' ' + f'price estimation {data_id} added')
        self.machine.on_estimation_added()

    # event triggered when schedules are generated
    def on_schedules_generated(self):
        # log all schedules generated
        logger.info(self.machine.my_id + ": " + "schedules generated")
        self.machine.on_schedules_generated()

    def on_bids_generated(self):
        # log bids ready
        logger.info(self.machine.my_id + ": " + "bids ready")
        self.machine.on_bids_generated()

    def on_bid_response_acquired(self):
        pass
        # log event to console
