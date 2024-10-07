from search_partial_grounding import smart_grounder, AStar, Node
from search_partial_grounding.action_grounding_tools import smart_grounder
#TODO: Fina a better place for ground_repair
from vanilla_runs.run_songtuans_vanilla import ground_repair
from custom_logger import StructuredLogger
from exptools import list_instances
from pathlib import Path
import logging
import time
import sys
import traceback


def solve_instance(search_algorithm, benchmark_path, log_file, log_interval, instance_id, heuristic_relaxation):
    log_interval = int(log_interval)
    print(benchmark_path)
    instance = list_instances(benchmark_path, instance_ids=[instance_id])[0]

    start_time = time.time()

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

    # Lifted repair
    Node.set_grounder(smart_grounder)
    Node.set_domain(instance.planning_domain)
    Node.set_task(instance.planning_task)
    Node.set_logger(logger)
    initial_node = Node(
        lifted_action_sequence=instance.lifted_plan,
        ground_action_sequence=[],
        parent=None,
        is_initial_node=True,
        h_cost_needed=True if search_algorithm in ('astar',) else False,
        heuristic_relaxation=heuristic_relaxation
    )
    match search_algorithm:
        case 'astar' | 'bfs':
            search_class = AStar
        case 'dfs':
            raise NotImplementedError
            # search_class = DFS
        case _:
            raise NotImplementedError("Search algorithm not supported.")
    searcher = search_class(initial_node)

    log_data_results = {}
    try:
        path, goal_node = searcher.find_path(logger=logger, log_interval=log_interval)
        if goal_node:
            log_data_results['goal'] = goal_node.to_dict()
        else:
            log_data_results['goal'] = 'not_found'
        logger.log(issuer="instance_solver", event_type="results", level=logging.INFO, message=log_data_results)
    except Exception as e:
        stack_trace = traceback.format_exc()
        log_data_error = f"An error occurred during A* search: {str(e)}. Stack trace: {stack_trace}"
        logger.log(issuer="instance_solver", event_type="error", level=logging.ERROR, message=log_data_error)
        path, goal_node = None, None
    
    # Logging
    end_time = time.time()
    elapsed_time = end_time - start_time
    seconds = elapsed_time
    minutes = elapsed_time / 60
    hours = elapsed_time / 3600
    time_spent = f"{hours:.1f} hours = {minutes:.1f} minutes = {seconds:.2f} seconds"
    logger.log(issuer="instance_solver", event_type="time_spent", level=logging.INFO, message=time_spent)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    if len(sys.argv) not in (6, 7):
        print("Usage: python instance_solver.py <search_algorithm> <benchmark_path> <log_folder> <log_interval> <instance_id> <heuristic_relaxation>")
        sys.exit(1)
    search_algorithm = sys.argv[1]
    benchmark_path = sys.argv[2]
    benchmark_path = Path(benchmark_path)
    log_file = Path(sys.argv[3])
    log_interval = int(sys.argv[4])
    instance_id = sys.argv[5]
    heuristic_relaxation = sys.argv[6] if(len(sys.argv)==7) else None

    solve_instance(
        search_algorithm=search_algorithm,
        benchmark_path=benchmark_path,
        log_file=log_file,
        log_interval=log_interval,
        instance_id=instance_id,
        heuristic_relaxation=heuristic_relaxation
    )
