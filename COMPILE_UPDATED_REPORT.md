# How to Compile the Updated LeadMate Report

## Overview

This document provides instructions for compiling the updated LeadMate report that includes the CodeClarity agent and updated system architecture diagrams.

## Prerequisites

Before compiling the report, ensure you have the following installed:

1. **LaTeX Distribution**:
   - TeX Live (Linux/Mac)
   - MiKTeX (Windows)
   - Overleaf (Online LaTeX editor)

2. **Required LaTeX Packages** (usually included in standard distributions):
   - graphicx
   - amsmath
   - amssymb
   - fancyhdr
   - titlesec
   - tocloft
   - listings
   - xcolor
   - hyperref
   - caption
   - subcaption
   - float
   - booktabs
   - array
   - multirow
   - longtable
   - enumitem

## Files Required for Compilation

Make sure the following files are in the same directory:
- `LeadMate_Sanjay_Report.tex` (main report file)
- `APPENDIX_Updated_Mermaid_Code_Sanjay.tex` (updated appendix with Mermaid diagrams)

## Compilation Instructions

### Method 1: Command Line (TeX Live/MiKTeX)

1. Open a terminal/command prompt
2. Navigate to the directory containing the LaTeX files
3. Run the following commands:

```bash
pdflatex LeadMate_Sanjay_Report.tex
bibtex LeadMate_Sanjay_Report.aux
pdflatex LeadMate_Sanjay_Report.tex
pdflatex LeadMate_Sanjay_Report.tex
```

Note: Multiple runs of pdflatex are required to properly generate the table of contents, references, and cross-references.

### Method 2: Using LaTeX Editors

#### TeXstudio
1. Open `LeadMate_Sanjay_Report.tex` in TeXstudio
2. Click "Build & View" (F1) to compile
3. If references aren't updated, click "Bibliography" (F8) then "Build & View" again

#### Overleaf
1. Create a new project
2. Upload both `LeadMate_Sanjay_Report.tex` and `APPENDIX_Updated_Mermaid_Code_Sanjay.tex`
3. Click "Recompile" to build the PDF

## Troubleshooting

### Common Issues

1. **Missing packages**: If you get package errors, install the missing packages using your LaTeX distribution's package manager.

2. **Input file not found**: Make sure both the main .tex file and the appendix file are in the same directory.

3. **Bibliography not showing**: Run the compilation sequence (pdflatex → bibtex → pdflatex → pdflatex) completely.

4. **References not updating**: Run pdflatex multiple times to update all cross-references.

### Error Messages

- **"File 'APPENDIX_Updated_Mermaid_Code_Sanjay.tex' not found"**: Ensure the appendix file is in the same directory as the main report.

- **"LaTeX Error: File 'listings.sty' not found"**: Install the listings package through your LaTeX distribution's package manager.

## Generated Files

After successful compilation, you will have:
- `LeadMate_Sanjay_Report.pdf` (the final report)
- Various auxiliary files (`.aux`, `.toc`, `.lof`, `.lot`, `.bbl`, `.blg`, etc.) that can be safely deleted after compilation

## Viewing the Report

Open `LeadMate_Sanjay_Report.pdf` with any PDF viewer to see the complete report with:
- Updated content including the CodeClarity agent
- All system architecture diagrams
- References to the appendix with Mermaid code

## Notes

- The report is designed to be compiled with PDFLaTeX
- The appendix contains the Mermaid code for all diagrams, which can be used to generate images for presentations
- The CodeClarity agent integration enhances the system's capabilities by providing technical insights from code repositories