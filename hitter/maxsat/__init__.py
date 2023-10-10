from pysat.formula import WCNF
from pysat.examples.fm import FM
from typing import List


class MaxSATHitter:
    def __init__(self):
        self._wcnf = WCNF()

    def add_conflict(self, conflict: List[int], weight=None):
        if weight is None:
            self._wcnf.append(conflict)
        else:
            self._wcnf.append(conflict, weight)

    def top(self):
        solver = FM(self._wcnf)
        _ = solver.compute()
        return [e for e in solver.model if e > 0]