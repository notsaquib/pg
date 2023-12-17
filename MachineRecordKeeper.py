# class for Machine submodule: Record Keeper
# Keeps the records and logs needed for strategies and all decision-making
import pandas as pd

import CONFIG
import Enums
from DataPoint import JobDataPoint, EstimationDataPoint, Request
from Enums import ScheduleSrc
from PlatfromHashTable import PlatformHashTable


class MachineRecordKeeper():
    def __init__(self, machine):
        self.machine = machine

        # record of added jobs
        self.jobs_record = pd.DataFrame(columns=CONFIG.LIST_JOB_RECORD_FIELDS)
        self.jobs_index = {}
        self.prices_record = PlatformHashTable()
        self.schedules_record = {}
        self.price_estimates = {}

    def add_job(self, job: JobDataPoint):
        # create new job entry from JobDataPoint to insert into record
        job_data = self.job_datapoint_to_record_list(job)
        # index for fast referencing using jobs_index hashtable and insert in jobs_record
        job_index = len(self.jobs_record)
        # insert new job_id entry in the dataframe and the hashtable
        self.jobs_record.loc[job_index] = job_data
        self.jobs_index[job.my_id] = job_index

        # create a agent to save in the jobs_added_queue

        # notify employer event listener
        # self.employer.events_listener.on_job_added()

    # TODO: handle EcoInfo types
    def add_prices(self, new_prices: EstimationDataPoint):
        prices = new_prices.prices

        # insert offer datapoint in record
        self.prices_record.insert(new_prices)

        # insert prices in collective dictionary
        times = new_prices.time_slots
        for time in times:
            if time in self.price_estimates.keys():
                pass
            else:
                self.price_estimates[time] = prices[times.index(time)]

        self.machine.events_listener.on_estimation_added(new_prices.data_id)

    # method to calculate all schedule-slot costs once information is obtained
    def calculate_all_schedule_energy_costs(self):
        for schedule in list(self.schedules_record.values()):
            for slot in schedule.table:
                cost = self.calculate_job_cost(start=slot.time_start, finish=slot.time_finish,
                                               energy_demand=self.get_job_energy(slot.job_id))
                schedule.add_cost_entry(job_id=slot.job_id, cost=cost)

    # methods to get offer data_response

    # method to get jobs from record
    def get_job(self, job_id: str) -> JobDataPoint:
        # get index from jobs_index_hashtable
        index = self.jobs_index[job_id]

        # use index to get JobDataPoint from jobs_record
        return self.jobs_record.loc[index][Enums.JobRecField.DATA]

    # method to get offer data_response between start and finish time
    def get_interval_prices(self, time_start: int, time_finish: int):
        time_list = CONFIG.create_time_list(time_start=time_start, time_end=time_finish)
        return self.price_estimates[time_list]

    # method to get prices from records
    def get_job_prices(self, job_id: str) -> EstimationDataPoint:
        return self.prices_record.find(job_id)

    # method to return offer estimate at certain time
    def get_time_price(self, time: int) -> float:
        try:
            return self.price_estimates[time]
        # if offer does not exist, data_response a new estimate
        except KeyError:
            miss_estimate = EstimationDataPoint.create_from_interval(start=max(self.price_estimates.keys()),
                                                                     finish=time)
            miss_estimate.my_id = "MissEst" + str(time)
            # new_event = MachineEvent(my_id=CONFIG.get_time_key(), agent=miss_estimate)
            # self.employer.events_listener.on_missing_estimation(new_event)
            return 0.0

    # method to get job_id energy demand
    def get_job_energy(self, job_id: str):
        return self.get_job(job_id=job_id).energy_demand

    # methods for schedule data_response
    def add_schedules(self, schedules):
        for schedule in schedules:
            self.schedules_record[schedule.source] = schedule

    def get_schedule(self, schedule_id: ScheduleSrc):
        return self.schedules_record[schedule_id]

    # Helper methods

    # method to convert JobDataPoint object to record entry
    @staticmethod
    def job_datapoint_to_record_list(job_datapoint: JobDataPoint):
        my_id = job_datapoint.my_id
        priority = job_datapoint.priority
        status = job_datapoint.status
        return pd.Series([my_id, priority, status, job_datapoint], index=CONFIG.LIST_JOB_RECORD_FIELDS)

    # calculating job_id cost
    def calculate_job_cost(self, start: int, finish: int, energy_demand: float):
        # calculating the cost of each job_id if it is scheduled as proposed
        cost = 0
        for slot in range(int(start), int(finish), CONFIG.TIME_INTERVAL_UNIX):
            # get offer from record keeper
            price = self.get_time_price(slot)

            # division / 1000 is subject to units: offer [€ / MWh], energy_demand [kWh / slot]
            cost += price * energy_demand / 1000
        return cost
