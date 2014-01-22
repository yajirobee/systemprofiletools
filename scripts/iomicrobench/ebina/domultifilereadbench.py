#! /usr/bin/env python

import sys, os, itertools, time
from clearcache import clean_cache_iod, clean_cache_disk

_parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_prjtopdir = os.path.dirname(os.path.dirname(_parentdir))
_bindir = os.path.join(_prjtopdir, "bin")

sys.path.append(_parentdir)
import multifilereadbench

def main(fpaths):
    iomax = 1 << 38
    timeout = 30
    iosizes = [2 ** i for i in range(9, 21)]
    nthreadslist = [2 ** i for i in range(8)]
    maxnthreads = max(nthreadslist)
    maxfsize = 1 << 32  #iomax / maxnthreads
    valdicts = [{"iosize" : vals[0],
                 "nthreads" : vals[1],
                 "timeout": timeout,
                 "iterate": maxfsize / vals[0]}
                for vals in itertools.product(iosizes, nthreadslist)]

    outdir = "/data/local/keisuke/{0}".format(time.strftime("%Y%m%d%H%M%S", time.gmtime()))
    os.mkdir(outdir)
    odirectflg = False
    statflg = True

    seqbncmgr = multifilereadbench.multifilereadbenchmanager(
        os.path.join(_bindir, "sequentialread"), outdir, fpaths, clean_cache_iod,
        odirectflg, statflg)
    randbncmgr = multifilereadbench.multifilereadbenchmanager(
        os.path.join(_bindir, "randomread"), outdir, fpaths, clean_cache_iod,
        odirectflg, statflg)

    for i in range(5):
        # sequential read
        # sys.stdout.write("sequential read\n")
        # seqbncmgr.dobench(valdicts)
        # time.sleep(300)

        # random read
        sys.stdout.write("random read\n")
        randbncmgr.dobench(valdicts)
        time.sleep(300)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stdout.write("Usage : {0} benchdatadir\n".format(sys.argv[0]))
        sys.exit(0)
    datadir = sys.argv[1]
    assert os.path.isdir(datadir), "datadir does not exist"

    fpaths = [os.path.join(datadir, d) for d in os.listdir(datadir)]
    main(fpaths)
