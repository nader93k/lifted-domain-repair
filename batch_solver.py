from logging_config import setup_logging
from exptools import list_instances, smart_instance_generator
from pathlib import Path
import os
import logging
import pstats
import subprocess



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


def run_process(search_algorithm, benchmark_path, log_folder, log_interval, instance_id=None):
    instance_list = list_instances(benchmark_path, instance_id=instance_id)
    
    # instance_list.sort(key=lambda i: i.plan_length)

    for instance in smart_instance_generator(instance_list, 5, 15):
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
        # 30 minutes in seconds
        timeout_seconds = 30 * 60
        # timeout_seconds = 15
        try:
            print(f"> Starting a subprocess search for file_name={log_file}")
            result = subprocess.run(cmd, check=True, timeout=timeout_seconds)
            logger.info(f"> Subprocess finished.")
        except subprocess.TimeoutExpired:
            logger.error("> Command timed out after 30 minutes")
        except subprocess.CalledProcessError as e:
            logger.error(f"> Error: instance id ={instance.identifier}, err: {e}")


# instance_id_example: 'blocks/pprobBLOCKS-5-0-err-rate-0-5'
if __name__ == "__main__":
    search_algorithm = 'bfs'
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    benchmark_path = Path('./input/benchmarks-G1')
    log_folder = Path('./exp_logs/4 BFS mega-run')
    # log_folder = Path('./exp_logs/6 ASTAR mega-run full-log-heauristic0')
    # log_folder = Path('./exp_logs_debug')
    # log_folder = Path('./exp_logs/7 Songtuan Vanilla')
    log_interval = 200
    
    run_process(search_algorithm=search_algorithm
               , benchmark_path=benchmark_path
               , log_folder=log_folder
               , log_interval=log_interval
               , instance_id=None)
