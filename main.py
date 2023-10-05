# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from repairer import *
from model.domain import *
from model.plan import *


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    domain_file = "/home/users/u6162630/Datasets/fuzzy-1-domain-1-task/tidybot-sat11-strips/p09/err-rate-0.5/domain.pddl"
    task_file = "/home/users/u6162630/Datasets/fuzzy-1-domain-1-task/tidybot-sat11-strips/p09/p09.pddl"
    plan_file = "/home/users/u6162630/Datasets/fuzzy-1-domain-1-task/tidybot-sat11-strips/p09/sas_plan"
    domain = Domain(domain_file)
    task = Task(task_file)
    pos_plan = PositivePlan(plan_file)
    repairer = Repairer(domain, [(task, [pos_plan])])
    repairer.print_repairs()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
