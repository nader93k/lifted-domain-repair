import logging
import heapq


class Searcher:
    def __init__(self, initial_node):
        self.initial_node = initial_node
        self.num_nodes_generated = 1
        self.sum_h_cost = 0
        self.sum_f_cost = 0
        self.sum_h_cost_time = 0
        self.sum_grounding_time = 0
        self.h_max = float('-inf')

    def find_path(self, logger, log_interval):
        raise NotImplementedError("Subclasses must implement find_path method")

    def reconstruct_path(self, node):
        path = []
        while node:
            path.append(node)
            node = node.parent
        return path[::-1]
    
    def log_iteration_info(self, logger, iteration, open_list, current_node, final, is_goal):
        log_data = {
            "final": final,
            "is_goal": is_goal,
            "iteration": iteration,
            "fring_size": len(open_list),
            "num_nodes_generated": self.num_nodes_generated,
            "sum_h_cost": self.sum_h_cost,
            "sum_f_cost": self.sum_f_cost,
            "sum_h_cost_time": self.sum_h_cost_time,
            "sum_grounding_time": self.sum_grounding_time,
            "h_max": self.h_max,
            "current_node": current_node.to_dict(include_state=False)
        }
        event_type = "final" if final else "general"
        logger.log(issuer="searcher", event_type=event_type, level=logging.INFO, message=log_data)


class AStar(Searcher):
    """AStar tree search with tie breakers of: 1. h_cost 2. depth"""
    def __init__(self, initial_node, g_cost_multiplier=1, h_cost_multiplier=1, prune_func=None):
        super().__init__(initial_node)
        self.g_cost_multiplier = g_cost_multiplier
        self.h_cost_multiplier = h_cost_multiplier 
        self.prune_func = prune_func or (lambda _: False)
    
    def calculate_f_cost(self, node):
        f = (self.g_cost_multiplier * node.g_cost) + self.calculate_h_cost(node)
        self.sum_f_cost += f
        return f

    def calculate_h_cost(self, node):
        h = self.h_cost_multiplier * node.h_cost
        self.sum_h_cost += h
        self.h_max = max(self.h_max, h) 
        return h

    def find_path(self, logger, log_interval):
        open_list = []

        f_cost = self.calculate_f_cost(self.initial_node)
        h_cost = self.calculate_h_cost(self.initial_node)
        heapq.heappush(open_list, (f_cost, h_cost, -self.initial_node.depth, self.initial_node))

        iteration = 0
        while open_list:
            iteration += 1
            current_node = heapq.heappop(open_list)[-1]

            if current_node.is_goal():
                self.log_iteration_info(logger, iteration, open_list, current_node, final=True, is_goal=True)
                return None, current_node

            neighbours = current_node.get_neighbors()
            self.num_nodes_generated += len(neighbours)
            self.sum_h_cost_time += current_node.h_cost_time
            self.sum_grounding_time += current_node.grounding_time

            for neighbor in neighbours:
                if not any(node[-1]==neighbor for node in open_list):
                    if not self.prune_func(neighbor):
                        f_cost = self.calculate_f_cost(neighbor)
                        h_cost = self.calculate_h_cost(neighbor)
                        heapq.heappush(open_list, (f_cost, h_cost, -neighbor.depth, neighbor))
                else: 
                    raise Exception("Identical node generation. Debug is needed.")

            if iteration % log_interval == 0:
                self.log_iteration_info(logger, iteration, open_list, current_node, final=True, is_goal=False)

        self.log_iteration_info(logger, iteration, open_list, current_node, final=True, is_goal=False)
        return None, None


class BranchBound(Searcher):
    def __init__(self, initial_node):
        super().__init__(initial_node)

    def prune_strategy(self, node, current_best_cost):
        return node.h_cost + node.g_cost >= current_best_cost
    
    def find_path(self, logger, log_interval):
        current_best_cost = float('inf')
        while True:
            searcher = AStar(self.initial_node,
                             g_cost_multiplier=0,
                             h_cost_multiplier=1,
                             prune_func=lambda node: self.prune_strategy(node, current_best_cost)
            )
            _, goal_node = searcher.find_path(logger=logger, log_interval=log_interval)
            if not goal_node:
                break
            current_best_cost = goal_node.g_cost


class DFS(Searcher):
    """DFS tree search"""
    def __init__(self, initial_node):
        super().__init__(initial_node)

    def find_path(self, logger, log_interval):
        stack = [self.initial_node]
        iteration = 0
        
        while stack:
            iteration += 1
            current_node = stack.pop()

            if current_node.is_goal():
                self.log_iteration_info(logger, iteration, ['not logged'], current_node, final=True, is_goal=True)
                return None, current_node

            neighbors = sorted(current_node.get_neighbors(), key=lambda x: x.g_cost, reverse=True)
            self.num_nodes_generated += len(neighbors)
            self.sum_h_cost_time += current_node.h_cost_time
            self.sum_grounding_time += current_node.grounding_time
            
            for neighbor in neighbors:
                stack.append(neighbor)

            if iteration % log_interval == 0:
                self.log_iteration_info(logger, iteration, ['not logged'], current_node, final=False, is_goal=False)

        self.log_iteration_info(logger, iteration, ['not logged'], current_node, final=True, is_goal=False)
        return None, None