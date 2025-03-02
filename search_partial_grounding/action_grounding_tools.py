import copy
# from heuristic_tools import heuristic
import subprocess
import os
from pathlib import Path
import re
from typing import List
import random



def read_lifted_actions(file_path, lift_prob=0.0, random_seed=0) -> List[List[str]]:
    random.seed(random_seed)
    result = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('('):
                line = line.lstrip('(').rstrip(')')

                parts = line.split()
                if not parts:
                    continue
                    
                action_name = parts[0]
                parameters = parts[1:]
                
                # Process parameters - maybe add ? to each
                processed_params = []
                for param in parameters:
                    if random.random() < lift_prob:
                        processed_params.append('?' + param)
                    else:
                        processed_params.append(param)
                
                processed_line = [action_name] + processed_params
                result.append(processed_line)

    return result


def read_ground_actions(file_path: str) -> List[str]:
    result = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('('):
                result.append(line)
    return result
