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
from heuristic_tools import Heurisitc as new_heuristic
import pickle




benchmark_path = '/home/remote/u7899572/lifted-white-plan-domain-repair/input/benchmarks-G1'
instance_list = list_instances(benchmark_path, None, [], lift_prob=1.0)
debug_data_folder = '/home/remote/u7899572/lifted-white-plan-domain-repair/debug/debug_h_data/'

# to run on an specific instance, you can pass instance_id like this:
instance_list = list_instances(
    benchmark_path,
    None, 
    ['mprime__pprob25-err-rate-0-1'],
    lift_prob=1.0)
with open(os.path.join(os.path.dirname(__file__), 'debug_log.txt'), 'w') as debug_log:
    for instance in smart_instance_generator(
        instance_list, min_length=1,
        max_length=15,
        order='random'):
        instance.load_to_memory()

        # domain = instance.planning_domain
        # task = instance.planning_task
        # plan = instance.lifted_plan

        # Read actions.pkl
        with open(debug_data_folder+'actions.pkl', 'rb') as f:
            plan = pickle.load(f)
        print("Actions:", plan)

        # Read domain.pkl
        with open(debug_data_folder+'domain.pkl', 'rb') as f:
            domain = pickle.load(f)
        print("\nDomain:", domain.to_pddl())

        # Read task.pkl
        with open(debug_data_folder+'task.pkl', 'rb') as f:
            task = pickle.load(f)
        print("\nTask:", task.to_pddl())



        base_folder=f''
        # print a headline
        print("="*15 + f' INSTANCE ID = {instance.identifier}' + "="*15, file=debug_log)
        print(f'Plan length = {instance.plan_length}', file=debug_log)
        try:
            start_time = time.time()
            h_new = new_heuristic(h_name="L_HADD", relaxation='none')
            h_cost_new = h_new.evaluate(domain, task, plan)
            end_time = time.time()
            wall_time = end_time - start_time
                # print(f"h_new={h_cost_new}", file=debug_log)
                # print(f"Wall time - RAM disk: {wall_time:.3f} seconds", file=debug_log)

        except Exception as e:
            end_time = time.time()
            wall_time = end_time - start_time
            print("="*15 + f' Error in INSTANCE ID = {instance.identifier}' + "="*15, file=debug_log)
            print(f'Plan length = {instance.plan_length}', file=debug_log)
            print(f"Wall time: {wall_time:.3f} seconds", file=debug_log)
            print(f"Failed to process instance {instance.identifier}: {str(e)}", file=debug_log)
            print("\nFull traceback:", file=debug_log)
            traceback.print_exc(file=debug_log)
            print("="*40, file=debug_log)
        debug_log.flush()
