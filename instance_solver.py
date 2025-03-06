import cProfile
import pstats
from pstats import SortKey
from search_partial_grounding import AStar, Node, DFS, BranchBound
#TODO: Fina a better place for ground_repair
from vanilla_runs.run_songtuans_vanilla import ground_repair
from custom_logger import StructuredLogger
from exptools import list_instances
from pathlib import Path
import logging
import time
import sys
import traceback
import resource
import os
import shutil
import yaml


pid = os.getpid()
workspace_path = f'/home/remote/u7899572/lifted-white-plan-domain-repair/heuristic_tools/aux_files/{pid}'

def setup_process_workspace():
    if os.path.exists(workspace_path):
        shutil.rmtree(workspace_path)
    os.makedirs(workspace_path)
    os.chdir(workspace_path)
    return workspace_path

def cleanup_workspace():
    # Change back to parent directory before deletion
    os.chdir(os.path.dirname(workspace_path))
    # Remove the process-specific directory
    if os.path.exists(workspace_path):
        shutil.rmtree(workspace_path)


def solve_instance(config_file, instance_id):
    start_time = time.time()

    with open(config_file, 'r') as config_file:
        config = yaml.safe_load(config_file)

    search_algorithm = config['search_algorithm']
    benchmark_path = Path(config['benchmark_path'])
    lift_prob = config['lift_prob']
    heuristic_relaxation = config['heuristic_relaxation']
    use_ff = config['use_ff']
    successor_generator = config['successor_generator']

    log_interval = config['log_interval']
    log_folder = Path(config['log_folder'])
    log_file = os.path.join(log_folder, f"{instance_id}.yaml")
    

    # setup_process_workspace()
    
    log_interval = int(log_interval)
    instance = list_instances(benchmark_path, instance_ids=[instance_id], lift_prob=lift_prob)[0]
    instance.load_to_memory()
    logger = StructuredLogger(log_file)
    log_data_meta= {
        "log_file": str(log_file),
        "instance_id": instance.identifier,
        "search_algorithm": search_algorithm,
        "plan_length": instance.plan_length,
        "domain_class": instance.domain_class,
        "instance_name": instance.instance_name,
        "ground_plan": instance.ground_plan,
        "lifted_plan": instance.lifted_plan
    }
    logger.log(issuer="instance_solver", event_type="metadata", level=logging.INFO, message=log_data_meta)

    # Ground repair
    try:
        gr = ground_repair(
                instance.planning_domain
                , instance.planning_task
                , instance.white_plan_file)
    except Exception as e:
        stack_trace = traceback.format_exc()
        logger.log(issuer="instance_solver"
            , event_type="error"
            , level=logging.ERROR
            , message=f"Can't perform vanilla repair: {str(e)}\n{stack_trace}")
        exit()

    log_data_gr = {
        "repair_length": len(gr.strip().split('\n')) if gr.strip() else 0,
        "repair": gr
    }
    logger.log(issuer="instance_solver", event_type="ground_repair", level=logging.INFO, message=log_data_gr)

    Node.set_domain(instance.planning_domain)
    Node.set_task(instance.planning_task)
    Node.set_logger(logger)
    Node.set_successor_generator(successor_generator)
    Node.set_heuristic_relaxation(heuristic_relaxation)
    Node.set_use_ff(use_ff)
    initial_node = Node(
        lifted_action_sequence=instance.lifted_plan,
        ground_action_sequence=[],
        parent=None,
        is_initial_node=True,
        h_cost_needed=False if search_algorithm in ('dfs', 'bfs') else True,
        heuristic_relaxation=heuristic_relaxation
    )

    if search_algorithm == 'astar':
        searcher = AStar(initial_node, g_cost_multiplier=1, h_cost_multiplier=1)
    elif search_algorithm == 'g_astar':
        searcher = AStar(initial_node, g_cost_multiplier=1, h_cost_multiplier=2)
    elif search_algorithm == 'bfs':
        searcher = AStar(initial_node, g_cost_multiplier=1, h_cost_multiplier=0)
    elif search_algorithm == 'greedy':
        searcher = AStar(initial_node, g_cost_multiplier=0, h_cost_multiplier=1)
    elif search_algorithm == 'dfs':
        searcher = DFS(initial_node)
    elif search_algorithm == 'bb':
        searcher = BranchBound(initial_node)
    else:
        raise NotImplementedError("Search algorithm not supported.")

    try:
        searcher.find_path(logger=logger, log_interval=log_interval)
    except Exception as e:
        stack_trace = traceback.format_exc()
        logger.log(issuer="instance_solver", event_type="error", level=logging.ERROR,
            message=f"An error occurred during A* search: {str(e)}. Stack trace: {stack_trace}")
    
    # Time measure
    end_time = time.time()
    elapsed_time = end_time - start_time
    time_spent = f"{elapsed_time:.2f}"
    logger.log(issuer="instance_solver", event_type="timer_seconds", level=logging.INFO, message=time_spent)


if __name__ == "__main__":
    size = 8 * 1024 * 1024 * 1024  # 8GB in bytes
    resource.setrlimit(resource.RLIMIT_AS, (size, size))

    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    config_file = sys.argv[1]
    instance_id = sys.argv[2]

    solve_instance(
        config_file=config_file,
        instance_id=instance_id
    )
