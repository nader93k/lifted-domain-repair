#!/usr/bin/env python

import argparse
import os
import subprocess
import platform

from distutils.dir_util import copy_tree
from shutil import copytree

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
DATALOG_TRANSFORMER = os.path.join(PROJECT_ROOT, 'datalog_transformer')
TRANSFORMER_BUILD_DIR = os.path.join(DATALOG_TRANSFORMER, 'cmake-build-debug')    

if __name__ == '__main__':
    os.makedirs(TRANSFORMER_BUILD_DIR, exist_ok=True)
    print("Building", DATALOG_TRANSFORMER, "in", TRANSFORMER_BUILD_DIR)
    subprocess.check_call(['cmake', DATALOG_TRANSFORMER, '-DCMAKE_BUILD_TYPE=Release'],
                          cwd=TRANSFORMER_BUILD_DIR)
    subprocess.check_call(['make', '-j5'], cwd=TRANSFORMER_BUILD_DIR)
