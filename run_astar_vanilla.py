# Import necessary modules and classes
import os
import logging
from model.plan import Domain, Task
from astar_partial_grounding import read_ground_actions, all_action_groundings, read_action_names, AStar, Node


input_directory = r"./input/dummy_block_world/AAAI25-example1"
domain_file = "domain.pddl"
task_file = "task.pddl"
white_plan_file = "white_plan_grounded.pddl"
output_directory = r"./output"

domain_file = os.path.join(input_directory, domain_file)
task_file = os.path.join(input_directory, task_file)
white_plan_file = os.path.join(input_directory, white_plan_file)
out_file = os.path.join(output_directory, "repairs")


if __name__ == "__main__":
    # logging.basicConfig(
    #     filename='./output/log.txt',
    #     filemode='w',
    #     level=logging.DEBUG,
    #     format='%(message)s'
    # )

    with open(domain_file, 'r') as f:
        file_content = f.read()
        domain = Domain(file_content)

    with open(task_file, 'r') as f:
        file_content = f.read()
        task = Task(file_content)
        task.set_goal_empty()

    ground_action_sequence = read_ground_actions(white_plan_file)
    lifted_action_names = read_action_names(white_plan_file)

    action_grounding_dict = all_action_groundings(lifted_action_names, domain, task)

    Node.set_grounder(action_grounding_dict)
    Node.set_domain(domain)
    Node.set_task(task)

    # Test: Input is the lifted action sequence
    initial_node = Node(
        lifted_action_sequence=lifted_action_names,
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

    # # Test: Input is the grounded action sequence
    # initial_node = Node(
    #     lifted_action_sequence=[],
    #     ground_action_sequence=ground_action_sequence,
    #     parent=None,
    #     is_initial_node=True
    # )
    # astar = AStar(initial_node)
    # path, goal_node = astar.find_path()
    # print("Goal found:")
    # print(goal_node.ground_action_sequence)
