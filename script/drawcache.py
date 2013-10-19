#! /usr/bin/env python

import sys, os, glob, re, Gnuplot
import plotutil

def plot_cache(cacheprof, output, interval = 1, terminaltype = "png"):
    gp = plotutil.gpinit(terminaltype)
    gp('set output "{0}"'.format(output))
    gp.xlabel('elapsed time [s]')
    gp('set ytics nomirror')
    gp('set ylabel "count" offset 4')
    gp('set y2label "cache miss rate [%]" offset -2')
    gp('set grid xtics noytics noy2tics')
    gp('set yrange [0:*]')
    gp('set y2range [0:100]')
    gp('set y2tic 10')
    gds = []
    cacheref, cachemiss, cachemissrate = [], [], []
    for v in cacheprof:
        cacheref.append(v["cache-references"])
        cachemiss.append(v["cache-misses"])
        cachemissrate.append((float(v["cache-misses"]) / v["cache-references"]) * 100)
    xvals = [interval * i for i in range(len(cacheref))]
    plotprefdict = {"with_" : "lines"}
    gds.append(Gnuplot.Data(xvals, cacheref,
                            title = "cache reference", axes = "x1y1",
                            **plotprefdict))
    gds.append(Gnuplot.Data(xvals, cachemiss,
                            title = "cache miss", axes = "x1y1",
                            **plotprefdict))
    gds.append(Gnuplot.Data(xvals, cachemissrate,
                            title = "cache miss rate", axes = "x1y2",
                            **plotprefdict))
    gp.plot(*gds)
    sys.stdout.write("output {0}\n".format(output))
    gp.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write(
            "Usage : {0} statfile core [terminaltype]\n".format(sys.argv[0]))
        sys.exit(0)

    statfile = sys.argv[1]
    core = sys.argv[2]
    terminaltype = sys.argv[3] if len(sys.argv) >= 4 else "png"

    from profileutils import import_perfstatfile
    perfstatdict = import_perfstatfile(statfile)
    output = "{0}core{1}.{2}".format(os.path.splitext(statfile)[0], core, terminaltype)
    cacheprof = perfstatdict[core]
    plot_cache(cacheprof, output, 1, terminaltype)
