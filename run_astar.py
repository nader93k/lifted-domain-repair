# Import necessary modules and classes
import os
from model.plan import *
from astar_partial_grounding import all_action_groundings, read_action_names, AStar, Node


input_directory = r"./input/block_world/AAAI25-example1"
domain_file = "domain.pddl"
task_file = "task.pddl"
white_plan_grounded_file = "white_plan_grounded.pddl"
white_plan_lifted_file = "white_plan_lifted.pddl"
output_directory = r"./output"

domain_file = os.path.join(input_directory, domain_file)
task_file = os.path.join(input_directory, task_file)
white_plan_grounded_file = os.path.join(input_directory, white_plan_grounded_file)
white_plan_lifted_file = os.path.join(input_directory, white_plan_lifted_file)
out_file = os.path.join(output_directory, "repairs")


if __name__ == "__main__":
    with open(domain_file, 'r') as f:
        file_content = f.read()
        domain = Domain(file_content)

    with open(task_file, 'r') as f:
        file_content = f.read()
        task = Task(file_content)

    lifted_action_names = read_action_names(white_plan_lifted_file)
    action_grounding_dict = all_action_groundings(white_plan_lifted_file, domain, task)

    # # test creating a plan from a string
    # with open(white_plan_grounded_file, 'r') as f:
    #     test_string = f.read()
    # test_plan = [PositivePlan(Plan.from_string(test_string))]

    Node.set_action_grounding_dict(action_grounding_dict)
    Node.set_planning_domain(domain)
    Node.set_planning_task(task)

    # Create the initial node
    initial_node = Node(
        white_ground_action_sequence='',
        white_lifted_action_sequence=lifted_action_names,
        parent=None,
        is_initial_node=True
    )

    # Run A* algorithm
    astar = AStar(initial_node)
    path, goal_node = astar.find_path()

    if path:
        print("Path found!")
        for node in path:
            print(node.white_ground_action_sequence)
    else:
        print("No path found.")
