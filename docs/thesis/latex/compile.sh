#!/bin/bash
# Compile LaTeX thesis document

# Navigate to latex directory
cd "$(dirname "$0")"

# Compile with pdflatex (run twice for references)
echo "Compiling main.tex..."
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex

# Check if PDF was created
if [ -f "main.pdf" ]; then
    echo "Success! PDF created: main.pdf"
    echo "File size: $(du -h main.pdf | cut -f1)"
else
    echo "Error: PDF was not created"
    exit 1
fi

# Clean auxiliary files (optional)
# rm -f *.aux *.log *.toc *.lof *.lot *.out
