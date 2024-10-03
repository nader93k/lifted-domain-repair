from instance_solver import solve_instance
from logging_config import setup_logging
from exptools import list_instances, smart_instance_generator
from pathlib import Path
import os
import logging
import pstats
import subprocess
import json



def print_profile(file_name: str, num_lines=20):
    stats = pstats.Stats(file_name)
    stats.sort_stats('ncalls')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stats.print_stats(script_dir, num_lines)


# def run_module(search_algorithm, benchmark_path, log_folder, log_interval, instance_id=None):
#     instance_list = list_instances(benchmark_path, instance_id=instance_id)
#     instance_list.sort(key=lambda i: i.plan_length)

#     for instance in instance_list:
#         solve_instance(search_algorithm
#                       , benchmark_path
#                       , log_folder
#                       , log_interval
#                       , instance.identifier
#         )


def run_process(search_algorithm, benchmark_path, log_folder, log_interval, timeout_seconds, order, min_length, max_length, domain_class=None, instance_ids=[]):
    instance_list = list_instances(benchmark_path, domain_class, instance_ids)
    
    # instance_list.sort(key=lambda i: i.plan_length)

    for instance in smart_instance_generator(instance_list, min_length=min_length, max_length=max_length, order=order):
        log_file = os.path.join(
            log_folder,
            f"{search_algorithm}_length_{instance.plan_length}_{instance.domain_class}_{instance.instance_name}.txt"
        )
        if os.path.isfile(log_file):
            continue
        logger = setup_logging(log_file)

        cmd = [
                "/home/nader/miniconda3/envs/planning/bin/python",
                "instance_solver.py",
                search_algorithm,
                benchmark_path,
                log_file,
                str(log_interval),
                instance.identifier
            ]
        if True:
            try:
                print(f"> Starting a subprocess search for file_name={log_file}")
                result = subprocess.run(cmd, check=True, timeout=timeout_seconds)
                logger.info(f"> Subprocess finished.")
            except subprocess.TimeoutExpired:
                logger.error(f"> Command timed out after {timeout_seconds} seconds")
            except subprocess.CalledProcessError as e:
                logger.error(f"> Error: instance id ={instance.identifier}, err: {e}")
        else:
            # normal function call: mostly used for debugging
            try:
                print(f"> Starting by function call for file_name={log_file}")
                result = solve_instance(*cmd[2:])
                logger.info(f"> Subprocess finished.")
            except Exception as e:
                logger.error(f"> Error: instance id ={instance.identifier}, err: {e}")
            
            

def load_instance_ids(file_path='instance_ids.json'):
    with open(file_path, 'r') as file:
        instance_ids = json.load(file)
    print(f"Successfully loaded {len(instance_ids)} instance IDs from JSON file.")
    return instance_ids

# instance_id_example: 'blocks/pprobBLOCKS-5-0-err-rate-0-5'
if __name__ == "__main__":
    benchmark_path = Path('./input/benchmarks-G1')
    search_algorithm = 'astar'
    # log_folder = Path('./exp_logs/4 BFS mega-run')
    log_folder = Path('./exp_logs_debug')
    # log_folder = Path('./exp_logs/7 Songtuan Vanilla')
    log_interval = 1
    timeout_seconds = 30 * 60
    order = 'random'
    min_length = 1
    max_length = 15
    # domain_class='blocks'
    domain_class = None
    instance_ids = load_instance_ids()
    # instance_ids = ["blocks/pprobBLOCKS-6-2-err-rate-0-3"]
    
    run_process(search_algorithm=search_algorithm
               , benchmark_path=benchmark_path
               , log_folder=log_folder
               , log_interval=log_interval
               , timeout_seconds=timeout_seconds
               , order=order
               , min_length=min_length
               , max_length=max_length
               , domain_class=domain_class
               , instance_ids=instance_ids)
