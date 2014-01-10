#! /usr/bin/env python

import sys, os, time
from clearcache import clean_cache_iod, clean_cache_disk

_parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_prjtopdir = os.path.dirname(os.path.dirname(_parentdir))
_bindir = os.path.join(_prjtopdir, "bin")

sys.path.append(_parentdir)
import mixedbench

def main():
    datadir = "/data/iod8raid0/tpchdata"
    valdicts = [{"nthreads": i, "numtasks": 16000,
                 "iosize": 1 << 13, "maxiter": 1 << 10,
                 "readfiles": [os.path.join(datadir, "benchdata" + str(j))
                               for j in range(32)],
                 "writefiles": [os.path.join(datadir, "benchdata" + str(j))
                                for j in range(32, 32 + 32)],
                 "timeout": 30
                 } for i in [1 << i for i in range(5)]]
    # valdicts = [{"nthreads": 1, "numtasks": 4000, "iosize": i, "maxiter": 1 << 10,
    #              "readfiles": [os.path.join(datadir, "benchdata" + str(j))
    #                            for j in range(32)],
    #              "writefiles": [os.path.join(datadir, "benchdata" + str(j))
    #                             for j in range(32, 32 + 32)]}
    #             for i in [1 << j in range(9, 21)]]
    iodumpfile = "/tmp/iodump"
    workloadfunc = lambda i: i % 4 <= 2
    outdir = "/data/local/keisuke/{0}".format(time.strftime("%Y%m%d%H%M%S", time.gmtime()))
    os.mkdir(outdir)
    odirectflg = False
    statflg = True

    mixbncmgr = mixedbench.mixedloadbenchmanager(
        os.path.join(_bindir, "ioreplayer"), outdir, iodumpfile,
        clean_cache_iod, workloadfunc, odirectflg, statflg)

    for i in range(5):
        mixbncmgr.dobench(valdicts)

if __name__ == "__main__":
    main()
