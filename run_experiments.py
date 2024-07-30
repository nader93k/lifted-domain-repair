# Import necessary modules and classes
import os
import logging
from model.plan import Domain, Task
from astar_partial_grounding import read_ground_actions, all_action_groundings, read_action_names, AStar, Node
from pathlib import Path
from exptools import generate_instances
import cProfile

benchmark_path = Path('/Users/naderkarimi/Code/GitHub/nader-classical-domain-repairer/input/benchmarks-G1')


def experiment(benchmark_path=benchmark_path):

    for instance in generate_instances(benchmark_path):
        instance.load_to_memory()

        if instance.domain_class == 'agricola-opt18-strips' and instance.instance_name == 'pp04-err-rate-0-5':
            print(f"Domain class: {instance.domain_class}")
            print(f"Instance name: {instance.instance_name}")

            action_grounding_dict = all_action_groundings(
                instance.lifted_plan
                , instance.planning_domain
                , instance.planning_task)

            # All data on memory here

            Node.set_action_grounding_dict(action_grounding_dict)
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
            print("Goal found:")
            print(goal_node.ground_action_sequence)
            print('Repairs:')
            print(goal_node.ground_repair_solution)

            break


if __name__ == "__main__":
    cProfile.run('experiment()')
