#! /usr/bin/env python

import sys, os, sqlite3
from plotutil import gpinit, query2gds

slide = False | True

cols = [{"name" : "mb_per_sec", "ylabel" : "Throughput [MB/S]"},
        {"name" : "io_per_sec", "ylabel" : "Throughput [IOPS]"},
        {"name" : "usec_per_io", "ylabel" : "Access Latency [us]"}]
tables = ["sequentialread", "randomread"]

def init_gnuplot(terminaltype):
    gp = gpinit(terminaltype)
    gp('set logscale x')
    gp('set grid')
    if slide:
        if "eps" == terminaltype:
            gp('set termoption font "Times-Roman,28"')
            plotprefdict = {"with_" : "linespoints lt 1 lw 6" }
        elif "png" == terminaltype:
            gp('set termoption font "Times-Roman,18"')
            plotprefdict = {"with_" : "linespoints lw 2"}
    else:
        plotprefdict = {"with_" : "linespoints" }
    return gp, plotprefdict

def plot_iosize_spec(dbpath, terminaltype = "png"):
    "draw iosize-spec graph"
    conn = sqlite3.connect(dbpath)
    fpath = os.path.dirname(dbpath) + "/" + os.path.splitext(dbpath)[0].rsplit('_', 1)[1]
    gp, plotprefdict = init_gnuplot(terminaltype)
    nthreadslistlist = [[r[0] for r in
                        conn.execute("select distinct nthreads from {0}".format(tbl))]
                       for tbl in tables]
    gp.xlabel("I/O size [B]")
    gp('set format x "%.0s%cB"')
    for col in cols:
        gp('set ylabel "{0}" offset 1'.format(col["ylabel"]))
        if col["name"] in ("mb_per_sec", "usec_per_io"): gp('set key left top')
        else: gp('set key right top')
        figpath = "{0}_{1}_xiosize.{2}".format(fpath, col["name"], terminaltype)
        gp('set output "{0}"'.format(figpath))
        gds = []
        for tbl, nth in zip(tables, nthreadslistlist):
            query = ("select iosize,avg({0}) from {1} where nthreads={{nthreads}} "
                     "group by iosize,nthreads".format(col["name"], tbl))
            gds.extend(query2gds(conn, query, nthreads = nth,
                                 title = "{0} {1} = {{{1}}}".format(tbl, "nthreads"),
                                 with_ = "linespoints"))
        sys.stdout.write('draw : {0}\n'.format(figpath))
        gp.plot(*gds)
    gp.close()
    conn.close()

def plot_nthread_spec(dbpath, terminaltype = "png"):
    "draw nthread-spec graph"
    conn = sqlite3.connect(dbpath)
    fpath = os.path.dirname(dbpath) + "/" + os.path.splitext(dbpath)[0].rsplit('_', 1)[1]
    gp, plotprefdict = init_gnuplot(terminaltype)
    iosizelistlist = [[r[0] for r in
                       conn.execute("select distinct iosize from {0}".format(tbl))]
                      for tbl in tables]
    gp.xlabel("nthreads")
    for col in cols:
        gp('set ylabel "{0}" offset 1'.format(col["ylabel"]))
        if col["name"] == "usec_per_io": gp('set key left top')
        else: gp('set key right top')
        figpath = "{0}_{1}_xnthreads.{2}".format(fpath, col["name"], terminaltype)
        gp('set output "{0}"'.format(figpath))
        gds = []
        for tbl, ios in zip(tables, iosizelistlist):
            query = ("select nthreads,avg({0}) from {1} where iosize={{iosize}} "
                     "group by iosize,nthreads".format(col["name"], tbl))
            gds.extend(query2gds(conn, query, iosize = ios,
                                 title = "{0} {1} = {{{1}}}".format(tbl, "iosize"),
                                 **plotprefdict))
        sys.stdout.write('draw : {0}\n'.format(figpath))
        gp.plot(*gds)
    gp.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stdout.write("Usage : {0} dbpath [eps|png]\n".format(sys.argv[0]))
        sys.exit(1)
    dbpath = os.path.abspath(sys.argv[1])
    terminaltype = sys.argv[2] if len(sys.argv) >= 3 else "png"

    if terminaltype != "png" and terminaltype != "eps":
        sys.stdout.write("wrong terminal type\n")
        sys.exit(1)

    plot_iosize_spec(dbpath, terminaltype)
    #plot_nthread_spec(dbpath, terminaltype)
