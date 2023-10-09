# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from repairer import *
from model.domain import *
from model.plan import *


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    domain_file = "test/domain.pddl"
    task_file = "test/task.pddl"
    # plan_file = "test/sas_plan"
    pos_plan_files = ["test/val_plan.{}".format(i) for i in range(1, 5, 1)]
    neg_plan_files = ["test/inval_plan.{}".format(i) for i in range(1, 4, 1)]
    domain = Domain(domain_file)
    task = Task(task_file)
    pos_plans = [PositivePlan(pos) for pos in pos_plan_files]
    indices = [1, 5, 7]
    neg_plan_files = zip(neg_plan_files, indices)
    neg_plans = [NegativePlan(neg, idx) for neg, idx in neg_plan_files]
    plans = pos_plans + neg_plans
    # plans = [NegativePlan("test/inval_plan.1", 1)]
    #pos_plan = PositivePlan(plan_file)
    # neg_plan = NegativePlan(plan_file, 3)
    repairer = Repairer(domain, [(task, neg_plans)])
    repairer.print_repairs()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
