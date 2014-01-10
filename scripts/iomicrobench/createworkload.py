#! /usr/bin/env python

import sys, os

def create_readtasks(filepath, iosize, maxiter):
    fsize = os.path.getsize(filepath)
    tasks = []
    offset = 0
    while offset + iosize <= fsize:
        iteration = min((fsize - offset) / iosize, maxiter)
        tasks.append((filepath, "R", str(offset), str(iosize), str(iteration)))
        offset += iosize * iteration
    return tasks

def create_writetasks(filepath, iosize, maxiter, writefilesize = 2 ** 33):
    tasks = []
    offset = 0
    while offset + iosize <= writefilesize:
        iteration = min((writefilesize - offset) / iosize, maxiter)
        tasks.append((filepath, "W", str(offset), str(iosize), str(iteration)))
        offset += iosize * iteration
    return tasks

def create_workload(output, ntasks, readfiles, writefiles,
                    nthreads = 1, iosize = 1 << 13, maxiter = 1 << 10,
                    workloadfunc = lambda i: i % 2 == 0):
    readtasksdict = dict([(i, []) for i in range(nthreads)])
    writetasksdict = dict([(i, []) for i in range(nthreads)])
    taskque = []
    with open(output, "w") as fo:
        for i in range(ntasks):
            idx = i % nthreads
            if workloadfunc(i / nthreads):
                if not readtasksdict[idx]:
                    f = readfiles.pop(0)
                    readtasksdict[idx] = create_readtasks(f, iosize, maxiter)
                taskque.append(readtasksdict[idx].pop(0))
            else:
                if not writetasksdict[idx]:
                    f = writefiles.pop(0)
                    writetasksdict[idx] = create_writetasks(f, iosize, maxiter)
                taskque.append(writetasksdict[idx].pop(0))
            if len(taskque) >= 1 << 25:
                fo.writelines(["\t".join(task) + "\n" for task in taskque])
                taskque = []
        else:
            if len(taskque) > 0:
                fo.writelines(["\t".join(task) + "\n" for task in taskque])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Usage : {0} output [nthreads]\n".format(sys.argv[0]))
        sys.exit(1)

    output = sys.argv[1]
    nthreads = int(sys.argv) if len(sys.argv) >= 3 else 1
    datadir = "/data/iod8raid0/tpchdata"
    readfiles = [os.path.join(datadir, "benchdata" + str(i)) for i in range(32)]
    writefiles = [os.path.join(datadir, "benchdata" + str(i)) for i in range(32, 64)]

    create_workload(output, 4000, nthread, readfiles, writefiles)
