# Import necessary modules and classes
import os
import logging
from model.plan import Domain, Task
from astar_partial_grounding import \
    read_ground_actions, all_action_groundings, read_action_names,smart_grounder, \
    AStar, Node
from astar_partial_grounding.action_grounding_tools import smart_grounder
from pathlib import Path
from exptools import generate_instances
import cProfile
import pstats
import json


def experiment(benchmark_path, specific_instance=None):

    for instance in generate_instances(
            benchmark_path
            , specific_instance=specific_instance):
        instance.load_to_memory()

        print()
        print(instance.identifier)

        if instance.domain_class=='agricola-opt18-strips' and instance.instance_name=='pp01-err-rate-0-1':
            print("Smart grounder outputs nothing")
        elif instance.domain_class=='agricola-opt18-strips' and instance.instance_name=='pp02-err-rate-0-5':
            print("Smart grounder outputs nothing")
        elif instance.domain_class=='agricola-opt18-strips' and instance.instance_name=='pp16-err-rate-0-1':
            print("Smart grounder finds groundings")
        else:
            break


        ###### Using exaustive grounding
        exaustive = all_action_groundings(
            [instance.lifted_plan[0]]
            , instance.planning_domain
            , instance.planning_task)
        
        # with open('action_grounding', 'w') as file:
        #     json.dump(action_grounding_dict, file, indent=4)

        ###### Using smart grounding

        smart = smart_grounder(
            instance.planning_domain,
            instance.planning_task,
            (instance.lifted_plan[0],)
        )
        

        print(exaustive)
        print(smart)



def print_profile(file_name: str, num_lines=20):
    stats = pstats.Stats(file_name)
    stats.sort_stats('ncalls')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stats.print_stats(script_dir, num_lines)


if __name__ == "__main__":
    benchmark_path = Path('./input/benchmarks-G1')

    # experiment(benchmark_path, specific_instance='blocks/pp01-err-rate-0-1')

    cProfile.run("experiment(benchmark_path)"
                 , 'profile_output')

    print_profile('profile_output', 20)
