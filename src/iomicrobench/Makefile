READBENCH = sequentialread randomread
IOREPLAYER = ioreplayer
TARGETS = $(READBENCH) $(IOREPLAYER)
LOCALOBJS = $(addsuffix .o, $(TARGETS))

top_builddir = ../..
bindir = $(top_builddir)/bin
commondir = ../common
CPPFLAGS = -I$(commondir)
include ../Makefile.global

$(READBENCH) : % : %.o $(commondir)/util.o
	$(CC) -o $(bindir)/$@ $^ $(LIBS)

$(IOREPLAYER): ioreplayer.o $(commondir)/util.o $(commondir)/arrayqueue.o
	$(CC) -o $(bindir)/$@ $^ $(LIBS)

clean:
	/bin/rm -f $(LOCALOBJS)

.PHONY: check-syntax clean

check-syntax:
	$(CC) -Wall -fsyntax-only $(CHK_SOURCES)
