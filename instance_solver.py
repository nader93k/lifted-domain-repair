import cProfile
import pstats
from pstats import SortKey
from search_partial_grounding import AStar, Node, DFS, BranchBound
from search_partial_grounding.lifted_pddl_grounder import ground_pddl
#TODO: Fina a better place for ground_repair
from vanilla_runs.run_songtuans_vanilla import ground_repair
from custom_logger import StructuredLogger
from exptools import list_instances
from pathlib import Path
import logging
import time
import sys
import traceback



def solve_instance(search_algorithm, benchmark_path, log_file, log_interval, instance_id, lift_prob, heuristic_relaxation):
    start_time = time.time()

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
            , message=f"An error occurred trying to get the vanilla repair: {str(e)}\n{stack_trace}")
        raise

    log_data_gr = {
        "repair_length": len(gr.strip().split('\n')) if gr.strip() else 0,
        "repair": gr
    }
    logger.log(issuer="instance_solver", event_type="ground_repair", level=logging.INFO, message=log_data_gr)

    Node.set_grounder(ground_pddl)
    Node.set_domain(instance.planning_domain)
    Node.set_task(instance.planning_task)
    Node.set_logger(logger)
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
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    if len(sys.argv) not in (7, 8):
        print("Usage: python instance_solver.py <search_algorithm> <benchmark_path> <log_folder> <log_interval> <instance_id> <heuristic_relaxation>")
        sys.exit(1)
    
    search_algorithm = sys.argv[1]
    benchmark_path = sys.argv[2]
    benchmark_path = Path(benchmark_path)
    log_file = Path(sys.argv[3])
    log_interval = int(sys.argv[4])
    instance_id = sys.argv[5]
    lift_prob = float(sys.argv[6])
    heuristic_relaxation = sys.argv[7] if(len(sys.argv)==8) else None

    solve_instance(
        search_algorithm=search_algorithm,
        benchmark_path=benchmark_path,
        log_file=log_file,
        log_interval=log_interval,
        instance_id=instance_id,
        heuristic_relaxation=heuristic_relaxation,
        lift_prob=lift_prob
    )
