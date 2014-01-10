CC = gcc
CFLAGS =
LDFLAGS =
BINDIR = ../../../bin
BENCHDATADIR = /data/iod8raid0/benchdata
NUMBERS = $(shell seq 0 63)
TARGET = $(addprefix $(BENCHDATADIR)/benchdata, $(NUMBERS))

all: $(TARGET)

$(TARGET):
	$(BINDIR)/genbenchdata $@ 4294967296

clean:
	/bin/rm -f $(TARGET)

.c.o:
	$(CC) $(CFLAGS) -c $<

.PHONY: check-syntax

check-syntax:
	$(CC) -Wall -fsyntax-only $(CHK_SOURCES)
