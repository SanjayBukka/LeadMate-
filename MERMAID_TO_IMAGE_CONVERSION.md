# Converting Mermaid Diagrams to Images for LeadMate Report

## Overview

This document provides instructions on how to convert the updated Mermaid diagrams to images that can be used in your LaTeX report.

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

### Step 1: Extract Individual Diagrams

From the `LeadMate_Updated_Mermaid_Flowcharts.md` file, extract each diagram and save it as a separate `.mmd` file:

1. HIGH-LEVEL_SYSTEM_ARCHITECTURE_WITH_CODECLARITY_AGENT.mmd
2. MULTI-AGENT_SYSTEM_ARCHITECTURE_WITH_CODECLARITY_AGENT.mmd
3. PROJECT-CENTRIC_DATA_FLOW_WITH_CODECLARITY_INTEGRATION.mmd
4. AGENT_INTERACTION_WORKFLOW_WITH_CODECLARITY.mmd
5. USER_INTERACTION_FLOW_WITH_CODECLARITY.mmd
6. COMPREHENSIVE_SYSTEM_ARCHITECTURE_USER_PERSPECTIVE_WITH_CODECLARITY.mmd
7. TECHNICAL_DATA_FLOW_ARCHITECTURE_WITH_CODECLARITY.mmd
8. DOCUMENT_AGENT_WORKFLOW.mmd
9. STACK_AGENT_WORKFLOW.mmd
10. TEAM_FORMATION_ALGORITHM_WORKFLOW.mmd
11. TASK_GENERATION_PROCESS.mmd
12. CODECLARITY_AGENT_WORKFLOW.mmd
13. CODECLARITY_AGENT_INTEGRATION_WITH_OTHER_AGENTS.mmd
14. PERFORMANCE_VISUALIZATION.mmd
15. FUTURE_ARCHITECTURE_EVOLUTION_WITH_CODECLARITY.mmd
16. SYSTEM_LIMITATIONS_WITH_CODECLARITY.mmd
17. COMPARISON_WITH_TRADITIONAL_TOOLS_INCLUDING_CODECLARITY.mmd

### Step 2: Convert to Images

Convert each diagram to PNG format:
```bash
mmdc -i HIGH-LEVEL_SYSTEM_ARCHITECTURE_WITH_CODECLARITY_AGENT.mmd -o HIGH-LEVEL_SYSTEM_ARCHITECTURE_WITH_CODECLARITY_AGENT.png
mmdc -i MULTI-AGENT_SYSTEM_ARCHITECTURE_WITH_CODECLARITY_AGENT.mmd -o MULTI-AGENT_SYSTEM_ARCHITECTURE_WITH_CODECLARITY_AGENT.png
mmdc -i PROJECT-CENTRIC_DATA_FLOW_WITH_CODECLARITY_INTEGRATION.mmd -o PROJECT-CENTRIC_DATA_FLOW_WITH_CODECLARITY_INTEGRATION.png
mmdc -i AGENT_INTERACTION_WORKFLOW_WITH_CODECLARITY.mmd -o AGENT_INTERACTION_WORKFLOW_WITH_CODECLARITY.png
mmdc -i CODECLARITY_AGENT_WORKFLOW.mmd -o CODECLARITY_AGENT_WORKFLOW.png
mmdc -i CODECLARITY_AGENT_INTEGRATION_WITH_OTHER_AGENTS.mmd -o CODECLARITY_AGENT_INTEGRATION_WITH_OTHER_AGENTS.png
mmdc -i FUTURE_ARCHITECTURE_EVOLUTION_WITH_CODECLARITY.mmd -o FUTURE_ARCHITECTURE_EVOLUTION_WITH_CODECLARITY.png
```

### Step 3: Image Optimization

For better quality in your report, consider these settings:
```bash
mmdc -i diagram.mmd -o diagram.png -w 1200 -H 800 --backgroundColor white
```

## Method 2: Using VS Code

1. Open the `LeadMate_Updated_Mermaid_Flowcharts.md` file in VS Code
2. Install the "Mermaid Preview" extension
3. Open the Command Palette (Ctrl+Shift+P or Cmd+Shift+P)
4. Run "Mermaid: Export Current Diagram"
5. Choose the export format (PNG, SVG, or PDF)
6. Save each diagram with the appropriate filename

## Method 3: Online Editors

1. Go to https://mermaid.live
2. Copy and paste each Mermaid code block from the Markdown file
3. Click "Preview" to see the diagram
4. Click "Download" to save as PNG or SVG
5. Save each diagram with the appropriate filename

## Recommended Image Sizes

For use in your LaTeX report, consider these image sizes:

- **Architecture Diagrams**: 1200x800 pixels (PNG) or A4 (PDF)
- **Workflow Diagrams**: 1000x600 pixels (PNG) or A5 (PDF)
- **Integration Diagrams**: 1200x700 pixels (PNG) or A4 (PDF)
- **Performance Visualization**: 800x600 pixels (PNG) or A5 (PDF)

## Image Naming Convention

Use the following naming convention for consistency:
- HIGH-LEVEL_SYSTEM_ARCHITECTURE_WITH_CODECLARITY_AGENT.png
- MULTI-AGENT_SYSTEM_ARCHITECTURE_WITH_CODECLARITY_AGENT.png
- PROJECT-CENTRIC_DATA_FLOW_WITH_CODECLARITY_INTEGRATION.png
- AGENT_INTERACTION_WORKFLOW_WITH_CODECLARITY.png
- CODECLARITY_AGENT_WORKFLOW.png
- CODECLARITY_AGENT_INTEGRATION_WITH_OTHER_AGENTS.png
- FUTURE_ARCHITECTURE_EVOLUTION_WITH_CODECLARITY.png

## Using Images in LaTeX

In your LaTeX document, reference the images as follows:

```latex
\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\textwidth]{HIGH-LEVEL_SYSTEM_ARCHITECTURE_WITH_CODECLARITY_AGENT.png}
    \caption{High-Level System Architecture with CodeClarity Agent}
    \label{fig:high-level-architecture-codeclarity}
\end{figure}
```

## Best Practices

1. **Consistent Styling**: Use the same theme and colors across all diagrams
2. **Appropriate Resolution**: Use high enough resolution for the intended use (screen vs. print)
3. **File Format**: 
   - PNG for presentations and web
   - SVG for scalable graphics and print
   - PDF for vector graphics in LaTeX documents
4. **Naming Convention**: Use descriptive names that match the diagram titles

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
mkdir -p images

# List of diagrams to convert
diagrams=(
    "HIGH-LEVEL_SYSTEM_ARCHITECTURE_WITH_CODECLARITY_AGENT"
    "MULTI-AGENT_SYSTEM_ARCHITECTURE_WITH_CODECLARITY_AGENT"
    "PROJECT-CENTRIC_DATA_FLOW_WITH_CODECLARITY_INTEGRATION"
    "AGENT_INTERACTION_WORKFLOW_WITH_CODECLARITY"
    "CODECLARITY_AGENT_WORKFLOW"
    "CODECLARITY_AGENT_INTEGRATION_WITH_OTHER_AGENTS"
    "FUTURE_ARCHITECTURE_EVOLUTION_WITH_CODECLARITY"
)

# Convert each diagram
for diagram in "${diagrams[@]}"; do
    echo "Converting $diagram..."
    mmdc -i "${diagram}.mmd" -o "images/${diagram}.png" -w 1200 -H 800 --backgroundColor white
done

echo "Conversion complete. Check the images folder."
```

By following these instructions, you can easily convert the Mermaid diagrams to high-quality images for use in your LaTeX report.