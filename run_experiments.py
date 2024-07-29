# Import necessary modules and classes
import os
import logging
from model.plan import Domain, Task
from astar_partial_grounding import read_ground_actions, all_action_groundings, read_action_names, AStar, Node
from pathlib import Path
from exptools import generate_instances


if __name__ == "__main__":

    benchmark_path = Path('/Users/nader/Documents/GitHub/classical-domain-repairer/input/benchmarks-G1')

    for instance in generate_instances(benchmark_path):
        instance.load_to_memory()
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
