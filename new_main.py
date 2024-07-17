# Import necessary modules and classes
from repairer import *
from model.plan import *
import os
import argparse
import astar


# parser = argparse.ArgumentParser()
# parser.add_argument("--input_directory", type=str)
# parser.add_argument("--domain_file", type=str, default="domain.pddl")
# parser.add_argument("--task_file", type=str, default="task.pddl")
# parser.add_argument("--white_plan_file", type=str, default="white_plan.pddl")
#
# parser.add_argument("--output_directory", type=str,
#                     help="the output file containing found repairs")
#
# args = parser.parse_args()


input_directory = r"/Users/naderkarimi/Code/GitHub/nader-classical-domain-repairer/input/block_world/AAAI25-example1"
domain_file = "domain.pddl"
task_file = "task.pddl"
white_plan_file = "white_plan_lifted.pddl"

output_directory = r"/Users/naderkarimi/Code/GitHub/nader-classical-domain-repairer/output"


domain_file = os.path.join(input_directory, domain_file)
task_file = os.path.join(input_directory, task_file)
white_plan_file = os.path.join(input_directory, white_plan_file)
out_file = os.path.join(output_directory, "repairs")


def distance_g(n1, n2):
    pass

def distance_h(n1, n2):
    pass




class Node:
    def __init__(self, domain, task, grounded_actions, g):
        self.domain = domain
        self.task = task
        self.grounded_actions = grounded_actions
        self.g = g


class Solver(astar.AStar):
    __slots__ = ()

    # @abstractmethod
    def heuristic_cost_estimate(self, current: T, goal: T) -> float:
        """
        Computes the estimated (rough) distance between a node and the goal.
        The second parameter is always the goal.
        This method must be implemented in a subclass.
        """
        raise NotImplementedError

    @abstractmethod
    def distance_between(self, n1: T, n2: T) -> float:
        """
        Gives the real distance between two adjacent nodes n1 and n2 (i.e n2
        belongs to the list of n1's neighbors).
        n2 is guaranteed to belong to the list returned by the call to neighbors(n1).
        This method must be implemented in a subclass.
        """

    @abstractmethod
    def neighbors(self, node: T) -> Iterable[T]:
        """
        For a given node, returns (or yields) the list of its neighbors.
        This method must be implemented in a subclass.
        """
        raise NotImplementedError

    def _neighbors(self, current: SearchNode[T], search_nodes: SearchNodeDict[T]) -> Iterable[SearchNode]:
        return (search_nodes[n] for n in self.neighbors(current.data))

    def is_goal_reached(self, current: T, goal: T) -> bool:
        """
        Returns true when we can consider that 'current' is the goal.
        The default implementation simply compares `current == goal`, but this
        method can be overwritten in a subclass to provide more refined checks.
        """
        return current == goal

    def reconstruct_path(self, last: SearchNode, reversePath=False) -> Iterable[T]:
        def _gen():
            current = last
            while current:
                yield current.data
                current = current.came_from

        if reversePath:
            return _gen()
        else:
            return reversed(list(_gen()))


def get_path(n1, n2):
    """ runs a_star"""


    def distance(n1, n2):
        """computes the distance between two stations"""
        latA, longA = n1.position
        latB, longB = n2.position
        # convert degres to radians!!
        latA, latB, longA, longB = map(
            lambda d: d * math.pi / 180, (latA, latB, longA, longB))
        x = (longB - longA) * math.cos((latA + latB) / 2)
        y = latB - latA
        return math.hypot(x, y)

    return astar.find_path(s1, s2, neighbors_fnct=lambda s: s.links, heuristic_cost_estimate_fnct=distance, distance_between_fnct=distance)


def read_action_names(file_path):
    result = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith(';'):
                result.append(line)
    return result

# if __name__ == '__main__':
#     PASS

if __name__ == '__main__':
    domain = Domain(domain_file)
    task = Task(task_file)
    # white_plan_list = [PositivePlan(white_plan_file)]
    white_action_names = read_action_names(white_plan_file)

    for name in white_action_names:
        print(domain.get_action(name))




    # repairer = Repairer(
    #     domain
    #     , [(task, white_plan_list)]
    # )
    #
    # repairer.write(out_file)
