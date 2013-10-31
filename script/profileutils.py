#! /usr/bin/env python

import sys, os, re
import subprocess as sp
import numpy as np

class cpuio_stat_watcher(object):
    def __init__(self, iostatfile, mpstatfile, interval = 1):
        self.iostatfile = iostatfile
        self.mpstatfile = mpstatfile

    def __enter__(self):
        self.iostatproc = sp.Popen(["iostat", "-x", str(interval)],
                                   stdout = open(self.iostatfile, "w"))
        self.mpstatproc = sp.Popen(["mpstat", "-P", "ALL", str(interval)],
                                   stdout = open(self.mpstatfile, "w"))

    def __exit__(self, exc_type, exc_val, exc_tb):
       self.iostatproc.kill()
       self.mpstatproc.kill()
       return True if exc_type == None else False

class perf_stat_watcher(object):
    perfevents = (
        {"select": "cycles", "name": "cycles"},
        {"select": "cache-references", "name": "L3_cache_references"},
        {"select": "cache-misses", "name": "L3_cache_misses"},
        {"select": "LLC-loads", "name": "LLC-loads"},
        {"select": "LLC-load-misses", "name": "LLC-load-misses"},
        {"select": "LLC-stores", "name": "LLC-stores"},
        {"select": "LLC-store-misses", "name": "LLC-store-misses"},
        {"select": "L1-dcache-loads", "name": "L1-dcache-loads"},
        {"select": "L1-dcache-load-misses", "name": "L1-dcache-load-misses"},
        {"select": "L1-dcache-stores", "name": "L1-dcache-stores"},
        {"select": "L1-dcache-store-misses", "name": "L1-dcache-store-misses"}
        )
    def __init__(self, perfstatfile, interval = 1):
        self.perfcmd = ["perf", "stat", "--all-cpus", "--no-aggr",
                        #"--cpu=" + ','.join([str(v) for v in self.cpus]),
                        "--output", perfstatfile, "--append",
                        "--event=" + ','.join([d["select"] for d in self.perfevents]),
                        "sleep", str(interval)]

    def __enter__(self):
        pid = os.fork()
        if pid == 0:
            while True: sp.call()
        else:
            self.child = pid
            return

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.kill(self.child, 9)
        return True if exc_type == None else False

def import_iostatfile(iostatfile):
    """
    import iostat output with dictionary
    Arguments:
    - `iostatfile`: the iostat output file (got by command like "iostat -x 1")

    iostat fields are assumed like following
    Device: rrqm/s wrqm/s r/s w/s rsec/s wsec/s avgrq-sz avgqu-sz await svctm %util
    """
    iostatdict = {}
    floatpat = re.compile("\d+(?:\.\d*)?")
    with open(iostatfile) as fo:
        fo.readline()
        for line in fo:
            vals = [v.strip() for v in line.split()]
            # skip header (start with "devicename:")
            # and avg-cpu line (header start with "avg-cpu:", content start with float number)
            if not vals or ':' in vals[0] or floatpat.match(vals[0]): continue
            if vals[0] not in iostatdict: iostatdict[vals[0]] = []
            fields = [float(v) for v in vals[1:]]
            fields[4] *= 512 * (10 ** -6) # convert read throughput from sec/s to MB/s
            fields[5] *= 512 * (10 ** -6) # convert write throughput from sec/s to MB/s
            iostatdict[vals[0]].append(fields)
    return iostatdict

def import_mpstatfile(mpstatfile):
    """
    import mpstat output with dictionary
    Arguments:
    - `mpstatfile`: the mpstat output file (got by command like "mpstat -P ALL 1")

    mpstat fields are assumed like following
    time CPU %usr %nice %sys %iowait %irq %soft %steal %guest %idle
    """
    cpustatdict = {}
    for line in open(mpstatfile):
        vals = [v.strip() for v in line.split()]
        if not vals: continue
        elif vals[1].isdigit() or "all" == vals[1]:
            if vals[1] not in cpustatdict: cpustatdict[vals[1]] = []
            cpustatdict[vals[1]].append([float(v) for v in vals[2:]])
    return cpustatdict

def import_perfstatfile(perfstatfile):
    """
    import perf stat output with dictionary
    Arguments:
    - `perfstatfile`: the perf stat output file
    (got by command like "perf stat --all-cpus --no-aggr --output file --append -- sleep 1")

    perf stat fields are assumed like following
    CPUnum value select [some comment] (float%)
    """
    perfstatdict = {}
    currentstatdict = {}
    corepat = re.compile("CPU(\d+)")
    for line in open(perfstatfile):
        vals = [v.strip() for v in line.split()]
        if not vals or len(vals) < 3: continue
        match = corepat.match(vals[0])
        if match:
            corenum = match.group(1)
            if corenum not in currentstatdict: currentstatdict[corenum] = {}
            currentstatdict[corenum][vals[2]] = int(vals[1]) if vals != "<not counted>" else -1
        elif vals[2] == "time" and vals[3] == "elapsed":
            if currentstatdict:
                for k, v in currentstatdict.items():
                    if k not in perfstatdict: perfstatdict[k] = []
                    perfstatdict[k].append(v)
            currentstatdict = {}
    return perfstatdict

def import_perfstatfile_aggregated(perfstatfile):
    """
    import perf stat output with aggregated style list
    Arguments:
    - `perfstatfile`: the perf stat output file
    (got by command like "perf stat --output file --append -- sleep 1")

    perf stat fields are assumed like following
    value select [some comment] [float%]
    """
    perfstatlist = []
    currentstatdict = {}
    for line in open(perfstatfile):
        vals = [v.strip() for v in line.split()]
        if not vals or len(vals) < 2: continue
        if vals[2] == "time" and vals[3] == "elapsed":
            if currentstatdict: perfstatlist.append(currentstatdict)
            currentstatdict = {}
        else: currentstatdict[vals[1]] = int(vals[0]) if vals != "<not counted>" else -1
    return perfstatlist
