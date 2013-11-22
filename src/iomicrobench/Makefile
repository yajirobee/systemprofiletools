READBENCH = sequentialread randomread
IOREPLAYER = ioreplayer
TARGETS = $(READBENCH) $(IOREPLAYER)
LOCALOBJS = $(foreach target, $(TARGETS), $(addsuffix .o, $(target)))

top_builddir = ../..
bindir = $(top_builddir)/bin
commondir = ../common
CPPFLAGS = -I$(commondir)
include ../Makefile.global

$(READBENCH) : % : %.o $(commondir)/util.o
	$(CC) -o $(bindir)/$@ $^ $(LIBS)

$(IOREPLAYER): ioreplayer.o $(commondir)/util.o $(commondir)/arrayqueue.o
	$(CC) -o $(bindir)/$@ $^ $(LIBS)

cleanobject:
	/bin/rm -f $(addsuffix .o, $(READBENCH)) util.o

clean: cleanobject
	/bin/rm -f $(TARGETS) $(LOCALOBJS)

.PHONY: check-syntax clean

check-syntax:
	$(CC) -Wall -fsyntax-only $(CHK_SOURCES)
