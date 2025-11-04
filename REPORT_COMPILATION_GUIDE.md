# LeadMate Project Report Compilation Guide

This document provides instructions on how to compile the LaTeX report for the LeadMate project.

## Prerequisites

To compile the LaTeX report, you need to have a LaTeX distribution installed on your system:

### Windows
- Install MiKTeX: https://miktex.org/download
- Or install TeX Live: https://www.tug.org/texlive/

### macOS
- Install MacTeX: https://www.tug.org/mactex/

### Linux
- Install TeX Live through your package manager:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install texlive-full
  
  # CentOS/RHEL/Fedora
  sudo yum install texlive-scheme-full
  ```

## Required LaTeX Packages

The report uses the following packages which should be automatically installed by your LaTeX distribution:
- inputenc
- geometry
- graphicx
- amsmath
- amssymb
- fancyhdr
- titlesec
- tocloft
- xcolor
- hyperref
- float
- booktabs
- array
- multirow
- caption
- subcaption
- tikz
- pgfplots
- algorithm
- algpseudocode
- forest
- smartdiagram
- adjustbox

## Compilation Instructions

### Method 1: Using pdflatex (Command Line)

1. Open a terminal/command prompt
2. Navigate to the project directory:
   ```bash
   cd "C:\Users\Sanjay\Desktop\Lead Mate full Application"
   ```

3. Compile the report:
   ```bash
   pdflatex LeadMate_Project_Report.tex
   ```

4. Run bibliography (if needed):
   ```bash
   bibtex LeadMate_Project_Report.aux
   ```

5. Run pdflatex twice more to resolve references:
   ```bash
   pdflatex LeadMate_Project_Report.tex
   pdflatex LeadMate_Project_Report.tex
   ```

### Method 2: Using LaTeX Workshop in VS Code

1. Install LaTeX Workshop extension in VS Code
2. Open the .tex file in VS Code
3. Use Ctrl+Alt+B (or Cmd+Alt+B on macOS) to build the document

### Method 3: Using TeXstudio

1. Open TeXstudio
2. Open the .tex file
3. Click on "Build & View" button (green arrow)

## Troubleshooting

### Common Issues

1. **Missing packages**: If you get errors about missing packages, your LaTeX distribution should automatically install them. If not, manually install the missing packages.

2. **Font issues**: The document uses standard LaTeX fonts. If you encounter font issues, ensure your LaTeX distribution is up to date.

3. **Image missing**: The report references `woxsen_logo.png` which is not included in the project. You can either:
   - Add the logo file to the project directory
   - Comment out the \includegraphics line in the title page
   - Replace with a placeholder image

### Fixing Image Issue

To fix the missing image issue, you can either:

1. Download the Woxsen University logo and save it as `woxsen_logo.png` in the project directory

2. Or modify the title page in the .tex file to remove the image:
   ```latex
   % Comment out or remove this line:
   % \includegraphics[width=0.3\textwidth]{woxsen_logo.png} \\
   ```

## Output

After successful compilation, you will get:
- `LeadMate_Project_Report.pdf` - The final report
- Auxiliary files (`.aux`, `.log`, `.toc`, etc.) which can be safely deleted

## Report Structure

The report contains the following sections:
1. Abstract
2. Table of Contents
3. List of Figures
4. List of Tables
5. Main Chapters (7 chapters)
6. Bibliography

Total: Approximately 35 pages with diagrams and visualizations.

## Customization

You can customize the report by:
1. Adding your actual roll number in the title page
2. Adding your guide's name and designation
3. Including actual performance metrics and test results
4. Adding any additional diagrams or screenshots from your project

## Key Features of This Version

This version of the report focuses on:
1. **Architecture diagrams** - Multiple TikZ diagrams showing system architecture
2. **Workflow visualizations** - Flowcharts for each agent's workflow
3. **Technology stack visualization** - Clear representation of the tech stack
4. **Performance charts** - Visual representation of system metrics
5. **Comparison tables** - Clear comparison with traditional tools
6. **Minimal code snippets** - Focus on concepts rather than implementation details

The report is designed to be visually appealing while maintaining academic rigor, with a focus on diagrams and explanations rather than code.