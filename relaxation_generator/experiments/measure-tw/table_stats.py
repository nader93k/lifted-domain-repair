#!/usr/bin/python3

import csv
import math
import statistics as stat
import sys

suff_ai = '_a_i'
suff_anoi = '_a_noi'
suff_noai = '_noa_i'
suff_noanoi = '_noa_noi'


def parse_name(name):
    name = name.split('/')[-1]
    name = name.split('.theory')[0]

    rem = ''
    if name.endswith(suff_ai):
        ai = (True, True)
        rem = suff_ai
    elif name.endswith(suff_anoi):
        ai = (True, False)
        rem = suff_anoi
    elif name.endswith(suff_noai):
        ai = (False, True)
        rem = suff_noai
    elif name.endswith(suff_noanoi):
        ai = (False, False)
        rem = suff_noanoi
    else:
        raise RuntimeError('Impossible case: {}'.format(name))

    i = name.index(rem)
    name = name[:i]

    return name, ai[0], ai[1]


def compute_stats(widths):
    w = [int(x) for x in widths]
    avg = stat.mean(w)
    med = stat.median(w)
    stddev = stat.stdev(w)
    return len(w), min(w), max(w), round(avg, 2), med, round(stddev, 2)


idx_ai = 0
idx_anoi = 1
idx_noai = 2
idx_noanoi = 3


def aggregate(rows, dom):
    ll = []
    for r in rows:
        if dom in r[0]:
            #print('{}\t{}'.format(dom, r))
            r[0] = dom
            ll.append(r)

    if len(ll) == 4:
        return ll

    cats = [[], [], [], []]
    for r in ll:
        if r[1] == True and r[2] == True:
            cats[idx_ai].append(r)
        elif r[1] == True and r[2] == False:
            cats[idx_anoi].append(r)
        elif r[1] == False and r[2] == True:
            cats[idx_noai].append(r)
        elif r[1] == False and r[2] == False:
            cats[idx_noanoi].append(r)

    res = []
    for k in range(4):
        res.append(aggregate_cat(cats[k]))
    return res


def aggregate_cat(cat):
    res = [cat[0][0], cat[0][1], cat[0][2], 0, 0, 0, 0, 0, 0]
    # average of num [3]
    res[3] = stat.mean([cat[j][3] for j in range(len(cat))])
    res[3] = round(r[3], 2)
    # min of all mins [4]
    res[4] = min([cat[j][4] for j in range(len(cat))])
    # max of all maxs [5]
    res[5] = max([cat[j][5] for j in range(len(cat))])
    # weigthed average of averages [6]
    nums = [cat[j][3] for j in range(len(cat))]
    weigths = [n/sum(nums) for n in nums]
    for j in range(len(cat)):
        res[6] += weigths[j] * cat[j][6]
    res[6] = round(res[6], 2)
    # median of medians [7] (no statistical meaning)
    res[7] = stat.median([cat[j][7] for j in range(len(cat))])
    res[7] = round(res[7], 2)
    # stdev of stdevs [8]
    n = 0
    d = 0
    for i in range(len(cat)):
        n += (cat[i][3]-1) * (cat[i][8]**2)
        d += (cat[i][3]-1)
    res[8] = math.sqrt(n/d)
    res[8] = round(res[8], 2)

    return res


if __name__ == '__main__':
    last_name = ''
    cnt = 4
    rows = []
    with open(sys.argv[1]) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            name, act, ineq = parse_name(row[0])
            if name != last_name:
                if cnt != 4:
                    raise RuntimeError(
                        '{} has only {} lines!'.format(last_name, cnt))
                last_name = name
                cnt = 1
            else:
                cnt = cnt + 1
            num, minimum, maximum, avg, median, stddev = compute_stats(
                row[1:len(row)-1])
            rows.append([name, act, ineq, num, minimum,
                        maximum, avg, median, stddev])
            # print('\t'.join([name, str(act), str(ineq),
            #                str(num), str(minimum), str(maximum), str(avg), str(median), str(stddev)]))

    print()
    # print(rows)
    print()
    domains = []
    with open(sys.argv[2], 'r') as f:
        domains = f.readlines()
    res = []
    for d in domains:
        d = d.strip()
        # print(d)
        for r in aggregate(rows, d):
            res.append(r)
    # print(res)

    ll = []
    ll.append('\\begin{table*}\n')
    ll.append('\t\\centering\n')
    ll.append('\t\\begin{tabular}{l|cc|rrrrrr}\n')
    ll.append('\t\t\\toprule\n')
    ll.append(
        '\t\t\\textbf{Domain} & A & I & \\# & min & max & avg & median & stdev \\\\\n')
    for i in range(len(res)):
        name = ''
        if i % 4 == 0:
            ll.append('\t\t\\midrule\n')
            name = '\\multirow{4}{*}{'+res[i][0]+'}'

        r = res[i]
        act = 'n'
        ineq = 'n'
        if r[1]:
            act = 'y'
        if r[2]:
            ineq = 'y'

        s = '\t\t' + '\t&\t'.join([name, act, ineq, str(r[3]), str(
            r[4]), str(r[5]), str(r[6]), str(r[7]), str(r[8])]) + '\\\\\n'
        ll.append(s)

        print('\t'.join([r[0], str(r[1]), str(r[2]), str(r[3]), str(
            r[4]), str(r[5]), str(r[6]), str(r[7]), str(r[8])]))
    ll.append('\t\t\\bottomrule\n')
    ll.append('\t\\end{tabular}\n')
    ll.append('\t\\caption{Treewidth statistical data.}\n')
    ll.append('\t\\label{table:treewidths}\n')
    ll.append('\\end{table*}\n')
    with open('table-treewidth.tex', 'w') as f:
        f.writelines(ll)
