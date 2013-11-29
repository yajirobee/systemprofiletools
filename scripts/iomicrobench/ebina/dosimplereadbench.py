#! /usr/bin/env python

import sys, os, time, itertools
import clearcache

_parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_prjtopdir = os.path.dirname(os.path.dirname(_parentdir))
_bindir = os.path.join(_prjtopdir, "bin")

sys.path.append(_parentdir)
import simplereadbench

def clearcache():
    clearcache.clear_os_cache()
    clearcache.clear_iodrive_buffer(2 ** 32)

def main(fpath):
    with open(fpath) as fo:
        fo.seek(0, os.SEEK_END)
        fsize = fo.tell()
    timeout = 30
    iosizes = [2 ** i for i in range(9, 22)]
    nthreads = [2 ** i for i in range(1)]
    valdicts = [{"iosize" : vals[0],
                 "nthreads" : vals[1],
                 "timeout": timeout,
                 "iterate": fsize / (vals[0] * vals[1])}
                for vals in itertools.product(iosizes, nthreads)]

    outdir = "/data/local/keisuke/{0}".format(time.strftime("%Y%m%d%H%M%S", time.gmtime()))
    os.mkdir(outdir)
    odirectflg = False
    statflg = True

    seqbncmgr = simplereadbench.simplereadbenchmanager(
        os.path.join(_bindir, "sequentialread"), outdir, fpath, clearcache,
        odirectflg, statflg)
    randbncmgr = simplereadbench.simplereadbenchmanager(
        os.path.join(_bindir, "randomread"), outdir, fpath, clearcache,
        odirectflg, statflg)

    for i in range(5):
        # sequential read
        sys.stdout.write("sequential read\n")
        seqbncmgr.dobench(valdicts)
        time.sleep(300)

        # random read
        sys.stdout.write("random read\n")
        randbncmgr.dobench(valdicts)
        time.sleep(300)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stdout.write("Usage : {0} fpath\n".format(sys.argv[0]))
        sys.exit(0)
    fpath = sys.argv[1]

    main(fpath)

