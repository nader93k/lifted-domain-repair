from search_partial_grounding import \
    read_ground_actions, all_action_groundings, read_action_names,smart_grounder, \
    AStar, DFS, Node
from model.plan import Domain, Task
from search_partial_grounding.action_grounding_tools import smart_grounder
#TODO: Fina a better place for ground_repair
from vanilla_runs.run_songtuans_vanilla import ground_repair
from instance_solver import solve_instance

from exptools import list_instances
from pathlib import Path
import os
import logging
import cProfile
import pstats
import json
import time
import subprocess



def print_profile(file_name: str, num_lines=20):
    stats = pstats.Stats(file_name)
    stats.sort_stats('ncalls')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stats.print_stats(script_dir, num_lines)


def run_module(search_algorithm, benchmark_path, log_folder, log_interval, instance_id=None):
    instance_list = list_instances(benchmark_path, instance_id=instance_id)
    instance_list.sort(key=lambda i: i.plan_length)

    for instance in instance_list:
        solve_instance(search_algorithm
                      , benchmark_path
                      , log_folder
                      , log_interval
                      , instance.identifier
                      )


def run_process(search_algorithm, benchmark_path, log_folder, log_interval, instance_id=None):
    instance_list = list_instances(benchmark_path, instance_id=instance_id)
    instance_list.sort(key=lambda i: i.plan_length)

    for instance in instance_list:
        cmd = [
            "/home/nader/miniconda3/envs/planning/bin/python",
            "instance_solver.py",
            search_algorithm,
            benchmark_path,
            log_folder,
            str(log_interval),
            instance.identifier
        ]
        # 30 minutes in seconds
        timeout_seconds = 30 * 60
        try:
            print(f"Starting a subprocess solver for instance_id={instance.identifier}")
            result = subprocess.run(cmd, check=True, timeout=timeout_seconds)
            print(f"Solver done with no errors.")
        except subprocess.TimeoutExpired:
            print("Command timed out after 30 minutes")
        except subprocess.CalledProcessError as e:
            print(f"Error: instance id ={instance.identifier}, err: {e}")



if __name__ == "__main__":
    search_algorithm = 'astar'
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    benchmark_path = Path('./input/benchmarks-G1')
    # log_folder = Path('./exp_logs/4 BFS mega-run')
    log_folder = Path('./exp_logs/6 ASTAR mega-run full-log')
    # log_folder = Path('./exp_logs_debug')
    log_interval = 1
    

    run_process(search_algorithm=search_algorithm
              , benchmark_path=benchmark_path
              , log_folder=log_folder
              , log_interval=log_interval
              , instance_id='blocks/pprobBLOCKS-5-0-err-rate-0-5')

    # cProfile.run("experiment(benchmark_path)", 'profiler_tmp')
    # instance_id_example: 'blocks/pprobBLOCKS-5-0-err-rate-0-5'
