#! /usr/bin/env python

import sys, os#, sqlite3
from pysqlite2 import dbapi2 as sqlite3
from plotutil import gpinit, query2gds

slide = False #| True

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
            plotprefdict = {"with_" : "yerrorlines lt 1 lw 6" }
        elif "png" == terminaltype:
            gp('set termoption font "Times-Roman,18"')
            plotprefdict = {"with_" : "yerrorlines lw 2"}
    else:
        plotprefdict = {"with_" : "yerrorlines" }
    return gp, plotprefdict

def plot_iosize_spec(dbpath, terminaltype = "png"):
    "draw iosize-spec graph"
    conn = sqlite3.connect(dbpath)
    conn.enable_load_extension(True)
    conn.load_extension(os.path.expanduser("~/common/libsqlitefunctions.so"))
    fpath = os.path.dirname(dbpath) + "/" + os.path.splitext(dbpath)[0].rsplit('_', 1)[1]
    gp, plotprefdict = init_gnuplot(terminaltype)

    gp.xlabel("I/O size [B]")
    gp('set format x "%.0s%cB"')
    for tbl in tables:
        nthreadlist = [r[0] for r in conn.execute("select distinct nthread from {0}".format(tbl))]
        gp('set title "{0}"'.format(tbl.title()))
        for col in cols:
            gp('set ylabel "{0}" offset 1'.format(col["ylabel"]))
            if col["name"] in ("mb_per_sec", "usec_per_io"): gp('set key left top')
            else: gp('set key right top')
            figpath = "{0}_{1}_{2}_xiosize.{3}".format(fpath, tbl, col["name"], terminaltype)
            gp('set output "{0}"'.format(figpath))
            query = ("select iosize,avg({0}),stdev({0}) "
                     "from {1} where nthread={{nthread}} "
                     "group by iosize,nthread".format(col["name"], tbl))
            gds = query2gds(conn, query, nthread = nthreadlist,
                            title = "nthreads = {nthread}", **plotprefdict)
            sys.stdout.write('draw : {0}\n'.format(figpath))
            gp.plot(*gds)
    gp.close()
    conn.close()

def plot_nthread_spec(dbpath, terminaltype = "png"):
    "draw nthread-spec graph"
    conn = sqlite3.connect(dbpath)
    conn.enable_load_extension(True)
    conn.load_extension(os.path.expanduser("~/common/libsqlitefunctions.so"))
    fpath = os.path.dirname(dbpath) + "/" + os.path.splitext(dbpath)[0].rsplit('_', 1)[1]
    gp, plotprefdict = init_gnuplot(terminaltype)

    gp.xlabel("nthread")
    for tbl in tables:
        iosizelist = [r[0] for r in conn.execute("select distinct iosize from {0}".format(tbl))]
        gp('set title "{0}"'.format(tbl.title()))
        for col in cols:
            gp('set ylabel "{0}" offset 1'.format(col["ylabel"]))
            if col["name"] == "usec_per_io": gp('set key left top')
            else: gp('set key right top')
            figpath = "{0}_{1}_{2}_xnthread.{3}".format(fpath, tbl, col["name"], terminaltype)
            gp('set output "{0}"'.format(figpath))
            query = ("select nthread,avg({0}),stdev({0})"
                     " from {1} where iosize={{iosize}} "
                     "group by iosize,nthread".format(col["name"], tbl))
            gds = query2gds(conn, query, iosize = iosizelist,
                            title = "iosize = {iosize}", **plotprefdict)
            sys.stdout.write('draw : {0}\n'.format(figpath))
            gp.plot(*gds)
    gp.close()
    conn.close()

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
    plot_nthread_spec(dbpath, terminaltype)
