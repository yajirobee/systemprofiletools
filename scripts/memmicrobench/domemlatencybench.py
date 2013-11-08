#! /usr/bin/env python

import sys, os, shlex, re, sqlite3, itertools, time
import subprocess as sp
import clearcache

_mydirabspath = os.path.dirname(os.path.abspath(__file__))
_prjtopdir = os.path.dirname(os.path.dirname(_mydirabspath))
_bindir = os.path.join(_prjtopdir, "bin")
_commondir = os.path.join(os.path.dirname(_mydirabspath), "common")

sys.path.append(_commondir)
import util

class membenchmarker(object):
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
        reslist = []
        respattern = re.compile(r"([a-z_]+)\s((?:\d+(?:\.\d*)?)(?:[eE][-+]?\d+))")
        reskeys = ["memory_alloc_node", "exec_time_sec", "total_ops", "total_clk",
                   "ops_per_sec", "clk_per_op", "usec_per_op"]
        curres = {}
        for k in reskeys: curres[k] = None
        for line in ouput:
            sys.stderr.write("  {0}".format(line))
            line = line.rstrip()
            match = respattern.match(line)
            if match and match.group(1) in curres:
                res[match.group(1)] = float(match.group(2))
                if match.group(1) == "usec_per_op":
                    reslist.append(curres)
                    curres = {}
                    for k in reskeys: curres[k] = None
        return reslist

def domembench(benchexe, outdir, valdicts, statflg = False):
    cmdtmp = benchexe + "-c {core} -s {access_size}"
    membench = membenchmarker()
    recorder = util.sqlitehelper(os.path.join(outdir, "memspec.db"))
    tblname = os.path.basename(benchexe)
    columns = (("core", "integer"),
               ("access_size", "integer"),
               ("memory_alloc_node", "integer"),
               ("exec_time_sec", "real"),
               ("total_ops", "integer"),
               ("total_clk", "integer"),
               ("ops_per_sec", "real"),
               ("clk_per_op", "real"),
               ("usec_per_op", "real"))
    columns = recorder.createtable(tblname, columns)
    for valdict in valdicts:
        clearcache.clear_os_cache()
        cmd = cmdtmp.format(**valdict)
        sys.stderr.write("start : {0}\n".format(cmd))
        if statflg:
            bname = '_'.join([str(k) + str(v) for k, v in valdict.items()]) if valdict else "record"
            direc = os.path.join(outdir, tblname + bname)
            statoutdir = util.create_sequenceddir(direc)
            iostatout = os.path.join(statoutdir, "iostat_interval1.io")
            mpstatout = os.path.join(statoutdir, "mpstat_interval1.cpu")
            perfout = os.path.join(statoutdir, "perfstat_interval1.perfstat")
            reslist = membench.exec_bench_wstat(cmd, iostatout, mpstatout)
        else: reslist = membench.exec_bench(cmd)
        for res in reslist:
            res.update(valdict)
            recorder.insert(tblname, res)

def main():
    sizelist = [2 ** i for i in range(14, 33)]
    valdicts = [{"core": 1, "access_size": size} for size in sizelist]

    outdir = "/data/local/keisuke/{0}".format(time.strftime("%Y%m%d%H%M%S", time.gmtime()))
    os.mkdir(outdir)

    for i in range(5):
        # random read
        sys.stdout.write("memory random bench : {0}\n".format(i))
        domembench(outdir, valdicts)
        time.sleep(30)

if __name__ == "__main__":
    main()
