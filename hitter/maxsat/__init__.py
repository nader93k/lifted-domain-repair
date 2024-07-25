from pysat.formula import WCNF
from pysat.examples.fm import FM
from typing import List


class MaxSATHitter:
    def __init__(self):
        self._wcnf = WCNF()

    def add_conflict(self, conflict: List[int], weight=None):
        if weight is None:
            self._wcnf.append(conflict)
            if conflict != []:
                x = 12
        else:
            self._wcnf.append(conflict, weight)
            x = 13

    def top(self):
        # solver = FM(self._wcnf)
        # _ = solver.compute()
        # return [e for e in solver.model if e > 0]

        solver = FM(self._wcnf)
        try:
            _ = solver.compute()
            return [e for e in solver.model if e > 0]
        except AttributeError:
            x = 1
            print("Error: 'FM' object has no attribute 'model'. Make sure the solver has been run and a model is available.")
            return None