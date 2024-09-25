from search_partial_grounding import smart_grounder, AStar, DFS, Node
from search_partial_grounding.action_grounding_tools import smart_grounder
#TODO: Fina a better place for ground_repair
from vanilla_runs.run_songtuans_vanilla import ground_repair
from logging_config import setup_logging
from exptools import list_instances
from pathlib import Path
import logging
import time
import sys


def solve_instance(search_algorithm, benchmark_path, log_file, log_interval, instance_id):
    instance = list_instances(benchmark_path, instance_id=instance_id)[0]

    start_time = time.time()

    instance.load_to_memory()

    logger = setup_logging(log_file)
    
    current_time = time.localtime()
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S %Z", current_time)
    logger.info(f"> Solving the next problem at: {formatted_time}")
    logger.info(f"> Search algorithm: {search_algorithm}")
    logger.info(f"> Instance ID={instance.identifier}")
    logger.info(f"> Plan length={instance.plan_length}")
    logger.info(f"> Domain class: {instance.domain_class}")
    logger.info(f"> Instance name: {instance.instance_name}")
    logger.info(f"> Ground plan:\n{instance.ground_plan}")
    logger.info(f"> Lifted plan:\n{instance.lifted_plan}")

    # Ground repair
    gr = ground_repair(
        instance.planning_domain
        , instance.planning_task
        , instance.white_plan_file)
    logger.info(f">>>  Vanilla ground repair:\n{gr}\n")

    # Lifted repair
    Node.set_grounder(smart_grounder)
    Node.set_domain(instance.planning_domain)
    Node.set_task(instance.planning_task)
    initial_node = Node(
        lifted_action_sequence=instance.lifted_plan,
        ground_action_sequence=[],
        parent=None,
        is_initial_node=True,
        h_cost_needed=True if search_algorithm in ('astar',) else False
    )
    match search_algorithm:
        case 'astar' | 'bfs':
            search_class = AStar
        case 'dfs':
            search_class = DFS
        case _:
            raise NotImplementedError("Search algorithm not supported.")
    searcher = search_class(initial_node, logger=logger)
    try:
        path, goal_node = searcher.find_path(log_interval=log_interval)
        if goal_node:
            logger.info(f">>> Goal found:\n{goal_node}")
        else:
            logger.info(">>> No goal found.\n")
    except Exception as e:
        logger.error(f"An error occurred during A* search: {str(e)}")
        path, goal_node = None, None
    
    # Logging ...
    end_time = time.time()
    elapsed_time = end_time - start_time
    seconds = elapsed_time
    minutes = elapsed_time / 60
    hours = elapsed_time / 3600
    logger.info(f"> Time spent on this problem: {hours:.1f} hours = {minutes:.1f} minutes = {seconds:.2f} seconds")


# def example():
#     benchmark_path = Path('./input/benchmarks-G1')
#     # log_folder = Path('./exp_logs/4 BFS mega-run')
#     log_folder = Path('./exp_logs_debug')

#     solve_instance(search_algorithm=AStar
#               , benchmark_path=benchmark_path
#               , log_folder=log_folder
#               , log_interval=200
#               , instance_id='blocks/pprobBLOCKS-5-0-err-rate-0-5')

    # cProfile.run("experiment(benchmark_path)", 'profiler_tmp')


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    # example()

    # Parse args
    if len(sys.argv) != 6:
        print("Usage: python instance_solver.py <search_algorithm> <benchmark_path> <log_folder> <log_interval> <instance_id>")
        sys.exit(1)
    search_algorithm = sys.argv[1]
    benchmark_path = Path(sys.argv[2])
    log_file = Path(sys.argv[3])
    log_interval = int(sys.argv[4])
    instance_id = sys.argv[5]

    solve_instance(
        search_algorithm=search_algorithm,
        benchmark_path=benchmark_path,
        log_file=log_file,
        log_interval=log_interval,
        instance_id=instance_id
    )
