#! /usr/bin/env python

import sys, os, re, Gnuplot
import plotutil

slide = False | True

def init_gnuplot(terminaltype):
    gp = plotutil.gpinit(terminaltype)
    gp.xlabel("elapsed time [s]")
    gp('set grid')
    if slide:
        gp('set termoption font "Times-Roman,22"')
        plotprefdict = {"with_" : "lines lw 2"}
    else:
        plotprefdict = {"with_" : "lines"}
    return gp, plotprefdict

def draw_mbps(xvals, rmbps, wmbps, output, terminaltype):
    gp, plotprefdict = init_gnuplot(terminaltype)
    gp('set output "{0}"'.format(output))
    gp.ylabel("I/O throughput [MB/s]")
    gp('set yrange [0:*]')
    gdrmbps = Gnuplot.Data(xvals, rmbps, title = "Read", **plotprefdict)
    gdwmbps = Gnuplot.Data(xvals, wmbps, title = "Write", **plotprefdict)
    gp.plot(gdrmbps, gdwmbps)

def draw_iops(xvals, riops, wiops, output, terminaltype):
    gp, plotprefdict = init_gnuplot(terminaltype)
    gp('set output "{0}"'.format(output))
    gp.ylabel("I/O throughput [IOPS]")
    gp('set yrange [0:*]')
    gdrmbps = Gnuplot.Data(xvals, riops, title = "Read", **plotprefdict)
    gdwmbps = Gnuplot.Data(xvals, wiops, title = "Write", **plotprefdict)
    gp.plot(gdrmbps, gdwmbps)

def draw_iosize(xvals, riosize, wiosize, output, terminaltype):
    gp, plotprefdict = init_gnuplot(terminaltype)
    gp('set output "{0}"'.format(output))
    gp.ylabel("I/O size [KB]")
    gdrios = Gnuplot.Data(xvals, riosize, title = "Read", **plotprefdict)
    gdwios = Gnuplot.Data(xvals, wiosize, title = "Write", **plotprefdict)
    gp.plot(gdrios, gdwios)

def plot_ioprof(ioprof, outprefix, interval = 1, terminaltype = "png"):
    riops, wiops, rmbps, wmbps, riosize, wiosize = [[] for i in range(6)]
    xvals = [interval * i for i in range(len(ioprof))]
    for vals in ioprof:
        riops.append(vals[2])
        wiops.append(vals[3])
        rmbps.append(vals[4])
        wmbps.append(vals[5])
        riosize.append((vals[4] * 1000.) / vals[2] if vals[2] != 0 else 0.)
        wiosize.append((vals[5] * 1000.) / vals[3] if vals[3] != 0 else 0.)

    # draw mbps graph
    output = "{0}mbps.{1}".format(outprefix, terminaltype)
    draw_mbps(xvals, rmbps, wmbps, output, terminaltype)
    sys.stdout.write("output {0}\n".format(output))

    # draw iops graph
    output = "{0}iops.{1}".format(outprefix, terminaltype)
    draw_iops(xvals, riops, wiops, output, terminaltype)
    sys.stdout.write("output {0}\n".format(output))

    # draw iosize graph
    output = "{0}iosize.{1}".format(outprefix, terminaltype)
    draw_iosize(xvals, riosize, wiosize, output, terminaltype)
    sys.stdout.write("output {0}\n".format(output))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stdout.write(
            "Usage : {0} iostatfile devname [eps|png]\n".format(sys.argv[0]))
        sys.exit(0)

    iofile = sys.argv[1]
    devname = sys.argv[2] if len(sys.argv) >= 3 else None
    terminaltype = sys.argv[3] if len(sys.argv) >= 4 else "png"
    if terminaltype != "png" and terminaltype != "eps":
        sys.stdout.write("wrong terminal type\n")
        sys.exit(1)

    if len(sys.argv) == 2:
        ioprof = [[float(v) for v in line.strip().split()] for line in open(iofile)]
    else:
        from profileutils import import_iostatfile
        iostatdict = import_iostatfile(iofile)
        ioprof = iostatdict[devname]

    outprefix = os.path.splitext(iofile)[0]
    plot_ioprof(ioprof, outprefix, 1, terminaltype)
