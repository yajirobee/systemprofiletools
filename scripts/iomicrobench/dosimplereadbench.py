#! /usr/bin/env python

import sys, os, shlex, re, itertools, time
import subprocess as sp
import clearcache

_mydirabspath = os.path.dirname(os.path.abspath(__file__))
_prjtopdir = os.path.dirname(os.path.dirname(_mydirabspath))
_bindir = os.path.join(_prjtopdir, "bin")
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

def doreadbench(benchexe, outdir, fpath, valdicts, statflg = False):
    cmdtmp = benchexe + " -s {iosize} -m {nthreads} -i {iterate} -t {timeout} " + fpath
    rbench = readbenchmarker()
    bname = os.path.splitext(os.path.basename(fpath))[0]
    recorder = util.sqlitehelper(os.path.join(outdir, "readspec_{0}.db".format(bname)))
    tblname = os.path.basename(benchexe)
    columns = (("iosize", "integer"),
               ("nthreads", "integer"),
               ("exec_time_sec", "real"),
               ("total_ops", "integer"),
               ("mb_per_sec", "real"),
               ("io_per_sec", "real"),
               ("usec_per_io", "real"))
    columns = recorder.createtable(tblname, columns)
    for valdict in valdicts:
        clearcache.clear_cache(2 ** 30)
        cmd = cmdtmp.format(**valdict)
        sys.stderr.write("start : {0}\n".format(cmd))
        if statflg:
            bname = '_'.join([str(k) + str(v) for k, v in valdict.items()]) if valdict else "record"
            direc = os.path.join(outdir, tblname + bname)
            statoutdir = util.create_sequenceddir(direc)
            iostatout = os.path.join(statoutdir, "iostat_interval1.io")
            mpstatout = os.path.join(statoutdir, "mpstat_interval1.cpu")
            perfout = os.path.join(statoutdir, "perfstat_interval1.perfstat")
            res = rbench.exec_bench_wstat(cmd, iostatout, mpstatout)
        else: res = rbench.exec_bench(cmd)
        res.update(valdict)
        recorder.insert(tblname, res)

def main(fpath):
    iomax = 2 ** 36
    timeout = 30
    iosizes = [2 ** i for i in range(9, 22)]
    nthreads = [2 ** i for i in range(11)]
    valdicts = []
    for vals in itertools.product(iosizes, nthreads):
        valdicts.append({"iosize" : vals[0],
                         "nthreads" : vals[1],
                         "timeout": timeout,
                         "iterate": iomax / (vals[0] * vals[1])})

    outdir = "/data/local/keisuke/{0}".format(time.strftime("%Y%m%d%H%M%S", time.gmtime()))
    os.mkdir(outdir)

    for i in range(5):
        # sequential read
        sys.stdout.write("sequential read\n")
        doreadbench(os.path.join(_bindir, "sequentialread"), outdir, fpath, valdicts, True)
        time.sleep(300)

        # random read
        sys.stdout.write("random read\n")
        doreadbench(os.path.join(_bindir, "randomread"), outdir, fpath, valdicts, True)
        time.sleep(300)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stdout.write("Usage : {0} fpath\n".format(sys.argv[0]))
        sys.exit(0)
    fpath = sys.argv[1]

    main(fpath)
