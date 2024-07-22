# astar_algorithm.py
import heapq


class AStar:
    def __init__(self, initial_node):
        self.initial_node = initial_node

    def find_path(self):
        open_list = []
        closed_set = set()

        heapq.heappush(open_list, (self.initial_node.f_cost, self.initial_node))

        while open_list:
            current_node = heapq.heappop(open_list)[1]

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

        return None, None  # No path found

    def reconstruct_path(self, node):
        path = []
        while node:
            path.append(node)
            node = node.parent
        return path[::-1]
