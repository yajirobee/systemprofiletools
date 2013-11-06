#! /usr/bin/env python

import sys, os, sqlite3, glob, re

class sqlitehelper(object):
    def __init__(self, dbpath):
        self.conn = sqlite3.connect(dbpath)
        self.tbldict = {}
        for r in self.conn.execute("select name, sql from sqlite_master where type = 'table'"):
            match = re.search(".*\((.*)\).*", r[1])
            columns = match.group(1).split(',')
            self.tbldict[r[0]] = [v.strip().split()[0] for v in columns]

    def createtable(self, tblname, columns):
        if tblname in self.tbldict:
            sys.stderr.write("table already exist : {0}\n".format(tblname))
        else:
            schema = ','.join([' '.join(v) for v in columns])
            self.conn.execute("create table {0}({1})".format(tblname, schema))
            self.tbldict[tblname] = [v[0] for v in columns]
        return self.tbldict[tblname]

    def insert(self, tblname, valdict):
        columns = self.tbldict[tblname]
        orderedvals = [valdict.get(col, 0) for col in columns]
        valmask = ','.join('?' * len(columns))
        self.conn.execute("insert into {0} values ({1})".format(tblname, valmask), orderedvals)
        self.conn.commit()

def create_sequenceddir(destdir):
    nums = [int(os.path.basename(d)) for d in glob.glob(os.path.join(destdir, "[0-9]*"))]
    n = max(nums) + 1 if nums else 0
    newseqdir = os.path.join(destdir, str(n))
    os.makedirs(newseqdir)
    return newseqdir
