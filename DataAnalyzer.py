import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import pymarket as pm

from Machine import Machine


class DataAnalyzer:
    def __init__(self, machines):
        self.machines = machines
        self.quaderant_data: pd.DataFrame = pd.DataFrame(columns=['release', 'deadline', 'start', 'finish'])

    @staticmethod
    def box_plot(data: list):
        plt.switch_backend('Qt5Agg')
        plt.boxplot(data)
        plt.show()
    def extract_quadrant_time_data(self, machine: Machine):
        data_raw = self.extract_quadrant_job_raw(machine)
        data_scheduled = self.extract_quadrant_job_scheduled(machine)

    @staticmethod
    def extract_quadrant_job_raw(machine: Machine):
        job_ids = machine.records_keeper.jobs_index
        return_dict = {}
        for job in job_ids:
            release = machine.records_keeper.get_job(job_id=job).time_ready
            deadline = machine.records_keeper.get_job(job_id=job).time_deadline
            return_dict[job] = {'release': release, 'deadline': deadline}
        return return_dict

    def extract_quadrant_job_scheduled(machine: Machine):
        schedules = machine.records_keeper.schedules_record
        return_dict = {}
        for schedule in schedules:
            job_ids = schedule.jobs
            for job in job_ids:
                start = schedule.get_time_start(job)
                finish = schedule.get_time_finish(job)
                return_dict[job] = {'start': start, 'finish': finish}
        return return_dict