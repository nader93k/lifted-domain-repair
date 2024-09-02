# Import necessary modules and classes
import os
import logging
from model.plan import Domain, Task
from astar_partial_grounding import \
    read_ground_actions, all_action_groundings, read_action_names,smart_grounder, \
    AStar, Node
from astar_partial_grounding.action_grounding_tools import smart_grounder
from pathlib import Path
from exptools import generate_instances
import cProfile
import pstats
import json


def experiment(benchmark_path, specific_instance=None):

    for instance in generate_instances(
            benchmark_path
            , specific_instance=specific_instance):
        instance.load_to_memory()

        print(f"Domain class: {instance.domain_class}")
        print(f"Instance name: {instance.instance_name}")


        ###### Using exaustive grounding
        # action_grounding_dict = all_action_groundings(
        #     instance.lifted_plan
        #     , instance.planning_domain
        #     , instance.planning_task)
        
        # # with open('action_grounding', 'w') as file:
        # #     json.dump(action_grounding_dict, file, indent=4)

        ###### Using smart grounding

        # print(plan[0]._steps):
        # [('pick-up', 'b'), ('stack', 'b', 'a'), ('pick-up', 'c'), ('stack', 'c', 'b'), ('pick-up', 'd'), ('stack', 'd', 'c')]

        action_grounding = smart_grounder(
            instance.planning_domain,
            instance.planning_task,
            instance.lifted_plan)


        Node.set_action_grounding(action_grounding)
        Node.set_planning_domain(instance.planning_domain)
        Node.set_planning_task(instance.planning_task)

        # Test: Input is the lifted action sequence
        initial_node = Node(
            lifted_action_sequence=instance.lifted_plan,
            ground_action_sequence=[],
            parent=None,
            is_initial_node=True
        )

        astar = AStar(initial_node)
        path, goal_node = astar.find_path()

        if goal_node:
            print("Goal found:")
            print(goal_node.ground_action_sequence)
            print('Repairs:')
            print(goal_node.ground_repair_solution)
        else:
            print("No goal found")


def print_profile(file_name: str, num_lines=20):
    stats = pstats.Stats(file_name)
    stats.sort_stats('ncalls')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stats.print_stats(script_dir, num_lines)


if __name__ == "__main__":
    benchmark_path = Path('./input/benchmarks-G1')

    cProfile.run("experiment(benchmark_path)"
                 , 'profile_output')

    print_profile('profile_output', 20)
