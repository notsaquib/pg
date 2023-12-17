# Code generated, in part, using chatGPT on 27.10.2023
# Prompt: I am simulating a problem where factory registered_entities receive jobs and schedule them such that they
# submit bids in an energy market to get the lowest operating cost possible.
# I need to generate a number of jobs with random data_response and distribute them among a number of registered_entities.
# Each  job_id has fields: "release_time", "due_time", "duration". The duration should not be greater than the starting
# time and the due time.
# Write me Python code that generates a number of jobs based on a parameter {n_Jobs} and a number of registered_entities based
# on a parameter {n_machines} . The Job field values should be generated randomly with the mentioned constraint.
# Response to question about distributing the jobs on the registered_entities fairly and randomly: Yes, the code randomly
# distributes the generated jobs among the {n_machines} available registered_entities.
# The line machine_jobs[i % n_machines].append(job_id) ensures that each job_id is assigned to a employer in a round-robin
# fashion, with the remainder of i divided by n_machines being used to determine which employer the job_id should be
# assigned to. This ensures that each employer receives a roughly equal number of jobs, regardless of the total number
# of jobs or registered_entities.

from datetime import datetime, timedelta
import random

import CONFIG
import Enums
from DataPoint import JobDataPoint
from ExternalMarket import ExtMarketData


def generate_data():
    n_jobs = CONFIG.N_JOBS  # Number of jobs to generate
    n_machines = CONFIG.N_MACHINES  # Number of registered_entities to distribute jobs among
    ref_time = CONFIG.REF_TIMESTAMP

    jobs = []  # List to store generated jobs
    max_time = 0  # store the maximum period for energy suppliers
    energy_list = []  # store the energy generated for jobs for suppliers generation
    duration_list = []  #  used for agent analysis

    for i in range(n_jobs):
        job_id = CONFIG.NAME_JOB + str(i + 1).zfill(CONFIG.NAME_ZERO_FILL)

        # Random release time between 0 and 50
        release_time = ref_time + random.randint(0, CONFIG.TIME_RELEASE_MAX) * CONFIG.TIME_INT_INTERVAL * 60

        # Random due time after release time
        due_time = release_time + (random.randint(1, CONFIG.TIME_DEADLINE_MAX) * CONFIG.TIME_INT_INTERVAL * 60)

        # Random duration that fits within release and due time
        duration = random.randint(1, (due_time - release_time) /
                                  (CONFIG.TIME_INT_INTERVAL * 60)) * CONFIG.TIME_INT_INTERVAL * 60

        # random energy demand generation
        energy = round(random.uniform(CONFIG.JOB_ENERGY_MIN, CONFIG.JOB_ENERGY_MAX), 2)

        # random priority per job
        priority = random.randint(0, CONFIG.PRIORITY_LEVELS - 1)

        # random number of job objectives
        objectives_num = random.randint(0, len(Enums.ObjectiveJob))
        objectives = random.choices(CONFIG.LIST_JOB_OBJECTIVES_ALL, k=objectives_num)

        # populate job attributes
        job_i = JobDataPoint(my_id=job_id)
        job_i.constraints = {Enums.JobConstraint.TIME_READY: release_time,
                             Enums.JobConstraint.TIME_DEADLINE: due_time,
                             Enums.JobConstraint.TIME_PROCESSING: duration,
                             Enums.JobConstraint.ENERGY_DEMAND: energy}
        job_i.priority = priority
        job_i.objectives = objectives

        max_time = max([max_time, due_time])
        energy_list.append(energy)
        duration_list.append(duration)
        jobs.append(job_i)

    # Distribute jobs among registered_entities
    machine_jobs = []
    for i, job in enumerate(jobs):
        # machine_jobs[i % n_machines].append(job_id)
        machine_jobs.append((i % n_machines, job))

    # shuffle order of data_response
    random.shuffle(machine_jobs)

    # dictionary for supplier generation data_response
    suppliers_data = {ExtMarketData.LIST_ENERGY: energy_list, ExtMarketData.TIME_SUPPLY_PERIOD_FINISH: max_time}

    return machine_jobs, suppliers_data, duration_list


if __name__ == "__main__":
    # Print generated jobs for each employer
    machines_jobs = generate_data()
    for j, machine_job in enumerate(machines_jobs):
        print(f"Machine {j + 1} jobs:")
        for job_j in machine_job:
            print(job_j)
