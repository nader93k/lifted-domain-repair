# astar_algorithm.py
import heapq
import logging


class AStar:
    def __init__(self, initial_node):
        self.initial_node = initial_node
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def find_path(self):
        open_list = []
        closed_set = set()

        heapq.heappush(open_list, (self.initial_node.f_cost, self.initial_node))

        iteration = 0
        while open_list:
            iteration = iteration + 1
            current_node = heapq.heappop(open_list)[1]

            self.logger.debug(f"A* iteration {iteration}, current node:\n{current_node}")

            if current_node.is_goal():
                return self.reconstruct_path(current_node), current_node

            closed_set.add(current_node)

            for neighbor in current_node.get_neighbors():
                if neighbor in closed_set:
                    continue

                tentative_g_cost = neighbor.g_cost

                if (neighbor.f_cost, neighbor) not in open_list:
                    heapq.heappush(open_list, (neighbor.f_cost, neighbor))
                elif tentative_g_cost >= neighbor.g_cost:
                    continue

                neighbor.parent = current_node

            self.logger.info(f"\nA* iteration {iteration}.\n")
            self.logger.info(f"\nCurrent Node: {current_node}.\n")
            self.logger.debug(f"Open list:\n" + str(open_list) + f"\nClose list:\n" + str(closed_set))

        return None, None  # No path found

    def reconstruct_path(self, node):
        path = []
        while node:
            path.append(node)
            node = node.parent
        return path[::-1]
