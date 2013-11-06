top_builddir = ..
bindir = $(top_builddir)/bin

all:
	@if [ ! -d $(bindir) ]; then \
		mkdir -p $(bindir); \
	fi
	$(MAKE) -C common
	$(MAKE) -C iomicrobench

clean:
	/bin/rm -rf $(bindir)
	$(MAKE) -C common $@
	$(MAKE) -C iomicrobench $@

