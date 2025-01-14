import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
sys.path.insert(0, project_root)
import time
from pathlib import Path
from typing import List
import traceback
from model.plan import *
from repairer import *
from exptools import list_instances, smart_instance_generator
from heuristic_tools import Heurisitc as heuristic
import pickle




benchmark_path = './input/benchmarks-G1'
instance_list = list_instances(benchmark_path, None, [], lift_prob=1.0)
debug_data_folder = '/home/remote/u7899572/lifted-white-plan-domain-repair/debug/debug_h_data/'

with open(os.path.join(os.path.dirname(__file__), 'debug_log.txt'), 'w') as debug_log:
    for instance in smart_instance_generator(
        instance_list, min_length=1,
        max_length=15,
        order='random'):
        instance.load_to_memory()

        domain = instance.planning_domain
        task = instance.planning_task
        plan = instance.lifted_plan

        base_folder=f''
        # print a headline
        print("="*15 + f' INSTANCE ID = {instance.identifier}' + "="*15, file=debug_log)
        print(f'Plan length = {instance.plan_length}', file=debug_log)
        # try:
        # no relaxation
        start_time = time.time()
        no_relax = heuristic(h_name="L_HADD", relaxation='none')
        h_no_relax = no_relax.evaluate(domain, task, plan)
        end_time = time.time()
        wall_time = end_time - start_time
        print(f"no_relaxation={h_no_relax}", file=debug_log)
        print(f"Wall time: {wall_time:.3f} seconds", file=debug_log)

        # zeroary
        start_time = time.time()
        zeroary = heuristic(h_name="L_HADD", relaxation='zeroary')
        h_zeroary = zeroary.evaluate(domain, task, plan)
        end_time = time.time()
        wall_time = end_time - start_time
        print(f"zeroary={h_zeroary}", file=debug_log)
        print(f"Wall time: {wall_time:.3f} seconds", file=debug_log)

        print(f"**diff: norelax - zeroary = {h_no_relax - h_zeroary}", file=debug_log)

        debug_log.flush()
