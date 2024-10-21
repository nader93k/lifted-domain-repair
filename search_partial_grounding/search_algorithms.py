# astar_algorithm.py
import heapq
import logging


def log_iteration_info(logger, iteration, open_list, current_node, is_goal):
    log_data = {
        "is_goal": is_goal,
        "iteration": iteration,
        "fring_size": len(open_list),
        # "fring_first_20": ", ".join(f"(D:{-nd},H:{-hc},C:{fc})" for fc, hc, nd, _ in sorted(open_list)[:20]),
        "current_node": current_node.to_dict()
    }
    logger.log(issuer="Searcher", event_type="general", level=logging.INFO, message=log_data)


class Searcher:
    def __init__(self, initial_node):
        self.initial_node = initial_node

    def find_path(self, logger, log_interval):
        raise NotImplementedError("Subclasses must implement find_path method")

    def reconstruct_path(self, node):
        path = []
        while node:
            path.append(node)
            node = node.parent
        return path[::-1]


class AStar(Searcher):
    """
    A class that implements the A* pathfinding algorithm.

    Note:
        This implementation assumes that the Node class used has the following attributes:
        - This implementation assumes no node will be generated twice, and hence won't check
        if a new node is already in the closed_list.
        - We also used list for closed_list instead of having a closed_set for the same reason.
    """


    def __init__(self, initial_node, g_cost_multiplier=1, h_cost_multiplier=1):
        super().__init__(initial_node)
        self.g_cost_multiplier = g_cost_multiplier
        self.h_cost_multiplier = h_cost_multiplier 
    

    def calculate_f_cost(self, node):  ##### Added new method to calculate f_cost
       return (self.g_cost_multiplier * node.g_cost) + self.calculate_h_cost(node)

    def calculate_h_cost(self, node):  ##### Added new method to calculate f_cost
       return self.h_cost_multiplier * node.h_cost


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

                log_iteration_info(logger, iteration, open_list, current_node, is_goal=True)
                return self.reconstruct_path(current_node), current_node

            closed_list.append(current_node)

            for neighbor in current_node.get_neighbors():
                # if neighbor in closed_list:
                #     continue

                # tentative_f_cost = neighbor.f_cost
                if not any(node[3]==neighbor for node in open_list):
                    f_cost = self.calculate_f_cost(neighbor)
                    h_cost = self.calculate_h_cost(neighbor)
                    heapq.heappush(open_list, (f_cost, h_cost, -neighbor.depth, neighbor))
                # elif tentative_f_cost >= neighbor.f_cost: continue
                else: raise Exception("Identical node generation detected. Debug is needed.")

                neighbor.parent = current_node

            if iteration % log_interval == 0:
                log_iteration_info(logger, iteration, open_list, current_node, is_goal=False)

        return None, None  # No path found


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
                log_iteration_info(
                    logger,
                    iteration,
                    ['intentionally skipped logging this'],
                    current_node,
                    is_goal=True)
                return self.reconstruct_path(current_node), current_node

            neighbors = sorted(current_node.get_neighbors(), key=lambda x: x.g_cost)
            # for neighbor in neighbors:
            #     if neighbor not in visited:
            #         stack.append(neighbor)
            # We don't need to check if neighbors are visited because each node is unique.
            # Instead, we can directly extend the stack with all neighbors.
            stack.extend(neighbors)

            if iteration % log_interval == 0:
                log_iteration_info(
                    logger,
                    iteration,
                    ['intentionally skipped logging this'],
                    current_node,
                    is_goal=False)

        return None, None  # No path found
