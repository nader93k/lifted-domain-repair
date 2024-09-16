from repairer import Repairer
from model.plan import PositivePlan, apply_action_sequence
from typing import List
import logging
import copy



class Node:
    original_domain = None
    original_task = None
    grounder = None

    @classmethod
    def set_grounder(cls, value):
        cls.grounder = value
    

    @classmethod
    def set_domain(cls, value):
        cls.original_domain = value


    @classmethod
    def set_task(cls, value):
        cls.original_task = value


    def __init__(self,
                 lifted_action_sequence: List[str],
                 ground_action_sequence: List[str],
                 parent: 'Node' = None,
                 is_initial_node: bool = False
                 ):
        if self.grounder is None:
            raise ValueError("Action grounder must be set before creating instances.")
        if self.original_domain is None:
            raise ValueError("Original domain must be set before creating instances.")
        if self.original_task is None:
            raise ValueError("Original task must be set before creating instances.")

        self.is_initial_node = is_initial_node
        self.ground_action_sequence = ground_action_sequence
        self.lifted_action_sequence = lifted_action_sequence
        self.parent = parent

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        if len(ground_action_sequence) == 0:
            # TODO: review the claim below
            # These values are arbitrary numbers and won't affect the results.
            self.g_cost = 0
            self.h_cost = 0
            self.f_cost = 0
            self.repaired_domain = copy.deepcopy(self.original_domain)
            self.ground_repair_solution = None
        else:
            self.g_cost, self.ground_repair_solution, self.repaired_domain = self._ground_repair()
            self.h_cost = self.compute_h_cost()
            self.f_cost = self.g_cost + self.h_cost


    def _ground_repair(self):
        # plan.compute_subs(domain, task)
        # succeed = plan.execute(domain, task)

        domain = copy.deepcopy(self.original_domain)
        task = self.original_task.copy()

        if len(self.lifted_action_sequence) != 0:
            task.set_goal_empty()
        plan = [PositivePlan(self.ground_action_sequence + [''])]

        repairer = Repairer()
        if repairer.repair(domain, [(task, plan)]):
            return repairer.count_repair_lines(), repairer.get_repairs_string(), domain
        else:
            return float('inf'), None, None


    def compute_h_cost(self):
        # TODO: NOT IMPLEMENTED
        # will always be run after ground_repair(), and hence works with the repaired self.planning.domain.
        # should be sth like: h(y(self.domain), d(self.task), self.lifted_action_sequence)

        return 0


    def get_neighbors(self):
        # don't try to expand this node if the cost is infinite (no repairs)
        if self.g_cost == float('inf'):
            raise ValueError("Can't expand this node.")
        
        next_action_name = self.lifted_action_sequence[0]

        task = copy.deepcopy(self.original_task)

        plan = PositivePlan(self.ground_action_sequence)
        plan.compute_subs(self.repaired_domain, task)
        state = apply_action_sequence(self.repaired_domain, task, plan)
        # state = apply_action_sequence(self.repaired_domain, task, self.ground_action_sequence)
        task.set_init_state(state)


        # initial state must be updated in the task
        possible_groundings = Node.grounder(
            self.repaired_domain,
            task,
            next_action_name
        )

        print(f'Current repairs:\n{self.ground_repair_solution}')

        print(f'current state:\n{state}')
        print(f'possible groundings:\n{possible_groundings}')

        neighbours = []
        for grounding in possible_groundings:
            next_node = Node(
                ground_action_sequence=self.ground_action_sequence + [grounding],
                lifted_action_sequence=self.lifted_action_sequence[1:],
                parent=self,
                is_initial_node=False
            )
            neighbours.append(next_node)

        print(f'Num neighbour created: {len(neighbours)}')
        return neighbours


    def is_goal(self):
        # check with @songtuan
        return len(self.lifted_action_sequence) == 0 and self.f_cost != float('inf')


    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.ground_action_sequence == other.ground_action_sequence


    def __str__(self):
        next_lifted = [] if len(self.lifted_action_sequence)==0 else self.lifted_action_sequence[0]
        return ("Node instance:"
                + "\n"
                + f"Ground actions: {self.ground_action_sequence}"
                + "\n"
                + f"Next lifted actions: {next_lifted}"
                )

    def __repr__(self):
        return self.__str__()


    def __lt__(self, other):
        return self.f_cost < other.f_cost


    def __hash__(self):
        return hash(tuple(self.ground_action_sequence))
