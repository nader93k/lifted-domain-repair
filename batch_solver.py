from instance_solver import solve_instance
from custom_logger import StructuredLogger
from exptools import list_instances, smart_instance_generator
from pathlib import Path
import os
import logging
import pstats
import subprocess
import json



def run_process(search_algorithm, benchmark_path, log_folder, log_interval, timeout_seconds, order, min_length, max_length, domain_class=None, instance_ids=[]):
    instance_list = list_instances(benchmark_path, domain_class, instance_ids)
    for instance in smart_instance_generator(instance_list, min_length=min_length, max_length=max_length, order=order):
        log_file = os.path.join(
            log_folder,
            f"{search_algorithm}_length_{instance.plan_length}_{instance.domain_class}_{instance.instance_name}.yaml"
        )
        if os.path.isfile(log_file):
            continue
        
        logger = StructuredLogger(log_file)

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
                logger.log(issuer="batch_solver", event_type="general", level=logging.INFO, message="Subprocess finished with no exception.")
            except subprocess.TimeoutExpired:
                logger.log(issuer="batch_solver", event_type="error", level=logging.ERROR, message=f"Subprocess timed out after {timeout_seconds} seconds.")
            except Exception as e:
                logger.log(issuer="batch_solver", event_type="error", level=logging.ERROR, message=f"> Eexception: instance id ={instance.identifier}, err: {e}")
        # else: # python function call: mostly used for debugging
        #     try:
        #         print(f"> Starting by function call for file_name={log_file}")
        #         result = solve_instance(*cmd[2:])
        #         logger.info(f"> Python call finished.")
        #     except Exception as e:
        #         logger.error(f"> Error: instance id ={instance.identifier}, err: {e}")


def load_instance_ids(file_path='instance_ids_nonzero_h.json'):
    with open(file_path, 'r') as file:
        instance_ids = json.load(file)
    print(f"Successfully loaded {len(instance_ids)} instance IDs from JSON file.")
    return instance_ids


if __name__ == "__main__":
    benchmark_path = Path('./input/benchmarks-G1')
    search_algorithm = 'bfs'
    log_folder = Path('./exp_logs/8 BFS-full-log length1-15')
    # log_folder = Path('./exp_logs_debug')
    log_interval = 1
    timeout_seconds = 30 * 60
    order = 'increasing' # 'increasing' or 'random'
    min_length = 1
    max_length = 15
    # domain_class='blocks'
    domain_class = None
    # instance_ids = load_instance_ids()
    # instance_ids = ["blocks/pprobBLOCKS-6-2-err-rate-0-3"]
    instance_ids = []
    
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
