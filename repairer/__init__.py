from hitter.maxsat import *
from model.plan import *
import logging
import pprint as pp


class Repairer:
    def __init__(self):
        self._repairs = None

    def repair(self
               , domain: Domain
               , instances: List[Tuple[Task, List[Plan]]]):
        # initialize the plans
        for instance in instances:
            task, plans = instance
            for plan in plans:
                plan.compute_subs(domain, task)
        _repair_to_idx = {}
        _idx_to_repair = {}
        hitter = MaxSATHitter()
        while True:
            candidate = hitter.top()
            candidate = set(_idx_to_repair[x] for x in candidate)
            for c in candidate:
                msg = str(c) + "({})".format(_repair_to_idx[c])
            domain.repairs = candidate
            domain.update()
            domain.repaired = True
            confs = set()
            for instance in instances:
                task, plans = instance
                for i, plan in enumerate(plans):
                    succeed = plan.execute(domain, task)
                    if not succeed:
                        domain.repaired = False
                        conf = plan.compute_conflict(domain)
                        if len(conf) == 0:
                            return False
                        confs.add(tuple(conf))
                        conflict = []
                        for r in conf:
                            if r not in _repair_to_idx:
                                idx = len(_repair_to_idx) + 1
                                _repair_to_idx[r] = idx
                                _idx_to_repair[idx] = r
                                hitter.add_conflict([-idx], 1)
                            if r.condition:
                                conflict.append(-_repair_to_idx[r])
                            else:
                                conflict.append(_repair_to_idx[r])
                            msg = str(r) + " condition: {} -- {}".format(
                                    r.condition, _repair_to_idx[r])
                        hitter.add_conflict(conflict)
            if domain.repaired:
                self._repairs = candidate
                return True

    def print_repairs(self):
        for r in self._repairs:
            print(str(r))

    def write(self, outfile):
        with open(outfile, "w") as f:
            for r in self._repairs:
                f.write(str(r) + "\n")

    def get_repairs_string(self):
        return "\n".join(str(r) for r in self._repairs)

    def count_repair_lines(self):
        return len(self._repairs)
