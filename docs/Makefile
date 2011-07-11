# Makefile for Sphinx documentation
#

PYTHON = python

.PHONY: all clean html epub latex latexpdf htmlhelp

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =
BUILDDIR      = build

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees/$(LANG) $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

SPHINX_DEPENDENCIES = es/Makefile

%/Makefile : en/Makefile
	$(PYTHON) -c "import shutil; shutil.copyfile('$<, '$@')"

html: $(SPHINX_DEPENDENCIES)
	cd en && make html LANG=en
	cd es && make html LANG=es
	cd gl && make html LANG=gl

htmlhelp: $(SPHINX_DEPENDENCIES)
	cd en && make html LANG=en
	cd es && make html LANG=es
	cd gl && make html LANG=gl
	
epub: $(SPHINX_DEPENDENCIES)
	cd en && make html LANG=en
	cd es && make html LANG=es
	cd gl && make html LANG=gl

latexpdf: $(SPHINX_DEPENDENCIES)
	cd en && make html LANG=en
	cd es && make html LANG=es
	cd gl && make html LANG=gl

clean:
	rm -rf $(BUILDDIR)/*
