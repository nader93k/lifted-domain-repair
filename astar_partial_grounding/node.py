from repairer import Repairer
from model.plan import PositivePlan
from typing import List, Optional
import logging


# Delete This
from hitter.maxsat import *
from model.plan import *



class Node:
    action_grounding_dict: dict = None
    planning_domain = None
    planning_task = None

    @classmethod
    def set_action_grounding_dict(cls, value):
        if cls.action_grounding_dict is None:
            cls.action_grounding_dict = value
        else:
            raise ValueError("Action grounding dict has already been set and cannot be changed.")

    @classmethod
    def set_planning_domain(cls, value):
        if cls.planning_domain is None:
            cls.planning_domain = value
        else:
            raise ValueError("Planning domain has already been set and cannot be changed.")

    @classmethod
    def set_planning_task(cls, value):
        if cls.planning_task is None:
            cls.planning_task = value
        else:
            raise ValueError("Planning task has already been set and cannot be changed.")

    def __init__(self,
                 lifted_action_sequence: List[str],
                 ground_action_sequence: List[str],
                 parent: 'Node' = None,
                 is_initial_node: bool = False
                 ):
        if self.action_grounding_dict is None:
            raise ValueError("Action grounding dicts must be set before creating instances.")
        if self.planning_domain is None:
            raise ValueError("Action grounding dicts must be set before creating instances.")
        if self.planning_task is None:
            raise ValueError("Action grounding dicts must be set before creating instances.")

        self.initial_node = is_initial_node
        self.ground_action_sequence = ground_action_sequence
        self.lifted_action_sequence = lifted_action_sequence
        self.parent = parent

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        if is_initial_node:
            assert len(ground_action_sequence) == 0 and parent is None
            # todo: review the claim below
            # These values are arbitrary numbers and won't affect the results.
            self.g_cost = 0
            self.h_cost = 0
            self.f_cost = 0
        else:
            self.g_cost, self.ground_repair_solution = self.ground_repair()
            self.h_cost = self.compute_h_cost()
            self.f_cost = self.g_cost + self.h_cost

    def ground_repair(self):
        # Side effect: after applying repairer, planning domain will be updated.
        # If current version is needed we have to take a copy.

        planning_task = self.planning_task.copy()
        # if len(self.lifted_action_sequence) != 0:
        #     planning_task.set_goal_empty()
        plan = [PositivePlan(self.ground_action_sequence + [''])]

        # self.logger.debug(f"Planning domain: {self.planning_domain.action_sequence}\n")
        self.logger.info(f"Task: {planning_task}\n")
        self.logger.info(f"Plan: {plan[0].action_sequence}\n")

        if bool(planning_task._goal):
            x = 1

        repairer = Repairer()

        repairer.repair(
            self.planning_domain
            , [(planning_task, plan)]
        )

        return repairer.count_repair_lines(), repairer.get_repairs_string()

    def compute_h_cost(self):
        # todo: NOT IMPLEMENTED
        # will always be run after ground_repair(), and hence works with the repaired self.planning.domain.
        # should be sth like: h(y(self.domain), d(self.task), self.lifted_action_sequence)

        return 0

    def get_neighbors(self):
        next_lifted_action_name = self.lifted_action_sequence[0]
        possible_groundings = Node.action_grounding_dict[next_lifted_action_name]

        neighbours = []
        for grounding in possible_groundings:
            next_node = Node(
                ground_action_sequence=self.ground_action_sequence + [grounding],
                lifted_action_sequence=self.lifted_action_sequence[1:],
                parent=self,
                is_initial_node=False
            )
            neighbours.append(next_node)
        return neighbours

    def is_goal(self):
        # check with @songtuan
        return len(self.lifted_action_sequence) == 0

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.ground_action_sequence == other.ground_action_sequence

    def __str__(self):
        return ("Node instance:"
                + "\n"
                + f"Ground actions: {self.ground_action_sequence}"
                + "\n"
                + f"Lifted actions: {self.lifted_action_sequence}"
                + "\n"
                )

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return self.f_cost < other.f_cost

    def __hash__(self):
        return hash(tuple(self.ground_action_sequence))
