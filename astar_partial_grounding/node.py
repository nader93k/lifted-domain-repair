from repairer import Repairer


class Node:
    action_grounding_dict = None
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

    def __init__(self
                 , white_ground_action_sequence
                 , white_lifted_action_sequence
                 , parent
                 , is_initial_node=False
                 ):
        if self.action_grounding_dict is None:
            raise ValueError("Action grounding dicts must be set before creating instances.")
        if self.planning_domain is None:
            raise ValueError("Action grounding dicts must be set before creating instances.")
        if self.planning_task is None:
            raise ValueError("Action grounding dicts must be set before creating instances.")

        if is_initial_node:
            assert white_ground_action_sequence is None and parent is None
            # These values are arbitrary numbers and won't affect the results.
            self.g_cost = 0
            self.h_cost = 0
            self.f_cost = 0
        else:
            self.g_cost, self.ground_repair_solution = self.ground_repair()
            self.h_cost = self.compute_h_cost()
            self.f_cost = self.g_cost + self.h_cost

        self.initial_node = is_initial_node
        self.white_ground_action_sequence = white_ground_action_sequence
        self.white_lifted_action_sequence = white_lifted_action_sequence
        self.parent = parent

    def ground_repair(self):
        # Side effect: after applying repairer, planning domain will be updated.
        # If current version is needed we have to take a copy.

        planning_task_empty_goal = self.planning_task.copy()
        planning_task_empty_goal.set_goal_empty()

        repairer = Repairer(
            self.planning_domain
            , [
                (
                    planning_task_empty_goal
                    , self.white_ground_action_sequence
                )
            ]
        )

        return repairer.count_repair_lines(), repairer.get_repairs_string()

    def compute_h_cost(self):
        # todo: NOT IMPLEMENTED
        # will always be run after ground_repair(), and hence works with the repaired self.planning.domain.
        # should be sth like: h(y(self.domain), d(self.task), self.white_lifted_action_sequence)

        return 0

    def get_neighbors(self):
        next_lifted_action_name = self.white_lifted_action_sequence[0]
        possible_groundings = Node.action_grounding_dict(next_lifted_action_name)

        neighbours = []
        for grounding in possible_groundings:
            next_node = Node(
                white_ground_action_sequence=self.white_ground_action_sequence + '\n' + grounding,
                white_lifted_action_sequence=self.white_lifted_action_sequence[1:],
                parent=self,
                is_initial_node=False
            )
            neighbours.append(next_node)
        return neighbours

    def is_goal(self):
        # check with @songtuan
        return len(self.white_lifted_action_sequence) == 0

    def __eq__(self, other):
        raise NotImplementedError("This method has not been implemented yet")
        return (self.white_ground_action_sequence == other.white_ground_action_sequence
                and self.white_lifted_action_sequence == other.white_lifted_action_sequence)

    def __lt__(self, other):
        return self.f_cost < other.f_cost
