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
#TODO: Fina a better place for ground_repair
from vanilla_runs.run_songtuans_vanilla import ground_repair


def experiment(benchmark_path, specific_instance=None):
    instance_list = list_instances(benchmark_path, specific_instance=specific_instance)

    instance_list.sort(key=lambda i: i.plan_length)

    # print(f'identifier={instance.identifier}')
    # print(len(read_action_names(plan_file)))

    for instance in instance_list:
        logging.info(f"> Instance ID={instance.identifier}")
        logging.info(f"> Plan length={instance.plan_length}")
        instance.load_to_memory()
        logging.info(f"> Domain class: {instance.domain_class}")
        logging.info(f"> Instance name: {instance.instance_name}")
        logging.info(f"> Lifted plan:\n{instance.lifted_plan}")

        # Ground repair
        gr = ground_repair(
            instance.planning_domain
            , instance.planning_task
            , instance.white_plan_file)
        logging.info(f">>>  Vanilla ground repair:\n{gr}\n")
        # exit()

        # Lifted repair
        Node.set_grounder(smart_grounder)
        Node.set_domain(instance.planning_domain)
        Node.set_task(instance.planning_task)

        # Test: Input is the lifted action sequence
        initial_node = Node(
            lifted_action_sequence=instance.lifted_plan,
            ground_action_sequence=[],
            parent=None,
            is_initial_node=True
        )

        astar = AStar(initial_node)
        path, goal_node = astar.find_path(log_interval=100)

        if goal_node:
            logging.info(f"Goal found:\n{goal_node}")
        else:
            logging.info("No goal found.")


def print_profile(file_name: str, num_lines=20):
    stats = pstats.Stats(file_name)
    stats.sort_stats('ncalls')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stats.print_stats(script_dir, num_lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    benchmark_path = Path('./input/benchmarks-G1')
    cProfile.run("experiment(benchmark_path, 'blocks/pprobBLOCKS-5-0-err-rate-0-5')", 'profiler_blocks_less_log')

    # cProfile.run("experiment(benchmark_path)", 'profiler_tmp')

    print_profile('\nexp_logs/full-log_blocks/profiler_blocks_full-log', 200)
