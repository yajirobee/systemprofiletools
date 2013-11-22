#! /usr/bin/env python

import sys, os

datadir = "/data/iod8raid0/tpchdata"

def create_tasks_fromfile(filepath, mode, iosize, maxiter):
    fsize = os.path.getsize(filepath)
    tasks = []
    offset = 0
    while offset + iosize <= fsize:
        iteration = min((fsize - offset) / iosize, maxiter)
        tasks.append((filepath, mode, str(offset), str(iosize), str(iteration)))
        offset += iosize * iteration
    return tasks

def create_workload(output, ntasks, readfiles, writefiles,
                    nthreads = 1, iosize = 1 << 13, maxiter = 1 << 10,
                    workloadfunc = lambda i: i % 2 == 0):
    readtasksdict = dict([(i, []) for i in range(nthreads)])
    writetasksdict = dict([(i, []) for i in range(nthreads)])
    with open(output, "w") as fo:
        for i in range(ntasks):
            idx = i % nthreads
            if workloadfunc(i):
                if not readtasksdict[idx]:
                    f = readfiles.pop(0)
                    readtasksdict[idx] = create_tasks_fromfile(f, "R", iosize, maxiter)
                task = readtasksdict[i % nthreads].pop(0)
            else:
                if not writetasksdict[idx]:
                    f = writefiles.pop(0)
                    writetasksdict[idx] = create_tasks_fromfile(f, "W", iosize, maxiter)
                task = writetasksdict[i % nthreads].pop(0)
            fo.write("\t".join(task) + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Usage : {0} output [nthreads]\n".format(sys.argv[0]))
        sys.exit(1)

    output = sys.argv[1]
    nthreads = int(sys.argv) if len(sys.argv) >= 3 else 1
    readfiles = [os.path.join(datadir, "benchdata" + str(i)) for i in range(32)]
    writefiles = [os.path.join(datadir, "benchdata" + str(i)) for i in range(32, 64)]

    create_workload(output, 4000, nthread, readfiles, writefiles)
