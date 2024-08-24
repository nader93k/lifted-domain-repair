#!/usr/bin/python3

import os
import subprocess
import sys


width_file = 'width.txt'

def split(filename):
    k = 0
    f = open(filename, 'r')
    tws = []
    while True:
        line = f.readline()
        if not line:
            break
        r = line.split(':-')
        if len(r) > 1:
            body = r[1].strip()
            #if not body.startswith('action') or '),' in body:
            if True:
                out_name = filename+'_r'+str(k)
                out = open(out_name, 'w')
                out.write(line)
                out.close()
                k = k+1

                subprocess.run(["lpopt", "-f", out_name, "-l", width_file],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                w = open(width_file, 'r')
                line = w.readline()
                tw = line.split(':')[1].strip()
                tws.append(tw)
                w.close()

                os.remove(out_name)
    f.close()
    os.remove(width_file)
    return tws


if __name__ == '__main__':
    lines = []
    for f in sys.argv[1:]:
        tws = split(f)
        print(f, '\t', tws)
        l = f + ',' + ','.join(tws) + '\n'
        print(l)
        lines.append(l)

    result = open('results_all.txt', 'w')
    result.writelines(lines)
    result.close()
