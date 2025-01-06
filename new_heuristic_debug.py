import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
sys.path.insert(0, project_root)
import copy
import subprocess
import time
from pathlib import Path
import re
from typing import List
import io
import contextlib
import psutil

from model.plan import *
from repairer import *
from exptools import list_instances, smart_instance_generator

from heuristic_tools import Heurisitc as new_heuristic
from heuristic_tools.old_heuristic import Heurisitc as old_Heuristic
from heuristic_tools import temporary_base_folder, temporary_base_folder_old_h




benchmark_path = './input/benchmarks-G1'
instance_list = list_instances(benchmark_path, None, [], lift_prob=1.0)

# to run on an specific instance, you can pass instance_id like this:
# instance_list = list_instances(
#     benchmark_path,
#     None, 
#     ['floortile-opt11-strips__popt-p02-003-err-rate-0-5', 'miconic__ps17-3-err-rate-0-3'],
#     lift_prob=1.0)
with open(os.path.join(os.path.dirname(__file__), 'debug_log.txt'), 'w') as debug_log:
    for instance in smart_instance_generator(
        instance_list, min_length=1,
        max_length=1000,
        order='increasing'):
        instance.load_to_memory()
        domain = instance.planning_domain
        task = instance.planning_task
        plan = instance.lifted_plan

        # print a headline
        print("="*15 + f' INSTANCE ID = {instance.identifier}' + "="*15, file=debug_log)
        print(f'Plan length = {instance.plan_length}', file=debug_log)

        # compute the OLD VERSION of the heuristic - NORMAL DISK
        print("="*10 + f' OLD HEURISTIC ' + "="*10, file=debug_log)
        base_folder=f'heuristic_files_old/instance_{instance.identifier}/'
        try:
            start_time = time.time()
            with temporary_base_folder_old_h(base_folder):
                h_old = old_Heuristic(h_name="L_HMAX", relaxation='none', ground_base_folder=base_folder)
                h_cost_old = h_old.evaluate(domain, task, plan)
                end_time = time.time()
                print(f"h_old_normal_disk={h_cost_old}", file=debug_log)
            
            wall_time = end_time - start_time
            
            print(f"Wall time - normal disk: {wall_time:.4f} seconds", file=debug_log)
        except Exception as e:
            print(f"Failed to process instance {instance.identifier}: {str(e)}", file=debug_log)

        # compute the OLD VERSION of the heuristic - RAM DISK
        base_folder=f'/dev/shm/heuristic_ramdisk/instance_{instance.identifier}'
        try:
            start_time = time.time()
            with temporary_base_folder_old_h(base_folder):
                h_old = old_Heuristic(h_name="L_HMAX", relaxation='none', ground_base_folder=base_folder)
                h_cost_old = h_old.evaluate(domain, task, plan)
                end_time = time.time()
                print(f"h_old_ram_disk={h_cost_old}", file=debug_log)
            
            wall_time = end_time - start_time
            print(f"Wall time - RAM disk: {wall_time:.3f} seconds", file=debug_log)
        except Exception as e:
            print(f"Failed to process instance {instance.identifier}: {str(e)}", file=debug_log)
        
        # compute the NEW VERSION of the heuristic - NORMAL DISK
        print("="*10 + f' NEW HEURISTIC ' + "="*10, file=debug_log)
        base_folder=f'heuristic_files_new/instance_{instance.identifier}/'
        try:
            start_time = time.time()
            with temporary_base_folder(base_folder):
                h_new = new_heuristic(h_name="L_HADD", relaxation='none')
                h_cost_new = h_new.evaluate(domain, task, plan)
                end_time = time.time()
                wall_time = end_time - start_time
                print(f"h_new={h_cost_new}", file=debug_log)
                print(f"Wall time - RAM disk: {wall_time:.3f} seconds", file=debug_log)

                # value comparison
                print("="*10 + f'COMPARISON', file=debug_log)
                equality = '==' if h_cost_new == h_cost_old else '<>'
                print(f"comparison: {equality}, h_new={h_cost_new}, h_old={h_cost_old}, instance={instance.identifier}", file=debug_log)
        except Exception as e:
            print(f"Failed to process instance {instance.identifier}: {str(e)}", file=debug_log)

        # Flush at the end of each iteration to ensure data is written
        debug_log.flush()
