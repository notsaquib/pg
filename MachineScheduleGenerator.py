from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from loguru import logger

import CONFIG
from Enums import JobRecField, JobConstraint
from DataPoint import KPI
from SchedulingStrategies import EmpiricalScheduling, PyomoScheduling, RecursiveScheduling


class MachineScheduleGenerator:
    def __init__(self, machine):
        self.machine = machine
        self.jobs_record = machine.records_keeper.jobs_record
        self.jobs = {}
        self.schedules = []

    def generate_schedules(self):
        self.jobs = self.create_dictionary()
        self.schedules.append(EmpiricalScheduling.first_in_first_out(self.jobs))
        self.schedules.append(EmpiricalScheduling.earliest_due_date_first(self.jobs))
        self.schedules.append(EmpiricalScheduling.last_in_first_out(self.jobs))
        self.schedules.append(EmpiricalScheduling.shortest_processing_time(self.jobs))
        self.schedules.append(RecursiveScheduling.recursive_min_cost(self.jobs))
        self.schedules.extend(PyomoScheduling.opt_schedule(self.jobs))

        # calculate KPI
        for schedule in self.schedules:
            schedule.kpi = self.calculate_kpi(schedule)

        # log schedules generated
        self.log_schedule_generation()

        # store generated schedules in record keeper
        self.machine.records_keeper.add_schedules(self.schedules)

        # create event of schedules generated
        self.machine.events_listener.on_schedules_generated()

    # TODO: get rid of it and replace with direct referencing to record-keeper
    def create_dictionary(self):
        jobs = self.jobs_record.loc[:][JobRecField.DATA]
        job_dict = {}
        for job in jobs:
            job_dict.update({job.my_id: {
                JobConstraint.TIME_READY: job.time_ready,
                JobConstraint.TIME_DEADLINE: job.time_deadline,
                JobConstraint.TIME_PROCESSING: job.time_processing,
                JobConstraint.ENERGY_DEMAND: job.energy_demand,
                JobRecField.PRIORITY: job.priority,
            }})
        return job_dict

    # helper method for calculating KPI for a schedule
    def calculate_kpi(self, schedule):
        kpi = KPI()
        kpi.makespan = (max(slot.time_finish for slot in schedule.table)
                        - min(slot.time_start for slot in schedule.table)) / CONFIG.TIME_INTERVAL_UNIX
        kpi.max_pastdue = max(max(0, slot.time_finish - self.jobs[slot.job_id][JobConstraint.TIME_DEADLINE])
                              for slot in schedule.table) / CONFIG.TIME_INTERVAL_UNIX
        kpi.sum_pastdue = sum(max(0, slot.time_finish - self.jobs[slot.job_id][JobConstraint.TIME_DEADLINE])
                              for slot in schedule.table) / CONFIG.TIME_INTERVAL_UNIX
        kpi.num_pastdue = sum(slot.time_finish > self.jobs[slot.job_id][JobConstraint.TIME_DEADLINE]
                              for slot in schedule.table)
        kpi.num_on_time = sum(slot.time_finish <= self.jobs[slot.job_id][JobConstraint.TIME_DEADLINE]
                              for slot in schedule.table)
        kpi.fraction_on_time = kpi.num_on_time / len(schedule.table)
        kpi.priority_job_pastdue = sum((slot.time_finish > self.jobs[slot.job_id][JobConstraint.TIME_DEADLINE]) *
                                       (CONFIG.PRIORITY_LEVELS - self.jobs[slot.job_id][JobRecField.PRIORITY])
                                       for slot in schedule.table)
        return kpi

    def log_schedule_generation(self):
        for schedule in self.schedules:
            logger.info(self.machine.my_id + f": schedule generated: {schedule.source}")

    def print_schedules(self):
        # print schedules using a readable time format
        for schedule in self.schedules:
            print(schedule)

    # Gantt Chart largely based on code from
    # https://jckantor.github.io/ND-Pyomo-Cookbook/notebooks/04.02-Machine-Bottleneck.html#example
    def plot_schedules(self):
        # plt.switch_backend('GTK3Agg')
        plt.switch_backend('Qt5Agg')
        bw = 0.3
        for schedule in self.schedules:
            JOBS = schedule.jobs
            plt.figure(figsize=(12, 0.7 * (len(schedule.table))))
            idx = 0
            for j in sorted(JOBS):
                x = datetime.fromtimestamp(self.machine.records_keeper.get_job(j).time_ready) # datetime.fromtimestamp(JOBS[j][JobConstraint.TIME_READY])
                y = datetime.fromtimestamp(self.machine.records_keeper.get_job(j).time_deadline) # datetime.fromtimestamp(JOBS[j][JobConstraint.TIME_DEADLINE])
                plt.fill_between([x, y], [idx - bw, idx - bw], [idx + bw, idx + bw], color='cyan', alpha=0.6)
                if j in schedule.jobs:
                    x = datetime.fromtimestamp(schedule.get_time_start(j))
                    y = datetime.fromtimestamp(schedule.get_time_finish(j))
                    plt.fill_between([x, y], [idx - bw, idx - bw], [idx + bw, idx + bw], color='red', alpha=0.5)
                    plt.plot([x, y, y, x, x], [idx - bw, idx - bw, idx + bw, idx + bw, idx - bw], color='k')
                    plt.text(datetime.fromtimestamp((schedule.get_time_start(j) + schedule.get_time_finish(j)) / 2),
                             idx,
                             'Job ' + j, color='white', weight='bold',
                             horizontalalignment='center', verticalalignment='center')
                idx += 1

            plt.ylim(-0.5, idx - 0.5)
            plt.title(schedule.source)
            plt.xlabel('Time')
            plt.ylabel('Jobs')
            plt.yticks(range(len(JOBS)), sorted(JOBS))
            plt.grid()
        plt.show()
