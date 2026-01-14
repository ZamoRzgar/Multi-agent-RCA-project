#!/bin/bash
# Compile thesis (BibTeX)

cd "$(dirname "$0")" || exit 1

set -e

pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex

echo "Success! PDF created: main.pdf" 
