#! /usr/bin/env python

import sys, os, shlex, re
import subprocess as sp
from createworkload import create_workload

_mydirabspath = os.path.dirname(os.path.abspath(__file__))
_prjtopdir = os.path.dirname(os.path.dirname(_mydirabspath))
_commondir = os.path.join(os.path.dirname(_mydirabspath), "common")

sys.path.append(_commondir)
import util

class mixedloadbenchmarker(object):
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
        reskeys = ["exec_time_sec", "generated_tasks", "operated_tasks", "usec_per_task",
                   "read_mb_per_sec", "read_io_per_sec", "read_usec_per_io",
                   "write_mb_per_sec", "write_io_per_sec", "write_usec_per_io"]
        for k in reskeys: res[k] = None
        for line in output:
            sys.stderr.write("  {0}".format(line))
            line = line.rstrip()
            match = respattern.match(line)
            if match and match.group(1) in res:
                res[match.group(1)] = float(match.group(2))
        return res

class mixedloadbenchmanager(object):
    def __init__(self, benchexe, outdir,
                 readfiles, writefiles, iodumpfile,
                 clearcachefunc, workloadfunc,
                 odirectflg = False, statflg = False):
        self.cmdtmp = benchexe
        if odirectflg: self.cmdtmp += " -d"
        self.outdir = outdir
        self.readfiles = readfiles
        self.writefiles = writefiles
        self.iodumpfile = iodumpfile
        self.clearcachefunc = clearcachefunc
        self.workloadfunc = workloadfunc
        self.statflg = statflg

        self.mixbench = mixedloadbenchmarker()
        self.recorder = util.sqlitehelper(os.path.join(outdir, "mixedbench.db"))
        self.tblname = "mixedworkload"
        columns = (("iosize", "integer"),
                   ("nthreads", "integer"),
                   ("exec_time_sec", "real"),
                   ("generated_tasks", "integer"),
                   ("operated_tasks", "integer"),
                   ("usec_per_task", "real"),
                   ("read_mb_per_sec", "real"),
                   ("read_io_per_sec", "real"),
                   ("read_usec_per_io", "real"),
                   ("write_mb_per_sec", "real"),
                   ("write_io_per_sec", "real"),
                   ("write_usec_per_io", "real"))
        self.recorder.createtable(self.tblname, columns)

    def generatecommand(self, optdict):
        cmd = self.cmdtmp
        if "nthreads" in optdict: cmd += " -m " + str(optdict["nthreads"])
        if "timeout" in optdict: cmd += " -t " + str(optdict["timeout"])
        cmd += " " + self.iodumpfile
        return cmd

    def dobench(self, valdicts):
        for d in valdicts:
            create_workload(self.iodumpfile, d["numtasks"],
                            self.readfiles[:], self.writefiles[:],
                            d["nthreads"], d["iosize"], d["maxiter"], self.workloadfunc)
            self.clearcachefunc()
            cmd = self.generatecommand(d)
            sys.stderr.write("start : {0}\n".format(cmd))
            if self.statflg:
                dirname = self.tblname
                for key in ("nthreads", "iosize"):
                    if key in d: dirname += "_{k}{v}".format(k = key, v = d[key])
                direc = os.path.join(self.outdir, dirname)
                statoutdir = util.create_sequenceddir(direc)
                iostatout = os.path.join(statoutdir, "iostat_interval1.io")
                mpstatout = os.path.join(statoutdir, "mpstat_interval1.cpu")
                res = self.mixbench.exec_bench_wstat(cmd, iostatout, mpstatout)
            else: res = self.mixbench.exec_bench(cmd)
            res.update(d)
            self.recorder.insert(self.tblname, res)
