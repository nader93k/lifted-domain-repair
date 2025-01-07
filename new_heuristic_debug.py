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
from heuristic_tools.old_heuristic import Heurisitc as old_Heuristic



benchmark_path = './input/benchmarks-G1'
instance_list = list_instances(benchmark_path, None, [], lift_prob=1.0)


# to run on an specific instance, you can pass instance_id like this:
instance_list = list_instances(
    benchmark_path,
    None, 
    ['mprime__pprob34-err-rate-0-3'],
    lift_prob=1.0)

with open(os.path.join(os.path.dirname(__file__), 'debug_log.txt'), 'w') as debug_log:
    for i, instance in enumerate(smart_instance_generator(
        instance_list, min_length=1,
        max_length=8,
        order='increasing')):
        print(f'iter {i}')



        instance.load_to_memory()
        domain = instance.planning_domain
        task = instance.planning_task
        plan = instance.lifted_plan

        # print a headline
        # print("="*15 + f' INSTANCE ID = {instance.identifier}' + "="*15, file=debug_log)
        # print(f'Plan length = {instance.plan_length}', file=debug_log)

        # # compute the OLD VERSION of the heuristic - NORMAL DISK
        # print("="*10 + f' OLD HEURISTIC ' + "="*10, file=debug_log)
        # base_folder=f'heuristic_files_old/instance_{instance.identifier}/'
        # try:
        #     start_time = time.time()
        #     h_old = old_Heuristic(h_name="L_HMAX", relaxation='none', ground_base_folder=base_folder)
        #     h_cost_old = h_old.evaluate(domain, task, plan)
        #     end_time = time.time()
        #     print(f"h_old_normal_disk={h_cost_old}", file=debug_log)
        #     wall_time = end_time - start_time
        #     print(f"Wall time - normal disk: {wall_time:.4f} seconds", file=debug_log)
        # except Exception as e:
        #     print(f"Failed to process instance {instance.identifier}: {str(e)}", file=debug_log)

        base_folder=f'heuristic_files_new/instance_{instance.identifier}/'
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
