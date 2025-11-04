# Converting Mermaid Diagrams to Images

## Overview

This document provides instructions for converting the Mermaid diagrams in the updated LeadMate report to images that can be used in presentations or other documents.

## Prerequisites

Before converting the diagrams, ensure you have one of the following tools installed:

### Option 1: Mermaid CLI (Recommended)

1. **Node.js** (version 14 or higher)
2. **npm** (comes with Node.js)

Install Mermaid CLI globally:
```bash
npm install -g @mermaid-js/mermaid-cli
```

### Option 2: Online Editors

- Mermaid Live Editor: https://mermaid.live
- GitLab Mermaid Editor: https://mermaid-gitlab.com/

### Option 3: VS Code Extension

- Install the "Mermaid Preview" extension in Visual Studio Code

## Method 1: Using Mermaid CLI

### Converting Individual Diagrams

1. Extract a single diagram from the Markdown file or appendix
2. Save it as a `.mmd` file
3. Convert to PNG:
   ```bash
   mmdc -i diagram.mmd -o diagram.png
   ```
4. Convert to SVG:
   ```bash
   mmdc -i diagram.mmd -o diagram.svg
   ```

### Batch Conversion

Create a script to convert all diagrams:

```bash
#!/bin/bash
# Convert all .mmd files in the current directory to PNG
for file in *.mmd; do
  mmdc -i "$file" -o "${file%.mmd}.png"
done
```

## Method 2: Using VS Code

1. Open the Markdown file in VS Code
2. Install the "Mermaid Preview" extension
3. Open the Command Palette (Ctrl+Shift+P or Cmd+Shift+P)
4. Run "Mermaid: Export Current Diagram"
5. Choose the export format (PNG, SVG, or PDF)

## Method 3: Online Editors

1. Go to https://mermaid.live
2. Copy and paste the Mermaid code for a diagram
3. Click "Preview" to see the diagram
4. Click "Download" to save as PNG or SVG

## Diagram Files

The updated Mermaid diagrams are available in two formats:

### 1. Markdown Format
File: `LeadMate_Updated_Mermaid_Flowcharts.md`

Contains all diagrams in a single Markdown file with proper formatting.

### 2. LaTeX Appendix
File: `APPENDIX_Updated_Mermaid_Code_Sanjay.tex`

Contains the same diagrams in LaTeX format with proper escaping for LaTeX compilation.

## Recommended Image Sizes

For use in presentations and documents, consider these image sizes:

- **High-Level Architecture**: 1200x800 pixels (PNG) or A4 (PDF)
- **Multi-Agent System**: 1400x900 pixels (PNG) or A4 (PDF)
- **Workflow Diagrams**: 1000x600 pixels (PNG) or A5 (PDF)
- **Integration Diagrams**: 1200x700 pixels (PNG) or A4 (PDF)

## Image Optimization

### For Web Use
```bash
# Optimize PNG for web
pngquant --quality=65-80 diagram.png -o diagram-optimized.png
```

### For Print
Export as SVG or high-resolution PNG (300 DPI) for better print quality.

## Using Images in Presentations

### PowerPoint
1. Save diagrams as PNG files
2. Insert → Pictures → This Device
3. Select the PNG files

### Google Slides
1. Save diagrams as PNG files
2. File → Insert → Image → Upload from computer

### LaTeX Beamer
```latex
\begin{frame}
  \frametitle{System Architecture}
  \includegraphics[width=\textwidth]{diagram.png}
\end{frame}
```

## Best Practices

1. **Consistent Styling**: Use the same theme and colors across all diagrams
2. **Appropriate Resolution**: Use high enough resolution for the intended use (screen vs. print)
3. **File Format**: 
   - PNG for presentations and web
   - SVG for scalable graphics and print
   - PDF for vector graphics in LaTeX documents
4. **Naming Convention**: Use descriptive names like `architecture-overview.png`, `agent-workflow.svg`

## Troubleshooting

### Common Issues

1. **Font Rendering**: If fonts look different in exported images, specify fonts explicitly in Mermaid:
   ```mermaid
   %%{init: {'theme': 'default', 'fontFamily': 'Arial'}}%%
   graph TB
   ```

2. **Large Diagrams**: For very large diagrams, consider breaking them into smaller components or using zoomable SVGs.

3. **Export Quality**: For high-quality prints, export as SVG and convert to PDF if needed:
   ```bash
   inkscape diagram.svg --export-pdf=diagram.pdf
   ```

## Example Conversion Script

Here's a complete example for converting all diagrams:

```bash
#!/bin/bash

# Create output directory
mkdir -p diagrams

# Extract and convert each diagram from the Markdown file
# (This is a simplified example - you'd need to parse the Markdown properly)

# Example for one diagram:
echo 'graph TB
    A[User Interface] --> B[API Layer]
    B --> C[AI Agents]
    C --> D[Database]' > diagrams/architecture.mmd

# Convert to PNG
mmdc -i diagrams/architecture.mmd -o diagrams/architecture.png -w 1200 -H 800

# Convert to SVG
mmdc -i diagrams/architecture.mmd -o diagrams/architecture.svg

echo "Conversion complete. Check the diagrams folder."
```

By following these instructions, you can easily convert the Mermaid diagrams to high-quality images for use in presentations, documentation, and other materials.