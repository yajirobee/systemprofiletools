LOCALOBJS = util.o arrayqueue.o
OBJS = $(LOCALOBJS) clearcache.o genbenchdata.o
CLEARCACHE = clearcache
GENBENCHDATA = genbenchdata
TARGETS = $(LOCALOBJS) $(CLEARCACHE) $(GENBENCHDATA)

top_builddir = ../..
bindir = $(top_builddir)/bin
include ../Makefile.global

$(CLEARCACHE) $(GENBENCHDATA): % : %.o
	$(CC) -o $(bindir)/$@ $^

.PHONY: check-syntax clean

clean:
	/bin/rm -f $(OBJS)

check-syntax:
	$(CC) -Wall -fsyntax-only $(CHK_SOURCES)
