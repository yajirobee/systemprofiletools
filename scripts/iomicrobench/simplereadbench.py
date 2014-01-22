#! /usr/bin/env python

import sys, os, shlex, re
import subprocess as sp

_mydirabspath = os.path.dirname(os.path.abspath(__file__))
_prjtopdir = os.path.dirname(os.path.dirname(_mydirabspath))
_commondir = os.path.join(os.path.dirname(_mydirabspath), "common")

sys.path.append(_commondir)
import util

class readbenchmarker(object):
    def exec_bench(self, cmd):
        p = sp.Popen(shlex.split(cmd), stdout = sp.PIPE)
        if p.wait() != 0:
            sys.stderr.write("measure failed : {0}\n".format(p.returncode))
            sys.exit(1)
        return self.proc_result(p.stdout)

    def exec_bench_wstat(self, cmd, iostatout, mpstatout):
        from profileutils import io_stat_watcher, mp_stat_watcher
        with io_stat_watcher(iostatout), mp_stat_watcher(mpstatout):
            return self.exec_bench(cmd)

    def exec_bench_wperfstat(self, cmd, iostatout, mpstatout, perfout):
        from profileutils import io_stat_watcher, mp_stat_watcher, perf_stat_watcher
        with io_stat_watcher(iostatout), mp_stat_watcher(mpstatout), perf_stat_watcher(perfout):
            return self.exec_bench(cmd)

    def proc_result(self, output):
        res = {}
        respattern = re.compile(r"([a-z_]+)\s(\d+(?:\.\d*)?)")
        reskeys = ["exec_time_sec", "total_ops",
                   "mb_per_sec", "io_per_sec", "usec_per_io"]
        for k in reskeys: res[k] = None
        for line in output:
            sys.stderr.write("  {0}".format(line))
            line = line.rstrip()
            match = respattern.match(line)
            if match and match.group(1) in res:
                res[match.group(1)] = float(match.group(2))
        return res

class simplereadbenchmanager(object):
    def __init__(self, benchexe, outdir, fpath, clearcachefunc,
                 odirectflg = False, statflg = False):
        self.cmdtmp = benchexe + " -s {iosize} -m {nthreads} -i {iterate} -t {timeout}"
        if odirectflg: self.cmdtmp += " -d"
        self.cmdtmp += " " + fpath
        self.outdir = outdir
        self.clearcachefunc = clearcachefunc
        self.statflg = statflg

        self.rbench = readbenchmarker()
        bname = os.path.splitext(os.path.basename(fpath))[0]
        self.recorder = util.sqlitehelper(os.path.join(outdir, "readspec_{0}.db".format(bname)))
        self.tblname = os.path.basename(benchexe)
        columns = (("iosize", "integer"),
                   ("nthreads", "integer"),
                   ("exec_time_sec", "real"),
                   ("total_ops", "integer"),
                   ("mb_per_sec", "real"),
                   ("io_per_sec", "real"),
                   ("usec_per_io", "real"))
        self.recorder.createtable(self.tblname, columns)

    def dobench(self, valdicts):
        for valdict in valdicts:
            self.clearcachefunc()
            cmd = self.cmdtmp.format(**valdict)
            sys.stderr.write("start : {0}\n".format(cmd))
            if self.statflg:
                bname = '_'.join([str(k) + str(v) for k, v in valdict.items()]) if valdict else "record"
                direc = os.path.join(self.outdir, self.tblname + bname)
                statoutdir = util.create_sequenceddir(direc)
                iostatout = os.path.join(statoutdir, "iostat_interval1.io")
                mpstatout = os.path.join(statoutdir, "mpstat_interval1.cpu")
                perfout = os.path.join(statoutdir, "perfstat_interval1.perfstat")
                res = self.rbench.exec_bench_wstat(cmd, iostatout, mpstatout)
            else: res = self.rbench.exec_bench(cmd)
            res.update(valdict)
            self.recorder.insert(self.tblname, res)
