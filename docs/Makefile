# Minimal Makefile for Sphinx docs (cross-platform)
SPHINXOPTS    ?=
SPHINXBUILD   ?= uv run sphinx-build
PYTHON        ?= uv run python
SOURCEDIR     = source
BUILDDIR      = build
REPOROOT      = $(abspath $(CURDIR)/..)

.PHONY: help Makefile html clean data

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Build-time JSON data consumed by the interactive UX layer.
# Re-run any time scripts/data/*.py changes or refrigerant set is bumped.
data:
	cd "$(REPOROOT)" && $(PYTHON) -m scripts.data.gen_glossary
	cd "$(REPOROOT)" && $(PYTHON) -m scripts.data.gen_refrigerant_data
	cd "$(REPOROOT)" && $(PYTHON) -m scripts.data.gen_validation_data
	cd "$(REPOROOT)" && $(PYTHON) -m scripts.data.gen_timeseries_data

html: data
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	rm -rf $(BUILDDIR)/*

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
