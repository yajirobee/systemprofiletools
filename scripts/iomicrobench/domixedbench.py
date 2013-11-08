#! /usr/bin/env python

import sys, os, shlex, re, time
import subprocess as sp
from createworkload import create_workload
import clearcache

_mydirabspath = os.path.dirname(os.path.abspath(__file__))
_prjtopdir = os.path.dirname(os.path.dirname(_mydirabspath))
_bindir = os.path.join(_prjtopdir, "bin")
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


def dobench(benchexe, outdir, valdicts, statflg = False):
    iodumpfile = "/tmp/iodump"
    cmdtmp = benchexe + " -m {nthreads} " + iodumpfile
    mixbench = mixedloadbenchmarker()
    dbpath = os.path.join(outdir, "mixedbench.db")
    recorder = util.sqlitehelper(dbpath)
    tblname = "mixedworkload"
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
    columns = recorder.createtable(tblname, columns)
    workloadfunc = lambda i: i % 4 <= 2
    for d in valdicts:
        create_workload(iodumpfile, d["numtasks"],
                        d["readfiles"][:], d["writefiles"][:],
                        d["nthreads"], d["iosize"], 1 << 10, workloadfunc)
        clearcache.clear_cache()
        cmd = cmdtmp.format(**d)
        sys.stderr.write("start : {0}\n".format(cmd))
        if statflg:
            direc = os.path.join(outdir, tblname + "_nthreads{0}".format(d["nthreads"]))
            statoutdir = util.create_sequenceddir(direc)
            iostatout = os.path.join(statoutdir, "iostat_interval1.io")
            mpstatout = os.path.join(statoutdir, "mpstat_interval1.cpu")
            res = mixbench.exec_bench_wstat(cmd, iostatout, mpstatout)
        else: res = mixbench.exec_bench(cmd)
        res.update(d)
        recorder.insert(tblname, res)

def main():
    datadir = "/data/iod8raid0/tpchdata"
    valdicts = [{"nthreads": 1 << i, "numtasks": 4000,
                 "iosize": 1 << 13, "maxiter": 1 << 10,
                 "readfiles": [os.path.join(datadir, "benchdata" + str(i))
                               for i in range(32)],
                 "writefiles": [os.path.join(datadir, "benchdata" + str(i))
                                for i in range(32, 64)]
                 } for i in range(5)]

    outdir = "/data/local/keisuke/{0}".format(time.strftime("%Y%m%d%H%M%S", time.gmtime()))
    os.mkdir(outdir)

    for i in range(5):
        dobench(os.path.join(_bindir, "ioreplayer"), outdir, valdicts, True)

if __name__ == "__main__":
    main()
