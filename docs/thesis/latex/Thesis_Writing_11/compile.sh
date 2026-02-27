#!/bin/bash
##
##  Compile script for NKU Master's Thesis (XeLaTeX + bibtex8)
##  Usage:  bash compile.sh
##
##  Full build sequence:
##    xelatex main   -> generates .aux, .bbl stubs
##    bibtex8 main   -> processes bibliography
##    xelatex main   -> resolves citations
##    xelatex main   -> finalises cross-references (TOC, labels)
##

set -e

echo "=== Pass 1: xelatex ==="
xelatex -interaction=nonstopmode main.tex

echo "=== Pass 2: bibtex8 ==="
bibtex8 main

echo "=== Pass 3: xelatex ==="
xelatex -interaction=nonstopmode main.tex

echo "=== Pass 4: xelatex (final) ==="
xelatex -interaction=nonstopmode main.tex

echo ""
echo "=== Done. Output: main.pdf ==="
