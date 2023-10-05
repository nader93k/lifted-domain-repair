from hitter.memhitter import *
from model.domain import *
from model.plan import *


class Repairer:
    def __init__(self,
                 domain: Domain,
                 instances: List[Tuple[Task, List[Plan]]]):
        # initialize the plans
        for instance in instances:
            task, plans = instance
            for plan in plans:
                plan.compute_subs(domain, task)
        _repair_to_idx = {}
        _idx_to_repair = {}
        hitter = Hitter()
        while True:
            candidate = hitter.top()
            candidate = set(_idx_to_repair[x] for x in candidate)
            domain.repairs = candidate
            domain.update()
            domain.repaired = True
            for instance in instances:
                task, plans = instance
                for plan in plans:
                    succeed = plan.execute(domain, task)
                    if not succeed:
                        domain.repaired = False
                        conf = plan.compute_conflict(domain)
                        conflict = []
                        for r in conf:
                            if r not in _repair_to_idx:
                                idx = len(_repair_to_idx) + 1
                                _repair_to_idx[r] = idx
                                _idx_to_repair[idx] = r
                            if r.condition:
                                conflict.append(-_repair_to_idx[r])
                            else:
                                conflict.append(_repair_to_idx[r])
                        hitter.add_conflict(conflict)
            if domain.repaired:
                self._repairs = candidate
                break

    def print_repairs(self):
        for r in self._repairs:
            print(str(r))