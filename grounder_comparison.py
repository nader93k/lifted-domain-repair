# Import necessary modules and classes
import os
import logging
from model.plan import Domain, Task
from astar_partial_grounding import \
    read_ground_actions, all_action_groundings, read_action_names,all_smart_groundings, \
    AStar, Node
from pathlib import Path
from exptools import generate_instances
import cProfile
import pstats
import json
from pprint import pprint



def experiment(benchmark_path, specific_instance=None):

    for instance in generate_instances(
            benchmark_path,
            specific_instance=specific_instance):
        instance.load_to_memory()

        print()
        print(instance.identifier)

        ###### Using smart grounding
        smart = all_smart_groundings(
            instance.planning_domain,
            instance.planning_task,
            instance.lifted_plan
        )
        pprint(smart)


        # ###### Using exaustive grounding
        # exaustive = all_action_groundings(
        #     [instance.lifted_plan[0]]
        #     , instance.planning_domain
        #     , instance.planning_task)
         # print(exaustive)
        
        # # with open('action_grounding', 'w') as file:
        # #     json.dump(action_grounding_dict, file, indent=4)


def print_profile(file_name: str, num_lines=20):
    stats = pstats.Stats(file_name)
    stats.sort_stats('ncalls')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stats.print_stats(script_dir, num_lines)


if __name__ == "__main__":
    benchmark_path = Path('./input/benchmarks-G1')

    experiment(benchmark_path, specific_instance='agricola-opt18-strips/pp01-err-rate-0-1')
    # experiment(benchmark_path, specific_instance='agricola-opt18-strips/pp02-err-rate-0-5')
    # experiment(benchmark_path, specific_instance='agricola-opt18-strips/pp16-err-rate-0-1')


    # cProfile.run("experiment(benchmark_path)"
    #              , 'profile_output')
    # print_profile('profile_output', 20)
