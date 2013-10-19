#! /usr/bin/env python

import sys, os, re
import numpy as np

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
