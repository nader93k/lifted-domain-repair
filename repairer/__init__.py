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
        # hitter = Hitter()
        hitter = MaxSATHitter()
        # cached_conflicts = []
        # cached = []
        while True:
            print(10)
            candidate = hitter.top()
            # try:
            #     candidate = hitter.top()
            # except AttributeError:
            #     print("Error: 'FM' object has no attribute 'model'. Make sure the solver has been run and a model is available.")
            #     x = 1
            candidate = set(_idx_to_repair[x] for x in candidate)
            logging.debug("printing candidate repairs:")
            for c in candidate:
                msg = str(c) + "({})".format(_repair_to_idx[c])
                logging.debug(msg)
            logging.debug("end printing candidate")
            # for e in cached:
            #     assert(candidate != e)
            # cached.append(candidate)
            domain.repairs = candidate
            domain.update()
            domain.repaired = True
            confs = set()
            for instance in instances:
                task, plans = instance
                for i, plan in enumerate(plans):
                    logging.debug("conflict for the {}th plan".format(i))
                    succeed = plan.execute(domain, task)
                    if not succeed:
                        domain.repaired = False
                        conf = plan.compute_conflict(domain)
                        confs.add(tuple(conf))
                        # cached_conflicts.append(conf)
                        conflict = []
                        for r in conf:
                            if r not in _repair_to_idx:
                                idx = len(_repair_to_idx) + 1
                                _repair_to_idx[r] = idx
                                _idx_to_repair[idx] = r
                                print('conflict in-loop:', conflict)
                                hitter.add_conflict([-idx], 1)
                            if r.condition:
                                conflict.append(-_repair_to_idx[r])
                            else:
                                conflict.append(_repair_to_idx[r])
                            msg = str(r) + " condition: {} -- {}".format(
                                    r.condition, _repair_to_idx[r])
                            logging.debug(msg)
                        print('conflict out-loop:', conflict)
                        print(">> id to repair ")
                        pp.pp(_idx_to_repair)
                        hitter.add_conflict(conflict)
                    logging.debug("end conflict for the {}th plan".format(i))
            if domain.repaired:
                self._repairs = candidate
                break

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
