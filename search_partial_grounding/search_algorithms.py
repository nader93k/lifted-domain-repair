# astar_algorithm.py
import heapq
import logging


def log_iteration_info(logger, iteration, open_list, current_node, is_goal):
        log_data = {
            "is_goal": is_goal,
            "iteration": iteration,
            "fring_size": len(open_list),
            "fring_first_20": ", ".join(f"(D:{-nd},H:{-hc},C:{fc})" for fc, hc, nd, _ in sorted(open_list)[:20]),
            "current_node": current_node.to_dict()
        }
        logger.log(issuer="Searcher", event_type="general", level=logging.INFO, message=log_data)


class AStar:
    """
    A class that implements the A* pathfinding algorithm.

    Note:
        This implementation assumes that the Node class used has the following attributes:
        - This implementation assumes no node will be generated twice, and hence won't check
        if a new node is already in the closed_list.
        - We also used list for closed_list instead of having a closed_set for the same reason.
    """


    def __init__(self, initial_node):
        self.initial_node = initial_node


    def find_path(self, logger, log_interval):
        open_list = []
        closed_list = []

        heapq.heappush(open_list, (self.initial_node.f_cost, -self.initial_node.depth, self.initial_node))

        iteration = 0
        while open_list:
            iteration += 1
            current_node = heapq.heappop(open_list)[2]

            if current_node.is_goal():

                log_iteration_info(logger, iteration, open_list, current_node, is_goal=True)
                return self.reconstruct_path(current_node), current_node

            closed_list.append(current_node)

            for neighbor in current_node.get_neighbors():
                # if neighbor in closed_list:
                #     continue

                tentative_f_cost = neighbor.f_cost

                if not any(node[3]==neighbor for node in open_list):
                    heapq.heappush(open_list, (neighbor.f_cost, neighbor.h_cost, -neighbor.depth, neighbor))
                elif tentative_f_cost >= neighbor.f_cost:
                    continue

                neighbor.parent = current_node

            if iteration % log_interval == 0:
                log_iteration_info(logger, iteration, open_list, current_node, is_goal=False)

        return None, None  # No path found

    def reconstruct_path(self, node):
        path = []
        while node:
            path.append(node)
            node = node.parent
        return path[::-1]



# TODO fix the logger before using
# class DFS:
#     """
#     A class that implements the Depth-First Search algorithm with f-cost prioritization.
#     This implementation assumes that distinct nodes cannot have equal children.
#     """
#     def __init__(self, initial_node, logger):
#         self.initial_node = initial_node
#         self.logger = logger
    
#     def log_iteration_info(self, iteration, stack, current_node, is_goal):
#         if is_goal:
#             self.logger.info(f"\n==== Goal Reached at Iteration {iteration} ====")
#         self.logger.info(f"\n>>>>  DFS iteration {iteration}  <<<<\n")
#         self.logger.info(f"> Stack size: {len(stack)}\n> Top 20 nodes: " + ", ".join(f"(F:{node.f_cost},D:{node.depth})" for node in sorted(stack, key=lambda x: x.f_cost)[:20])) # <<<<<<<
#         self.logger.info(f"\n{current_node}")
#         if is_goal:
#             self.logger.info("==== End of Goal State Log ====\n")

#     def find_path(self, log_interval):
#         stack = [self.initial_node]  # <<<<<<<
#         # visited = set()  # <<<<<<<
#         # The visited set is not necessary because distinct nodes cannot have equal children.
#         # This ensures we won't revisit nodes, eliminating the need for a visited set.

#         iteration = 0
#         while stack:
#             iteration += 1
#             current_node = stack.pop()  # <<<<<<<

#             # if current_node in visited:  # <<<<<<<
#             #     continue  # <<<<<<<
#             # This check is not needed because each node is unique and won't be revisited.

#             # visited.add(current_node)  # <<<<<<<
#             # We don't need to track visited nodes for the same reason as above.

#             if current_node.is_goal():
#                 self.log_iteration_info(iteration, stack, current_node, is_goal=True)
#                 return self.reconstruct_path(current_node), current_node

#             neighbors = sorted(current_node.get_neighbors(), key=lambda x: x.f_cost)  # <<<<<<<
#             # for neighbor in neighbors:
#             #     if neighbor not in visited:  # <<<<<<<
#             #         stack.append(neighbor)  # <<<<<<<
#             # We don't need to check if neighbors are visited because each node is unique.
#             # Instead, we can directly extend the stack with all neighbors.
#             stack.extend(neighbors)  # <<<<<<<

#             if iteration % log_interval == 0:
#                 self.log_iteration_info(iteration, stack, current_node, is_goal=False)

#         return None, None  # No path found

#     def reconstruct_path(self, node):
#         path = []
#         while node:
#             path.append(node)
#             node = node.parent
#         return path[::-1]
