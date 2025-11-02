# 📄 AI Document Extraction Feature

## Overview
Automatic document content extraction using Ollama LLM. When documents are uploaded, the system extracts text from PDFs, Word docs, and text files, then uses AI to structure and present the content. Team leads can see all document content directly in their project cards - numbered and separated for easy reading.

---

## 🎯 Features Implemented

### AI-Powered Processing
1. **Automatic Text Extraction** - Extracts text from PDF, DOCX, TXT files
2. **LLM Processing** - Uses Ollama (llama3.2:3b) to structure content
3. **No Summarization** - Shows complete document content as-is
4. **Multi-Document Support** - Each document numbered (#1, #2, #3...)
5. **Real-Time Processing** - Extracts during upload
6. **Error Handling** - Graceful fallback if extraction fails

### For Team Leads
1. **View Full Content** - See complete document text in project modal
2. **Numbered Documents** - Easy identification (#1, #2, etc.)
3. **Scrollable Content** - Large documents in scrollable containers
4. **Download Option** - Still can download original files
5. **Visual Indicators** - File type icons and metadata

---

## 📁 Files Created

### Backend Services
- `backend/services/ollama_service.py` - LLM integration service
- `backend/services/document_extractor.py` - Document text extraction
- `backend/services/__init__.py` - Services package init

### Backend Modified
- `backend/routers/documents.py` - Added extraction on upload

### Frontend Modified
- `frontend/src/components/ProjectDetailModal.tsx` - Display extracted content

---

## 🤖 Technology Stack

### LLM Integration
**Model Used:** `llama3.2:3b` (fastest, smallest)
- **Why llama3.2:3b?** 
  - Only 2.0 GB (smallest model)
  - Fast processing
  - Good for content extraction
  - Available in your Ollama

**Alternative Models Available:**
- `llama2:latest` (3.8 GB)
- `mistral:7b` (4.4 GB)
- `llama3.1:8b` (4.9 GB)

### Document Processing Libraries
- **PyPDF2** - PDF text extraction
- **python-docx** - Word document extraction
- **Python built-ins** - Text file handling

---

## 🔄 How It Works

### Upload Flow

```
1. Manager uploads document (PDF/DOCX/TXT)
   ↓
2. File saved to disk
   ↓
3. DocumentExtractor extracts raw text
   ↓
4. OllamaService processes with LLM
   ↓
5. Extracted content stored in MongoDB
   ↓
6. Team lead views project → sees content
```

### Extraction Process

**Step 1: File Type Detection**
```python
# Detects file type from content_type and extension
if 'pdf' in content_type or extension == '.pdf':
    extract_from_pdf()
elif 'word' in content_type or extension in ['.docx', '.doc']:
    extract_from_docx()
elif 'text' in content_type or extension in ['.txt', '.md']:
    extract_from_text()
```

**Step 2: Text Extraction**
```python
# PDF: Extracts page by page
for page_num in range(total_pages):
    text = page.extract_text()
    content.append(f"--- Page {page_num + 1} ---\n{text}")

# DOCX: Extracts paragraphs and tables
for para in doc.paragraphs:
    content.append(para.text)
```

**Step 3: LLM Processing**
```python
prompt = f"""Extract and present content EXACTLY as it appears.
DO NOT summarize. Preserve all details, numbers, dates.

Document: {filename}
Content: {text}

Extracted Content:"""

response = ollama.chat(model='llama3.2:3b', messages=[...])
```

**Step 4: Storage**
```javascript
document_data = {
    // ... other fields ...
    "extractedContent": extracted_content  // AI-processed content
}
```

---

## 💻 Backend Implementation

### Ollama Service

```python
class OllamaService:
    def __init__(self, model="llama3.2:3b"):
        self.model = model
        self.client = ollama
    
    def extract_document_content(self, text, filename):
        # Prompt instructs LLM to preserve all content
        prompt = """Extract content EXACTLY as it appears...
        DO NOT summarize..."""
        
        response = self.client.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}]
        )
        
        return response['message']['content']
```

### Document Extractor

```python
class DocumentExtractor:
    @staticmethod
    def extract_from_pdf(file_path):
        pdf_reader = PyPDF2.PdfReader(file_path)
        text_content = []
        for page in pdf_reader.pages:
            text_content.append(page.extract_text())
        return "\n\n".join(text_content)
    
    @staticmethod
    def extract_from_docx(file_path):
        doc = docx.Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs]
        return "\n\n".join(paragraphs)
```

### Upload Integration

```python
# In documents upload endpoint
# After saving file to disk:

extracted_text = document_extractor.extract_text(
    file_path, 
    file.content_type
)

if extracted_text:
    extracted_content = ollama_service.extract_document_content(
        extracted_text, 
        file.filename
    )

document_data["extractedContent"] = extracted_content
```

---

## 🎨 Frontend Display

### Document Card with Content

```typescript
// Each document numbered and with extracted content

{documents.map((doc, index) => (
  <div key={doc.id} className="rounded-xl border">
    {/* Header with #1, #2, etc. */}
    <div className="p-4 bg-gray-50">
      <span className="font-bold text-blue-600">#{index + 1}</span>
      <h4>{doc.filename}</h4>
    </div>
    
    {/* Extracted Content */}
    {doc.extractedContent && (
      <div className="p-4 border-t">
        <h5>Document Content:</h5>
        <div className="whitespace-pre-wrap max-h-96 overflow-y-auto">
          {doc.extractedContent}
        </div>
      </div>
    )}
  </div>
))}
```

### UI Features
- **Numbered (#1, #2, #3)** - Easy reference
- **Scrollable** - Max height with overflow
- **Pre-wrapped** - Preserves formatting
- **File Icons** - Visual file type indicators
- **Metadata** - Size, upload date, uploader
- **Download Button** - Original file download

---

## 🧪 Testing Guide

### Test 1: Upload PDF Document

```bash
1. Login as Manager (vastav@woxsen.edu.in)
2. Click on a project card (edit mode)
3. Upload a PDF file (e.g., requirements.pdf)
4. Watch backend logs:
   - "Extracting text from requirements.pdf..."
   - "Processing content with Ollama LLM..."
   - "Successfully processed requirements.pdf"
5. Close modal, save changes
```

### Test 2: View as Team Lead

```bash
1. Login as Team Lead (Nikunj@woxsen.edu.in)
2. Go to dashboard
3. Click on the project card
4. Modal opens showing:
   ✓ Document #1: requirements.pdf
   ✓ Full extracted content below
   ✓ Scrollable if long
   ✓ Download button available
```

### Test 3: Multiple Documents

```bash
1. Upload 3 documents:
   - requirements.pdf
   - architecture.docx
   - notes.txt
2. Team lead views project
3. Sees:
   - #1: requirements.pdf (with content)
   - #2: architecture.docx (with content)
   - #3: notes.txt (with content)
4. Each document separately numbered and displayed
```

### Test 4: Large Document

```bash
1. Upload 10-page PDF document
2. System extracts all pages
3. LLM processes entire content
4. Team lead views:
   - Content in scrollable container
   - Max height with overflow-y-auto
   - All pages visible with scrolling
```

---

## 🔧 Configuration

### Change LLM Model

Edit `backend/services/ollama_service.py`:

```python
# Default (fastest)
def __init__(self, model: str = "llama3.2:3b"):

# For better quality (slower)
def __init__(self, model: str = "llama3.1:8b"):

# For different approach
def __init__(self, model: str = "mistral:7b"):
```

### Supported File Types

**Currently Supported:**
- ✅ PDF (`.pdf`)
- ✅ Word Documents (`.docx`, `.doc`)
- ✅ Plain Text (`.txt`, `.md`, `.log`)

**Easy to Add:**
- Excel (`.xlsx`) - use `openpyxl`
- PowerPoint (`.pptx`) - use `python-pptx`
- Images (`.jpg`, `.png`) - use OCR

---

## 📊 Database Schema Update

### Documents Collection

```javascript
{
  _id: ObjectId,
  projectId: String,
  startupId: String,
  originalFilename: String,
  storedFilename: String,
  filePath: String,
  fileSize: Number,
  contentType: String,
  uploadedBy: String,
  uploadedAt: DateTime,
  extractedContent: String  // NEW: AI-extracted content
}
```

---

## 🎯 Key Features

| Feature | Description | Status |
|---------|-------------|--------|
| PDF Extraction | Extract text from PDF files | ✅ Done |
| DOCX Extraction | Extract from Word documents | ✅ Done |
| TXT Extraction | Extract from text files | ✅ Done |
| LLM Processing | Structure content with AI | ✅ Done |
| No Summarization | Show complete content | ✅ Done |
| Document Numbering | #1, #2, #3 labeling | ✅ Done |
| Scrollable Display | Long documents scrollable | ✅ Done |
| Error Handling | Graceful failures | ✅ Done |
| Dark Mode | Consistent theming | ✅ Done |
| Original Download | Keep original files | ✅ Done |

---

## 🚀 Performance

### Processing Times (Estimated)

| File Type | Size | Extraction | LLM | Total |
|-----------|------|------------|-----|-------|
| PDF | 1 MB (10 pages) | ~1s | ~3-5s | ~4-6s |
| DOCX | 500 KB | ~0.5s | ~2-4s | ~2.5-4.5s |
| TXT | 100 KB | <0.1s | ~1-2s | ~1-2s |

**Note:** Using llama3.2:3b for speed. Larger models slower but more accurate.

---

## 🔐 Security & Privacy

### Data Storage
- Original files: `backend/uploads/{project_id}/`
- Extracted content: MongoDB database
- Access: Restricted to project team and manager

### LLM Processing
- **Local Processing:** Ollama runs locally
- **No External APIs:** No data sent to cloud
- **Privacy:** All processing on your machine
- **Offline:** Works without internet

---

## 💡 Future Enhancements

Potential improvements:
1. **OCR for Images** - Extract text from scanned documents
2. **Table Extraction** - Better table formatting
3. **Code Highlighting** - Syntax highlighting for code files
4. **Search in Content** - Full-text search across documents
5. **Content Summarization** - Optional AI summaries
6. **Key Points Extraction** - Highlight important info
7. **Question Answering** - Ask questions about documents
8. **Multi-language Support** - Translate extracted content
9. **Version Tracking** - Track document changes
10. **Collaborative Annotations** - Add notes to content

---

## 🐛 Troubleshooting

### Issue: "No text extracted"

**Cause:** File format not supported or corrupted
**Solution:** 
- Check file is valid PDF/DOCX/TXT
- Try re-saving the file
- Check backend logs for errors

### Issue: "Ollama connection error"

**Cause:** Ollama not running
**Solution:**
```bash
# Start Ollama service
ollama serve

# Verify model is available
ollama list

# Pull model if needed
ollama pull llama3.2:3b
```

### Issue: "Extraction timeout"

**Cause:** Large document or slow LLM
**Solution:**
- Use smaller/faster model (llama3.2:3b)
- Split large documents
- Increase timeout in code

### Issue: "Content not displaying"

**Cause:** Frontend not receiving extracted content
**Solution:**
- Check browser console for errors
- Verify API returns `extractedContent` field
- Refresh frontend

---

## ✅ Success Criteria Met

✅ Extracts text from PDF, DOCX, TXT  
✅ Uses Ollama LLM for processing  
✅ Shows complete content (no summary)  
✅ Documents are numbered (#1, #2, #3)  
✅ Multiple documents separated  
✅ Scrollable for long content  
✅ Team leads can view in project cards  
✅ Original download still available  
✅ Dark mode supported  
✅ Error handling in place  
✅ Local LLM (no cloud APIs)  
✅ Fast processing with llama3.2:3b  

---

## 📝 Usage Example

### Manager Workflow

```
1. Create/Edit Project
2. Upload "Project Requirements.pdf"
3. System automatically:
   - Extracts text from PDF
   - Processes with Ollama
   - Stores extracted content
4. Save project
```

### Team Lead Workflow

```
1. View Dashboard
2. Click project card
3. See document:
   ┌─────────────────────────────────────┐
   │ #1 📄 Project Requirements.pdf      │
   │ 2.5 MB • Uploaded Jan 15 • Vastav  │
   ├─────────────────────────────────────┤
   │ Document Content:                   │
   │                                     │
   │ Project Requirements                │
   │ ====================                │
   │                                     │
   │ 1. User Authentication              │
   │    - Login with email/password      │
   │    - JWT token based auth           │
   │                                     │
   │ 2. Dashboard                        │
   │    - View all projects              │
   │    - Statistics cards               │
   │                                     │
   │ [Scroll for more...]                │
   └─────────────────────────────────────┘
4. Read full content
5. Download original if needed
```

---

## 🎉 Benefits

### For Managers
- Upload once, team sees content immediately
- No need to explain document contents
- AI extracts key information
- Team stays informed

### For Team Leads
- Quick document overview
- No need to download to read
- All content in one place
- Easy reference with numbering

### For the Team
- Centralized information
- AI-powered extraction
- Always up-to-date
- Accessible anywhere

---

**The Document Extraction feature is now fully functional! 🎉**

Upload any PDF, Word doc, or text file and the AI will automatically extract and display the complete content for team leads to view directly in their project cards.


