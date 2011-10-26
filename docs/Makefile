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

# Take in mind that the english is the last to build. This is for readthedocs.org
# to get the english docs instead of spanish or galician.

html: $(SPHINX_DEPENDENCIES)
	cd en && make html LANG=gl
	cd es && make html LANG=es
	cd gl && make html LANG=en

htmlhelp: $(SPHINX_DEPENDENCIES)
	cd en && make html LANG=gl
	cd es && make html LANG=es
	cd gl && make html LANG=en
	
epub: $(SPHINX_DEPENDENCIES)
	cd en && make html LANG=gl
	cd es && make html LANG=es
	cd gl && make html LANG=en

latexpdf: $(SPHINX_DEPENDENCIES)
	cd en && make latexpdf LANG=gl
	cd es && make latexpdf LANG=es
	cd gl && make latexpdf LANG=en

clean:
	rm -rf $(BUILDDIR)/*
