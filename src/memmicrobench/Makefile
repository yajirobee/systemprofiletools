MEMBENCH = membench
TARGETS = $(MEMBENCH)
LOCALOBJS = $(addsuffix .o, $(TARGETS))

top_builddir = ../..
bindir = $(top_builddir)/bin
commondir = ../common
VPATH = $(commondir)
CPPFLAGS = -I$(commondir)
include ../Makefile.global

$(MEMBENCH) : % : %.o util.o
	$(CC) -o $(bindir)/$@ $^ $(LIBS)

$(MEMBENCH).c: membench-inner-rand.c

membench-inner-rand.c:
	python ./genmembenchinnerloop.py > $@

.PHONY: check-syntax clean

clean:
	/bin/rm -f $(LOCALOBJS) membench-inner-rand.c

check-syntax:
	$(CC) -Wall -fsyntax-only $(CHK_SOURCES)
