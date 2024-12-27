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


log_old_h = open(os.path.join(os.path.dirname(__file__), 'log_old_h.txt'), 'w')
log_new_h = open(os.path.join(os.path.dirname(__file__), 'log_new_h.txt'), 'w')

# # to run on an specific instance, you can pass instance_id like this:
# # instance_list = list_instances(
# #     benchmark_path,
# #     None, 
# #     ['floortile-opt11-strips__popt-p02-003-err-rate-0-5', 'miconic__ps17-3-err-rate-0-3'],
# #     lift_prob=1.0)
# for instance in smart_instance_generator(
#     instance_list, min_length=1,
#     max_length=1000,
#     order='random'):
#     # randomness seed is fixed to 0

#     print(f'instance id = {instance.identifier}')

#     instance.load_to_memory()

#     domain = instance.planning_domain
#     task = instance.planning_task
#     plan = instance.lifted_plan


#     # compute the old version of the heuristic
#     base_folder=f'heuristic_files_old/instance_{instance.identifier}/'
#     try:
#         with temporary_base_folder_old_h(base_folder):
#             h_old = old_Heuristic(h_name="L_HMAX", relaxation='none')
#             h_cost_old = h_old.evaluate(domain, task, plan)
#             print(f"h_old={h_cost_old}, instance={instance.identifier}", file=log_old_h)
#     except Exception as e:
#         print(f"Failed to process instance {instance.identifier}: {str(e)}", file=log_old_h)
#         continue
    
    
#     # compute the new version of the heuristic
#     base_folder=f'heuristic_files_new/instance_{instance.identifier}/'
#     try:
#         with temporary_base_folder(base_folder):
#             h_new = new_heuristic(h_name="L_HADD", relaxation='none')
#             h_cost_new = h_new.evaluate(domain, task, plan)
#             print(f"h_new={h_cost_new}, instance={instance.identifier}", file=log_new_h)
#     except Exception as e:
#         print(f"Failed to process instance {instance.identifier}: {str(e)}", file=log_new_h)
#         continue

#     # equality = '==' if h == h_old else '<>'
#     # print(f"comparison: {equality}, h_new={h_cost}, h_old={h_cost_old}, instance={instance.identifier}")



###### TIME MEASURE #######

def get_io_time():
    try:
        # Get block I/O delays in clock ticks
        io_delays = psutil.Process().cpu_times().iowait
        return io_delays
    except AttributeError:
        return 0

log_time = open(os.path.join(os.path.dirname(__file__), 'heuristic_timings.txt'), 'w')
# to run on an specific instance, you can pass instance_id like this:
for instance in smart_instance_generator(
    instance_list, min_length=1,
    max_length=1000,
    order='random'):

    print("\n" + "="*50 + "\n", file=log_time)  # Add before each instance
    print(f'instance id = {instance.identifier}', file=log_time)

    instance.load_to_memory()

    domain = instance.planning_domain
    task = instance.planning_task
    plan = instance.lifted_plan


    # old version with normal files
    # base_folder=f'heuristic_files_old/instance_{instance.identifier}/'
    # try:
    #     start_time = time.time()
    #     start_cpu_time = time.process_time()
    #     start_io_time = get_io_time()
    #     with temporary_base_folder_old_h(base_folder):
    #         h_old = old_Heuristic(h_name="L_HMAX", relaxation='none')
    #         h_cost_old = h_old.evaluate(domain, task, plan)
    #     end_time = time.time()
    #     end_cpu_time = time.process_time()
    #     end_io_time = get_io_time()
        
    #     # Calculate times
    #     wall_time = end_time - start_time
    #     cpu_time = end_cpu_time - start_cpu_time
    #     io_time = end_io_time - start_io_time
        
    #     print(f"Normal Files Results:", file=log_time)
    #     print(f"  Wall time: {wall_time:.3f} seconds", file=log_time)
    #     print(f"  CPU time: {cpu_time:.3f} seconds", file=log_time)
    #     print(f"  I/O time: {io_time:.3f} seconds", file=log_time)
    #     print(f"  h_old={h_cost_old}", file=log_time)
    # except Exception as e:
    #     print(f"Failed to process instance {instance.identifier}: {str(e)}", file=log_time)
    #     continue

    # old version with RAM disk
    base_folder=f'/dev/shm/heuristic/instance_{instance.identifier}'
    try:
        start_time = time.time()
        start_cpu_time = time.process_time()
        start_io_time = get_io_time()
        with temporary_base_folder_old_h(base_folder):
            h_old = old_Heuristic(h_name="L_HMAX", relaxation='none')
            h_cost_old = h_old.evaluate(domain, task, plan)
        end_time = time.time()
        end_cpu_time = time.process_time()
        end_io_time = get_io_time()
        
        # Calculate times
        wall_time = end_time - start_time
        cpu_time = end_cpu_time - start_cpu_time
        io_time = end_io_time - start_io_time
        
        print(f"RAM Disk Results:", file=log_time)
        print(f"  Wall time: {wall_time:.3f} seconds", file=log_time)
        print(f"  CPU time: {cpu_time:.3f} seconds", file=log_time)
        print(f"  I/O time: {io_time:.3f} seconds", file=log_time)
        print(f"  h_old={h_cost_old}", file=log_time)
    except Exception as e:
        print(f"RAM Disk Error Details:", file=log_time)
        print(f"  Error type: {type(e).__name__}", file=log_time)
        print(f"  Error message: {str(e)}", file=log_time)
        # Try to get any stderr output if available
        if hasattr(e, 'stderr'):
            print(f"  stderr: {e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}", file=log_time)
    
    break
