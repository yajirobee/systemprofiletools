READBENCH = sequentialread randomread
IOREPLAYER = ioreplayer
TARGETS = $(READBENCH) $(IOREPLAYER)
LOCALOBJS = $(addsuffix .o, $(TARGETS))

top_builddir = ../..
bindir = $(top_builddir)/bin
commondir = ../common
VPATH = $(commondir)
CPPFLAGS = -I$(commondir)
include ../Makefile.global

$(READBENCH) : % : %.o util.o
	$(CC) -o $(bindir)/$@ $^ $(LIBS)

$(IOREPLAYER): ioreplayer.o util.o arrayqueue.o
	$(CC) -o $(bindir)/$@ $^ $(LIBS)

.PHONY: check-syntax clean

clean:
	/bin/rm -f $(LOCALOBJS)

check-syntax:
	$(CC) -Wall -fsyntax-only $(CHK_SOURCES)
