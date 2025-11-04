# Final Compilation Instructions

This document provides step-by-step instructions for compiling the LeadMate_Project_Report.tex file successfully.

## Prerequisites

Make sure you have a LaTeX distribution installed on your system:
- **Windows**: Install MiKTeX or TeX Live
- **macOS**: Install MacTeX
- **Linux**: Install texlive-full package

## Compilation Steps

Follow these steps in order to compile the document successfully:

1. **Clean previous compilation files** (if any):
   Delete any existing files with these extensions:
   - .aux
   - .toc
   - .lof
   - .lot
   - .bbl
   - .blg
   - .out
   - .pdf (the old one)

2. **First pdflatex run**:
   ```
   pdflatex LeadMate_Project_Report.tex
   ```

3. **BibTeX run**:
   ```
   bibtex LeadMate_Project_Report.aux
   ```

4. **Second pdflatex run**:
   ```
   pdflatex LeadMate_Project_Report.tex
   ```

5. **Third pdflatex run**:
   ```
   pdflatex LeadMate_Project_Report.tex
   ```

## Common Issues and Solutions

### 1. Syntax Errors
- **Problem**: Missing figure environments or malformed TikZ diagrams
- **Solution**: All figure environments have been properly added and all TikZ diagrams are correctly formatted

### 2. "pdflatex is not recognized" error
- **Solution**: Add your LaTeX distribution's bin directory to your system PATH, or navigate to the bin directory before running commands.

### 2. "File not found" errors
- **Solution**: Make sure you're running the commands from the directory containing LeadMate_Project_Report.tex

### 3. Image not found errors
- **Solution**: Make sure all image files referenced in the document exist in the correct locations. 
  If you're using the Mermaid diagrams, you'll need to:
  1. Convert the Mermaid code from LeadMate_Updated_Mermaid_Flowcharts.md to image files
  2. Name the image files according to the diagram headings
  3. Place the images in the same directory as the LaTeX file

### 4. Overfull hbox warnings
- **Solution**: These are common and don't prevent compilation. They relate to text justification and can be ignored for now.

## What We Fixed

We've resolved all the critical errors that were preventing compilation:

1. **Duplicate labels**: Fixed all duplicate figure labels
2. **Malformed figure environments**: Corrected improperly closed figure environments
3. **Undefined references**: Updated all references to match actual labels
4. **Package compatibility**: Added necessary compatibility settings for pgfplots
5. **Header height warnings**: Fixed fancyhdr package warnings
6. **Bibliography**: Verified all citations have corresponding bibliography entries

## Expected Warnings (Not Errors)

You may still see these warnings which are normal and don't prevent successful compilation:

- Overfull hbox warnings (related to text formatting)
- Citation warnings (if compiling for the first time)
- Package deprecation warnings (common with LaTeX packages)

These warnings don't affect the final PDF output.

## Success Criteria

If the compilation is successful, you should see:
- A LeadMate_Project_Report.pdf file created
- No error messages (warnings are OK)
- Properly formatted document with all figures and references

If you continue to have issues, please check that:
1. All required LaTeX packages are installed
2. Your LaTeX distribution is up to date
3. You're following the compilation steps in the exact order specified