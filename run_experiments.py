# Import necessary modules and classes
import os
import logging
from model.plan import Domain, Task
from astar_partial_grounding import \
    read_ground_actions, all_action_groundings, read_action_names,smart_grounder, \
    AStar, Node
from astar_partial_grounding.action_grounding_tools import smart_grounder
from pathlib import Path
from exptools import list_instances
import cProfile
import pstats
import json
import time
#TODO: Fina a better place for ground_repair
from vanilla_runs.run_songtuans_vanilla import ground_repair


def print_profile(file_name: str, num_lines=20):
    stats = pstats.Stats(file_name)
    stats.sort_stats('ncalls')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stats.print_stats(script_dir, num_lines)


def experiment(benchmark_path, log_folder, specific_instance=None):
    instance_list = list_instances(benchmark_path, specific_instance=specific_instance)
    instance_list.sort(key=lambda i: i.plan_length)

    for instance in instance_list:
        start_time = time.time()
        instance.load_to_memory()

        log_file = os.path.join(
            log_folder
            , f"length_{instance.plan_length}_" \
                + instance.domain_class \
                + '_' \
                + instance.instance_name \
                + '.txt')
        file_handler = logging.FileHandler(log_file,  mode='w')
        file_handler.setLevel(logging.INFO)
        logger = logging.getLogger(log_file)
        logger.addHandler(file_handler)

        current_time = time.localtime()
        formatted_time = time.strftime("%Y-%m-%d %H:%M:%S %Z", current_time)
        logger.info(f"> Solving the next problem at: {formatted_time}")
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
            is_initial_node=True
        )

        astar = AStar(initial_node)
        path, goal_node = astar.find_path(log_interval=200)
        if goal_node:
            logger.info(f">>> Goal found:\n{goal_node}")
        else:
            logger.info(">>> No goal found.\n")
        
    
        # Calculate time in different units
        end_time = time.time()
        elapsed_time = end_time - start_time
        seconds = elapsed_time
        minutes = elapsed_time / 60
        hours = elapsed_time / 3600
        logger.info(f"{hours:.1f} hours, {minutes:.1f} minutes, {seconds:.2f} seconds")

        file_handler.close()



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    benchmark_path = Path('./input/benchmarks-G1')
    log_folder = Path('./exp_logs/4 BFS mega-run')

    experiment(benchmark_path, log_folder)

    # cProfile.run("experiment(benchmark_path)"
    #             , 'profiler_tmp')
    # cProfile.run("experiment(benchmark_path, 'blocks/pprobBLOCKS-5-0-err-rate-0-5')"
    #             , 'profiler_tmp')

    # print_profile('exp_logs/4 BFS mega-run-less-log/profiler_blocks_less_log', 200)
