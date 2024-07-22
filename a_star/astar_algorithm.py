# astar/astar_algorithm.py
from .node import Node
import heapq

class AStar:
    def __init__(self, grid):
        self.grid = grid

    def find_path(self, start, goal):
        start_node = Node(start, 0, self.heuristic(start, goal))
        open_list = []
        closed_set = set()

        heapq.heappush(open_list, (start_node.f_cost, start_node))

        while open_list:
            current_node = heapq.heappop(open_list)[1]

            if current_node.position == goal:
                return self.reconstruct_path(current_node)

            closed_set.add(current_node.position)

            for neighbor in self.get_neighbors(current_node):
                if neighbor.position in closed_set:
                    continue

                tentative_g_cost = current_node.g_cost + 1

                if (neighbor.f_cost, neighbor) not in open_list:
                    heapq.heappush(open_list, (neighbor.f_cost, neighbor))
                elif tentative_g_cost >= neighbor.g_cost:
                    continue

                neighbor.parent = current_node
                neighbor.g_cost = tentative_g_cost
                neighbor.f_cost = neighbor.g_cost + neighbor.h_cost

        return None


    def heuristic(self, a, b):
        return abs(b[0] - a[0]) + abs(b[1] - a[1])


    def get_neighbors(self, node):
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_position = (node.position[0] + dx, node.position[1] + dy)
            neighbors.append(Node(new_position, node.g_cost + 1, self.heuristic(new_position, goal)))
        return neighbors


    def reconstruct_path(self, node):
        path = []
        while node:
            path.append(node.position)
            node = node.parent
        return path[::-1]
