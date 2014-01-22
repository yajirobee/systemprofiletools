#! /usr/bin/env python

import sys, os, time
from clearcache import clean_cache_iod, clean_cache_disk

_parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_prjtopdir = os.path.dirname(os.path.dirname(_parentdir))
_bindir = os.path.join(_prjtopdir, "bin")

sys.path.append(_parentdir)
import mixedbench

def main():
    datadir = "/data/iod8raid0/benchdata"
    # datadir = "/data/disk12raid0/benchdata"
    totaliosize = 1 << 37
    maxiter = 1 << 2
    valdicts = [{"nthreads": i, "numtasks": totaliosize / (j * maxiter),
                 "iosize": j, "maxiter": maxiter, "timeout": 60
                 } for j in (1 << 13, 1 << 16, 1 << 18) for i in [1 << i for i in range(7)]]
    # valdicts = [{"nthreads": 1, "numtasks": totaliosize / (i * maxiter),
    #              "iosize": i, "maxiter": maxiter, "timeout": 60
    #              } for i in [1 << j for j in range(9, 21)]]

    readfiles = [os.path.join(datadir, "benchdata" + str(k)) for k in range(64)]
    readfiles *= 4
    writefiles = [os.path.join(datadir, "benchdata" + str(k)) for k in range(64, 128)]
    writefiles *= 4
    iodumpfile = "/tmp/iodump"
    workloadfunc = lambda i: i % 4 <= 2
    outdir = "/data/local/keisuke/{0}".format(time.strftime("%Y%m%d%H%M%S", time.gmtime()))
    os.mkdir(outdir)
    odirectflg = False
    statflg = True

    mixbncmgr = mixedbench.mixedloadbenchmanager(
        os.path.join(_bindir, "ioreplayer"), outdir,
        readfiles, writefiles, iodumpfile,
        clean_cache_iod, #clean_cache_disk,
        workloadfunc, odirectflg, statflg)

    for i in range(5):
        mixbncmgr.dobench(valdicts)

if __name__ == "__main__":
    main()
