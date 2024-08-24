#!/usr/bin/python3

import argparse
import os
import subprocess
import sys


def parse_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='inp', action='store',
                        default=None, help='Path of domains to process.')
    parser.add_argument('-o', '--output', dest='out', action='store',
                        default=None, help='Destination path.')

    args = parser.parse_args()
    if args.inp is None:
        raise RuntimeError(f'Input path is invalid.')
    elif args.out is None:
        raise RuntimeError(f'Output path is invalid.')
    elif not os.path.exists(args.inp) or not os.path.isdir(args.inp):
        raise RuntimeError(f'Input folder does not exist.')
    elif os.path.exists(args.out):
        if os.path.isdir(args.out):
            if os.listdir(args.out):
                raise RuntimeError(f'Target path already exists '
                                   'and directory is not empty.')
        else:
            raise RuntimeError(
                f'There is a file with the same target path name.')

    return args


def theorize(abs_dir, dir, out_dir):
    dom = '/'.join([abs_dir, 'domain.pddl'])
    if not os.path.exists(dom):
        raise RuntimeError('No domain file in {}.'.format(abs_dir))
    inst = ''
    for f in os.scandir(abs_dir):
        if f.name != dom:
            inst = '/'.join([abs_dir, f.name])
            break
    #print(dom, inst)

    cmds = [
        [prog, '-i', inst, '--domain', dom, '--ground-actions',
            '--inequality-rules'],  # action, ineq
        [prog, '-i', inst, '--domain', dom, '--ground-actions'],  # action, noineq
        [prog, '-i', inst, '--domain', dom, '--inequality-rules'],  # noaction, ineq
        [prog, '-i', inst, '--domain', dom],  # noaction, noineq
    ]
    postfixes = [
        ['a', 'i'],
        ['a', 'noi'],
        ['noa', 'i'],
        ['noa', 'noi'],
    ]

    for k in range(4):
        out_name = out_theory.format(dir, postfixes[k][0], postfixes[k][1])
        out = '/'.join([out_dir, out_name])
        cmd = cmds[k]
        cmd.append('-t')
        cmd.append(out)
        print(cmd)

        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=10)
        except subprocess.TimeoutExpired:
            pass

        if not os.path.exists(out):
            raise RuntimeError('{} does not exist!'.format(out))


prog = '/home/davide/asp-grounding-planning/generate-asp-model.py'
theory = '/home/davide/asp-grounding-planning/output.theory'
out_theory = '{}_{}_{}.theory'

if __name__ == '__main__':
    options = parse_options()
    absolute_path_in = os.path.abspath(options.inp)
    absolute_path_out = os.path.abspath(options.out)
    os.makedirs(absolute_path_out, exist_ok=True)

    # subprocess.run(['source', '.venv/bin/activate'])

    for d in os.scandir(absolute_path_in):
        abs_d = os.path.abspath(d)
        d = os.path.basename(d)
        theorize(abs_d, d, absolute_path_out)
