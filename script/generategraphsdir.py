#! /usr/bin/env python

import sys, os, collections, errno
import drawio, drawcpu, drawcache
from profileutils import import_iostatfile, import_mpstatfile, import_perfstatfile

def search_statfiles(rootdir):
    exts = (".io", ".cpu", ".perf",
            ".iohist", ".cpuhist", ".cachehist")
    dirqueue = collections.deque([rootdir])
    statfiles = []
    while dirqueue:
        currentdir = dirqueue.popleft()
        for entry in os.listdir(currentdir):
            path = os.path.join(currentdir, entry)
            if os.path.islink(path): continue
            elif os.path.isdir(path) and os.access(path, os.R_OK | os.W_OK | os.X_OK):
                dirqueue.append(path)
            elif os.path.isfile(path):
                ext = os.path.splitext(entry)[1]
                if ext in exts: statfiles.append(path)
    return statfiles

def generate_allgraphs(statfiles, devices = [], cores = [], terminaltype = "png"):
    for f in statfiles:
        fwoext, ext = os.path.splitext(f)
        if ext == ".io":
            iostatdict = import_iostatfile(f)
            for dev in devices:
                ioprof = iostatdict[dev]
                outprefix = fwoext + "_" + dev
                drawio.plot_ioprof(ioprof, outprefix, 1, terminaltype)
        elif ext == ".cpu":
            cpustatdict = import_mpstatfile(f)
            for core in cores:
                cpuprof = cpustatdict[core]
                output = "{0}_core{1}.{2}".format(fwoext, core, terminaltype)
                drawcpu.plot_cpuprof(cpuprof, output, 1, terminaltype)
        elif ext == ".perf":
            perfstatdict = import_perfstatfile(f)
            for core in cores:
                cacheprof = perfstatdict[core]
                output = "{0}_core{1}cache.{2}".format(fwoext, core, terminaltype)
                drawcache.plot_cache(cacheprof, output, 1, terminaltype)
        elif ext == ".iohist":
            ioprof = [[float(v) for v in line.strip().split()] for line in open(f)]
            outprefix = fwoext
            drawio.plot_ioprof(ioprof, outprefix, 1, terminaltype)
        elif ext == ".cpuhist":
            cpuprof = [[float(v) for v in line.strip().split()] for line in open(f)]
            output = fwoext + "." + terminaltype
            drawcpu.plot_cpuprof(cpuprof, output, 1, terminaltype)
        elif ext == ".cachehist":
            cacheprof = [[float(v) for v in line.strip().split()] for line in open(f)]
            output = fwoext + "cache." + terminaltype
            drawcachemiss.plot_cachemiss(cacheprof, output, 1, terminaltype)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Usage : {0} rootdir [devices] [cores] [terminaltype]\n".format(sys.argv[0]))

    rootdir = sys.argv[1]
    devices = sys.argv[2].split(',') if len(sys.argv) >= 3 else []
    cores = sys.argv[3].split(',') if len(sys.argv) >= 4 else []
    terminaltype = sys.argv[4] if len(sys.argv) >= 5 else "png"

    statfiles = search_statfiles(rootdir)
    generate_allgraphs(statfiles, devices, cores, terminaltype)
