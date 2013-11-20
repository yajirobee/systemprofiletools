#! /usr/bin/env python

import sys, os, shlex
import subprocess as sp

_mydirabspath = os.path.dirname(os.path.abspath(__file__))
_prjtopdir = os.path.dirname(os.path.dirname(_mydirabspath))
_bindir = os.path.join(_prjtopdir, "bin")

sequentialread_bin = os.path.join(_bindir, "sequentialread")

def clear_dev_buffer(devs, iosize, iterate, nthread):
    # clear storage side buffer
    procs = []
    readcmd = sequentialread_bin + " -d -s {iosize} -i {iterate} -m {nthread} {dev}"
    for dev in devs:
        cmd = shlex.split(readcmd.format(iosize = iosize, iterate = iterate,
                                         nthread = nthread, dev = dev))
        procs.append(sp.Popen(cmd, stdout = open("/dev/null", "w"), stderr = sp.STDOUT))
    rcs = [p.wait() for p in procs]
    if [0 for rc in rcs] != rcs:
        sys.stderr.write("device read error : {0}\n".format(zip(devs, rcs)))
        sys.exit(1)

'''
examples
def clear_iodrive_buffer(size):
    devs = ["/dev/fio{0}".format(i) for i in "abcdefgh"]
    maxsize = 128 * 2 ** 30
    size = min(size, maxsize)
    iosize = 2 ** 25
    nthread = 4
    iterate = max(size / (iosize * nthread), 1)
    clear_dev_buffer(devs, iosize, iterate, nthread)

def clear_disk_buffer(size):
    devs = ["/dev/sd{0}".format(i) for i in "bcdefghijklm"]
    maxsize = 120 * 2 ** 30
    size = min(size, maxsize)
    iosize = 2 ** 25
    nthread = 1
    iterate = max(size / (iosize * nthread), 1)
    clear_dev_buffer(devs, iosize, iterate, nthread)
'''

def clear_os_cache():
    sp.call(["sync"])
    sp.call(["clearcache"])
