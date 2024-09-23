# astar_algorithm.py
import heapq
import logging


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

    def find_path(self):
        open_list = []
        closed_list = []

        heapq.heappush(open_list, (self.initial_node.f_cost, -self.initial_node.depth, self.initial_node))

        iteration = 0
        while open_list:
            iteration += 1
            current_node = heapq.heappop(open_list)[2]

            if current_node.is_goal():
                return self.reconstruct_path(current_node), current_node

            closed_list.append(current_node)

            for neighbor in current_node.get_neighbors():
                # if neighbor in closed_list:
                #     continue

                tentative_f_cost = neighbor.f_cost

                if not any(node[2]==neighbor for node in open_list):
                    heapq.heappush(open_list, (neighbor.f_cost, -neighbor.depth, neighbor))
                elif tentative_f_cost >= neighbor.f_cost:
                    continue

                neighbor.parent = current_node

            logging.info(f"\n>>>>  A* iteration {iteration}  <<<<\n")
            logging.info(f"> Fringe size: {len(open_list)}\n> First 20 nodes: " + ", ".join(f"(D:{-nd},C:{fc})" for fc, nd, _ in sorted(open_list)[:20]))
            logging.info(f"\n{current_node}")

        return None, None  # No path found

    def reconstruct_path(self, node):
        path = []
        while node:
            path.append(node)
            node = node.parent
        return path[::-1]
