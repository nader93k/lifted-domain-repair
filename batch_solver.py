from instance_solver import solve_instance
from custom_logger import StructuredLogger
from exptools import list_instances, smart_instance_generator
from pathlib import Path
import os
import sys
import logging
import subprocess
import json
import yaml



def run_process(search_algorithm, benchmark_path, log_folder, log_interval, \
                timeout_seconds, order, min_length, max_length, heuristic_relaxation, \
                domain_class=None, instance_ids=[], lift_prob=0.0, run_mode='subprocess'):
    
    instance_list = list_instances(benchmark_path, domain_class, instance_ids)
    for instance in smart_instance_generator(instance_list, min_length=min_length
                                             , max_length=max_length
                                             , order=order):
        log_file = os.path.join(
            log_folder,
            f"{search_algorithm}_length_{instance.plan_length}_{instance.domain_class}_{instance.instance_name}.yaml"
        )
        if os.path.isfile(log_file):
            continue
        logger = StructuredLogger(log_file)

        interpreter_path = sys.executable
        cmd = [
                interpreter_path,
                "instance_solver.py",
                search_algorithm,
                str(benchmark_path),
                log_file,
                str(log_interval),
                instance.identifier,
                str(lift_prob) if run_mode == 'subprocess' else float(lift_prob)
            ]
        if heuristic_relaxation:
            cmd.append(heuristic_relaxation)
        if run_mode == 'subprocess':
            try:
                print(f"> Starting a subprocess search for file_name={log_file}")
                result = subprocess.run(cmd, check=True, timeout=timeout_seconds)
                logger.log(issuer="batch_solver", event_type="general"
                           , level=logging.INFO
                           , message="Subprocess finished with no exception.")
            except subprocess.TimeoutExpired:
                logger.log(issuer="batch_solver", event_type="error"
                           , level=logging.ERROR
                           , message=f"Subprocess timed out after {timeout_seconds} seconds.")
            except Exception as e:
                logger.log(issuer="batch_solver", event_type="error"
                           , level=logging.ERROR
                           , message=f"> Eexception: instance id ={instance.identifier}, err: {e}")
        elif run_mode == 'pycall': # python function call: mostly used for debugging
            print(f"> Starting by function call for file_name={log_file}")
            result = solve_instance(*cmd[2:])
        else:
            raise NotImplementedError


def load_instance_ids(file_path):
    with open(file_path, 'r') as file:
        instance_ids = json.load(file)
    print(f"Successfully loaded {len(instance_ids)} instance IDs from JSON file.")
    return instance_ids


if __name__ == "__main__":
    config_file = 'config.yaml'
    with open(config_file, 'r') as config_file:
        config = yaml.safe_load(config_file)
    
    benchmark_path = Path(config['benchmark_path'])
    search_algorithm = config['search_algorithm']
    log_folder = Path(config['log_folder'])
    log_interval = config['log_interval']
    timeout_seconds = config['timeout_seconds']
    order = config['order']
    min_length = config['min_length']
    max_length = config['max_length']
    domain_class = config['domain_class'] 
    heuristic_relaxation = config['heuristic_relaxation']
    lift_prob = config['lift_prob']
    run_mode = config['run_mode']

    # run on fixed instance_ids
    instance_ids = config['instance_ids']
    if instance_ids == 'load_instance_ids':
        instance_ids = load_instance_ids('instance_ids_nonzero_h.json')
    elif instance_ids == 'instance_ids_small_exp_set':
        instance_ids = load_instance_ids('instance_ids_small_exp_set.json')

    print(f"Loaded configuration from: {config_file}")
    
    run_process(search_algorithm=search_algorithm
               , benchmark_path=benchmark_path
               , log_folder=log_folder
               , log_interval=log_interval
               , timeout_seconds=timeout_seconds
               , order=order
               , min_length=min_length
               , max_length=max_length
               , domain_class=domain_class
               , instance_ids=instance_ids
               , heuristic_relaxation=heuristic_relaxation
               , lift_prob=lift_prob
               , run_mode=run_mode
               , num_parallel_processes=num_parallel_processes
               )
