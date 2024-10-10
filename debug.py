from heuristic_tools.heuristic import Heurisitc
import pickle



with open('domain.pkl', 'rb') as file:
    domain = pickle.load(file)
with open('task.pkl', 'rb') as file:
    task = pickle.load(file)
with open('actions.pkl', 'rb') as file:
    actions = pickle.load(file)

h = Heurisitc(h_name="G_HMAX", relaxation=None)
h_cost = h.evaluate(domain, task, actions)
