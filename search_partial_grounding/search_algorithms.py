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
            "current_node": current_node.to_dict()
        }
        event_type = "final" if final else "general"
        logger.log(issuer="searcher", event_type=event_type, level=logging.INFO, message=log_data)


class AStar(Searcher):
    """
    A class that implements the A* pathfinding algorithm.

    Note:
        This implementation assumes that the Node class used has the following attributes:
        - This implementation assumes no node will be generated twice, and hence won't check
        if a new node is already in the closed_list.
        - We also used list for closed_list instead of having a closed_set for the same reason.
    """


    def __init__(self, initial_node, g_cost_multiplier=1, h_cost_multiplier=1, prune_func=None):
        super().__init__(initial_node)
        self.g_cost_multiplier = g_cost_multiplier
        self.h_cost_multiplier = h_cost_multiplier 
        self.prune_func = prune_func or (lambda _: False)  # Default to never prune if no function provided
    

    def calculate_f_cost(self, node):
        f = (self.g_cost_multiplier * node.g_cost) + self.calculate_h_cost(node)
        self.sum_f_cost += f
        return f

    def calculate_h_cost(self, node):
        h = self.h_cost_multiplier * node.h_cost
        self.sum_h_cost += h
        return h


    def find_path(self, logger, log_interval):
        open_list = []
        closed_list = []

        f_cost = self.calculate_f_cost(self.initial_node)
        h_cost = self.calculate_h_cost(self.initial_node)
        heapq.heappush(open_list, (f_cost, h_cost, -self.initial_node.depth, self.initial_node))

        iteration = 0
        while open_list:
            iteration += 1
            current_node = heapq.heappop(open_list)[3]

            if current_node.is_goal():
                self.log_iteration_info(logger, iteration, open_list, current_node, final=True, is_goal=True)
                return self.reconstruct_path(current_node), current_node

            closed_list.append(current_node)

            neighbours = current_node.get_neighbors()
            self.num_nodes_generated += len(neighbours)
            self.sum_h_cost_time += current_node.h_cost_time
            self.sum_grounding_time += current_node.grounding_time

            for neighbor in neighbours:
                if not any(node[3]==neighbor for node in open_list):
                    if not self.prune_func(neighbor):
                        f_cost = self.calculate_f_cost(neighbor)
                        h_cost = self.calculate_h_cost(neighbor)
                        heapq.heappush(open_list, (f_cost, h_cost, -neighbor.depth, neighbor))
                # elif tentative_f_cost >= neighbor.f_cost: continue
                else: raise Exception("Identical node generation. Debug is needed.")

                neighbor.parent = current_node

            if iteration % log_interval == 0:
                self.log_iteration_info(logger, iteration, open_list, current_node, final=True, is_goal=False)

        self.log_iteration_info(logger, iteration, open_list, current_node, final=True, is_goal=False)
        return None, None  # No path found


class BranchBound(Searcher):
    def __init__(self, initial_node):
        super().__init__(initial_node)

    def prune_strategy(self, node, current_best_cost):
        """
        Default pruning strategy that decides whether to prune a node based on its cost.
        
        Args:
            node: The node to evaluate for pruning
            current_best_cost: The cost of the current best solution
            
        Returns:
            bool: True if the node should be pruned, False otherwise
        """
        return node.h_cost + node.g_cost >= current_best_cost
    
    def find_path(self, logger, log_interval):
        current_best_cost = float('inf')
        while True:
            #TODO add error handling for this
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
    """
    A class that implements the Depth-First Search algorithm with f-cost prioritization.
    This implementation assumes that distinct nodes cannot have equal children.
    """
    def __init__(self, initial_node):
        super().__init__(initial_node)

    def find_path(self, logger, log_interval):
        stack = [self.initial_node]
        # visited = set()
        # The visited set is not necessary because distinct nodes cannot have equal children.
        # This ensures we won't revisit nodes, eliminating the need for a visited set.

        iteration = 0
        while stack:
            iteration += 1
            current_node = stack.pop()

            # if current_node in visited:
            #     continue
            # This check is not needed because each node is unique and won't be revisited.
            # visited.add(current_node)
            # We don't need to track visited nodes for the same reason as above.

            if current_node.is_goal():
                self.log_iteration_info(
                    logger,
                    iteration,
                    ['not logged'],
                    current_node,
                    final=True,
                    is_goal=True)
                return self.reconstruct_path(current_node), current_node

            neighbors = sorted(current_node.get_neighbors(), key=lambda x: x.g_cost)
            self.num_nodes_generated += len(neighbours)
            stack.extend(neighbors)
            # for neighbor in neighbors:
            #     if neighbor not in visited:
            #         stack.append(neighbor)
            # We don't need to check if neighbors are visited because each node is unique.
            # Instead, we can directly extend the stack with all neighbors.
            if iteration % log_interval == 0:
                self.log_iteration_info(
                    logger,
                    iteration,
                    ['not logged'],
                    current_node,
                    final=True,
                    is_goal=False)

        self.log_iteration_info(
                    logger,
                    iteration,
                    ['not logged'],
                    current_node,
                    final=True,
                    is_goal=False)
        
        return None, None  # No path found
