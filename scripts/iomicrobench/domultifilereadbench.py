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

class multifilereadbenchmarker(object):
    def exec_bench(self, cmd, nthreads, fpaths):
        threadsperfilelist = [nthreads / len(fpaths) for lu in fpaths]
        for i in range(nthreads % len(fpaths)): threadsperfilelist[i] += 1
        procs = [sp.Popen(shlex.split(cmd.format(fpath = fpath, nthreads = nth)),
                          stdout = sp.PIPE, stderr = open("/dev/null", "w"))
                 for fpath, nth in zip(fpaths, threadsperfilelist)]
        if any([p.wait() for p in procs]):
            sys.stderr.write("storage_measure failed\n")
            sys.exit(1)
        return self.proc_result([p.stdout for p in procs])

    def exec_bench_wstat(self, cmd, fpaths, iostatout, mpstatout):
        from profileutils import io_stat_watcher, mp_stat_watcher
        with io_stat_watcher(iostatout), mp_stat_watcher(mpstatout):
            return self.exec_bench(cmd, nthreads, fpaths)

    def exec_bench_wstat(self, cmd, fpaths, iostatout, mpstatout, perfout):
        from profileutils import io_stat_watcher, mp_stat_watcher, perf_stat_watcher
        with io_stat_watcher(iostatout), mp_stat_watcher(mpstatout), perf_stat_watcher(perfout):
            return self.exec_bench(cmd, nthreads, fpaths)

    def proc_result(self, outputs):
        res = {}
        respattern = re.compile(r"([a-z_]+)\s(\d+(?:\.\d*)?)")
        reskeys = ["start_time", "finish_time", "total_ops"]
        for key in reskeys: res[k] = []
        for output in outputs:
            for line in output:
                line = line.rstrip()
                match = respattern.match(line)
                if match and match.group(1) in res:
                    res[match.group(1)].append(float(match.group(2)))

        for key in reskeys:
            assert len(res[key]) == len(outputs), "could not collect result : " + key
        res["exec_time_sec"] = max(res["finish_time"]) - min(res["start_time"])
        res["bench_time_sec"] = min(res["finish_time"]) - max(res["start_time"])
        res["total_ops"] = sum(res["total_ops"])
        return res

def doreadbench(benchexe, outdir, fpaths, valdicts, statflg = False):
    cmdtmp = benchexe + " -s {iosize} -m {{nthreads}} -i {iterate} -t {timeout} {{fpath}}"
    rbench = multifilereadbenchmarker()
    dbpath = os.path.join(outdir, "readspec_files{0}.db".format(len(fpaths)))
    recorder = util.sqlitehelper(dbpath)
    tblname = os.path.basename(benchexe)
    columns = (("iosize", "integer"),
               ("nthreads", "integer"),
               ("exec_time_sec", "real"),
               ("bench_time_sec", "real"),
               ("total_ops", "integer"),
               ("mb_per_sec", "real"),
               ("io_per_sec", "real"),
               ("usec_per_io", "real"))
    columns = recorder.createtable(tblname, columns)
    for valdict in valdicts:
        clearcache.clear_cache(2 ** 35)
        nthreads = valdict["nthreads"]
        cmd = cmdtmp.format(**valdict)
        paramstr = ' '.join(["{0} = {1}".format(k, v) for k, v in valdict.items()])
        sys.stderr.write("start : {0} {1}\n".format(tblname, paramstr))
        if statflg:
            bname = '_'.join([str(k) + str(v) for k, v in valdict.items()]) if valdict else "record"
            direc = os.path.join(outdir, tblname + bname)
            statoutdir = util.create_sequenceddir(direc)
            iostatout = os.path.join(statoutdir, "iostat_interval1.io")
            mpstatout = os.path.join(statoutdir, "mpstat_interval1.cpu")
            perfout = os.path.join(statoutdir, "perfstat_interval1.perfstat")
            res = rbench.exec_bench_wstat(cmd, nthreads, fpaths, iostatout, mpstatout)
        else: res = rbench.exec_bench(cmd, nthreads, fpaths)
        res.update(valdict)
        res["io_per_sec"] = res["total_ops"] / res["exec_time_sec"]
        res["mb_per_sec"] = res["io_per_sec"] * valdict["iosize"] / 2 ** 20
        res["usec_per_io"] = res["exec_time_sec"] * (10 ** 6) / res["total_ops"]
        for key in ["exec_time_sec", "bench_time_sec", "total_ops",
                    "io_per_sec", "mb_per_sec", "usec_per_io"]:
            sys.stderr.write("  {0} : {1}\n".format(key, res[key]))
        recorder.insert(tblname, res)

def main(fpaths):
    iomax = 2 ** 38
    timeout = 30
    iosizes = [2 ** i for i in range(9, 22)]
    nthreadslist = [2 ** i for i in range(7)]
    maxnthreads = max(nthreadslist)
    maxfsize = iomax / maxnthreads
    valdicts = []
    for vals in itertools.product(iosizes, nthreadslist):
        valdicts.append({"iosize" : vals[0],
                         "nthreads" : vals[1],
                         "timeout": timeout,
                         "iterate": maxfsize / vals[0]})

    outdir = "/data/local/keisuke/{0}".format(time.strftime("%Y%m%d%H%M%S", time.gmtime()))
    os.mkdir(outdir)

    for i in range(5):
        # sequential read
        sys.stdout.write("sequential read\n")
        doreadbench(os.path.join(_bindir, "sequentialread"), outdir, fpaths, valdicts, True)
        time.sleep(300)

        # random read
        sys.stdout.write("random read\n")
        doreadbench(os.path.join(_bindir, "randomread"), outdir, fpaths, valdicts, True)
        time.sleep(300)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stdout.write("Usage : {0} benchdatadir\n".format(sys.argv[0]))
        sys.exit(0)
    datadir = sys.argv[1]
    assert os.path.isdir(datadir), "datadir does not exist"

    fpaths = os.listdir(datadir)
    main(fpaths)
