from repairer import Repairer


class Node:
    action_grounding_dict = None

    @classmethod
    def set_action_grounding_dict(cls, value):
        if cls.action_grounding_dict is None:
            cls.action_grounding_dict = value
        else:
            raise ValueError("Action grounding dicts have already been set and cannot be changed.")

    def __init__(self
                 , planning_domain
                 , planning_task
                 , white_ground_action_sequence
                 , white_lifted_action_sequence
                 , parent
                 , is_initial_node=False
                 ):
        if self.action_grounding_dict is None:
            raise ValueError("Action grounding dicts must be set before creating instances.")

        if is_initial_node:
            assert white_ground_action_sequence is None and parent is None
            # These values are arbitrary numbers and won't affect the results.
            self.g_cost = 0
            self.h_cost = 0
            self.f_cost = 0
        else:
            self.g_cost, self.g_repair = self.ground_repair()
            # self.repaired_planning_domain = repair(self.g_repair)
            self.h_cost = self.compute_h_cost()
            self.f_cost = self.g_cost + self.h_cost

        self.planning_domain = planning_domain
        self.planning_task = planning_task
        self.white_ground_action_sequence = white_ground_action_sequence
        self.white_lifted_action_sequence = white_lifted_action_sequence
        self.parent = parent

    def ground_repair(self):
        # todo
        # pass empty set as planning task
        # save the repairs in class so that we can apply them before computing h
        # question: how does self.domain._updated_actions help here after applying the repair?
        # will we use that in h?
        # should we worry about deep copying because repairing permanently affects our domain?
        repairer = Repairer(
            self.planning_domain
            , [(self.planning_task, self.white_ground_action_sequence)]
        )

        raise NotImplementedError("This method has not been implemented yet")
        return repairer.count_repair_lines(), repairer.get_repairs_string()


    def compute_h_cost(self):
        # apply the repairs that we got by running "ground_repair" function
        #  only uses self.white_lifted_action_sequence
        # should be sth like:
        # h(y(self.domain), d(self.task), self.white_lifted_action_sequence)

        raise NotImplementedError("This method has not been implemented yet")

    def get_neighbors(self):
        raise NotImplementedError("This method has not been implemented yet")

    def is_goal(self):
        # check with @songtuan
        return len(self.white_lifted_action_sequence) == 0

    def __eq__(self, other):
        raise NotImplementedError("This method has not been implemented yet")
        # return (self.planning_domain == other.planning_domain and
        #         self.planning_task == other.planning_task and
        #         self.white_ground_action_sequence == other.white_ground_action_sequence and
        #         self.white_lifted_action_sequence == other.white_lifted_action_sequence)

    def __lt__(self, other):
        return self.f_cost < other.f_cost
