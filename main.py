# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from repairer import *
from model.domain import *
from model.plan import *

import os


def clean_plan(plan_file, out_file, negative=False):
    lines = []
    idx = None
    with open(plan_file, "r") as f:
        for i, line in enumerate(f):
            if "-copy" in line:
                continue
            if "turning" in line:
                continue
            if "-stop" in line:
                if negative:
                    idx = i//2
                continue
            lines.append(line)
    with open(out_file, "w") as f:
        for line in lines:
            f.write(line)
    return idx

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    root = "/home/users/u6162630/Datasets/test-2/grid"
    domain_file = os.path.join(root, "domain-modified.pddl")
    domain = Domain(domain_file)
    task_dirs = filter(lambda x: "prob" in x, os.listdir(root))
    instances = []
    for task_dir in task_dirs:
        d = os.path.join(root, task_dir)
        task_file = os.path.join(d, task_dir + ".pddl")
        task = Task(task_file)
        pos_plan_dir = os.path.join(d, "positive-plans")
        neg_plan_dir = os.path.join(d, "negative-plans")
        pos_plan_files = filter(lambda x: "plan" in x and "val-" not in x, os.listdir(pos_plan_dir))
        pos_plans = []
        for pos_plan_file in pos_plan_files:
            f = os.path.join(pos_plan_dir, pos_plan_file)
            out = os.path.join(pos_plan_dir, "val-" + pos_plan_file)
            _ = clean_plan(f, out)
            pos_plans.append(PositivePlan(out))
        neg_plan_files = filter(lambda x: "plan" in x and "val-" not in x, os.listdir(neg_plan_dir))
        neg_plans = []
        for neg_plan_file in neg_plan_files:
            f = os.path.join(neg_plan_dir, neg_plan_file)
            out = os.path.join(neg_plan_dir, "inval-" + neg_plan_file)
            idx = clean_plan(f, out, True)
            assert (idx is not None)
            neg_plans.append(NegativePlan(out, idx))
        plans = pos_plans + neg_plans
        if len(plans) == 0:
            continue
        instances.append((task, plans))
    repairer = Repairer(domain, instances)
    repairer.print_repairs()

    # domain_file = "test/domain.pddl"
    # # domain_file = "/home/users/u6162630/Datasets/test-1/domain.pddl"
    # task_file = "test/task.pddl"
    # # task_file = "/home/users/u6162630/Datasets/test-1/problem.pddl"
    # # plan_file = "test/sas_plan"
    # pos_plan_files = ["test/val_plan.{}".format(i) for i in range(1, 2, 1)]
    # # pos_plan_files = ["/home/users/u6162630/Datasets/test-1/val_plan.{}".format(i) for i in range(1, 3)]
    # neg_plan_files = ["test/inval_plan.{}".format(i) for i in range(1, 2, 1)]
    # # neg_plan_files = ["/home/users/u6162630/Datasets/test-1/inval_plan.{}".format(i) for i in range(1, 3)]
    # domain = Domain(domain_file)
    # task = Task(task_file)
    # pos_plans = [PositivePlan(pos) for pos in pos_plan_files]
    # indices = [6]
    # # indices = [0, 0]
    # neg_plan_files = zip(neg_plan_files, indices)
    # neg_plans = [NegativePlan(neg, idx) for neg, idx in neg_plan_files]
    # plans = pos_plans + neg_plans
    # # plans = [NegativePlan("test/inval_plan.1", 1)]
    # #pos_plan = PositivePlan(plan_file)
    # # neg_plan = NegativePlan(plan_file, 3)
    # repairer = Repairer(domain, [(task, plans)])
    # repairer.print_repairs()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
