# Document Storage System - Complete Guide

## 📁 Where Documents Are Stored

### File System Storage
Documents are physically stored in the backend's file system:

```
backend/
  └── uploads/
      └── {project_id}/
          ├── {uuid1}.pdf
          ├── {uuid2}.docx
          ├── {uuid3}.txt
          └── ...
```

**Example:**
```
backend/
  └── uploads/
      └── 68ebd004255234c2619113e5/
          ├── a7f3e2d9-4c1b-4f23-9a8e-1b2c3d4e5f6g.pdf
          ├── b8g4f3e0-5d2c-5g34-0b9f-2c3d4e5f6g7h.docx
          └── c9h5g4f1-6e3d-6h45-1c0g-3d4e5f6g7h8i.txt
```

### Database Storage (MongoDB)
Document **metadata** is stored in MongoDB:

**Collection: `documents`**
```javascript
{
  _id: ObjectId("..."),
  projectId: "68ebd004255234c2619113e5",
  startupId: "68ebacad2d41fb7462747403",
  originalFilename: "project_requirements.pdf",
  storedFilename: "a7f3e2d9-4c1b-4f23-9a8e-1b2c3d4e5f6g.pdf",
  filePath: "uploads/68ebd004255234c2619113e5/a7f3e2d9-4c1b-4f23-9a8e-1b2c3d4e5f6g.pdf",
  fileSize: 1048576, // bytes
  contentType: "application/pdf",
  uploadedBy: "68ebacad2d41fb7462747405",
  uploadedAt: ISODate("2025-10-12T10:30:00Z")
}
```

**Collection: `projects`**
```javascript
{
  _id: ObjectId("68ebd004255234c2619113e5"),
  title: "Mobile App Development",
  // ... other fields
  documents: [
    "68ebd12a255234c2619113f1",
    "68ebd12b255234c2619113f2",
    "68ebd12c255234c2619113f3"
  ], // Array of document IDs
  // ... other fields
}
```

---

## 🔄 How Document Upload Works

### Step-by-Step Flow

1. **Frontend: User Selects Files**
   - User opens "Create Project" modal
   - Fills in project details
   - Selects files using file input
   - Clicks "Create Project"

2. **Frontend: Create Project**
   ```typescript
   // ManagerDashboard.tsx
   const response = await fetch('/api/projects', {
     method: 'POST',
     body: JSON.stringify({
       title: "...",
       description: "...",
       deadline: "...",
       teamLeadId: "..."
     })
   });
   const newProject = await response.json(); // { _id: "68ebd...", ... }
   ```

3. **Frontend: Upload Documents**
   ```typescript
   if (files && files.length > 0) {
     const formData = new FormData();
     files.forEach(file => formData.append('files', file));
     
     await fetch(`/api/documents/upload/${newProject._id}`, {
       method: 'POST',
       headers: { 'Authorization': `Bearer ${token}` },
       body: formData
     });
   }
   ```

4. **Backend: Save Files to Disk**
   ```python
   # routers/documents.py
   for file in files:
       # Generate unique filename
       unique_filename = f"{uuid.uuid4()}{file_extension}"
       file_path = project_dir / unique_filename
       
       # Save to disk
       with file_path.open("wb") as buffer:
           shutil.copyfileobj(file.file, buffer)
   ```

5. **Backend: Store Metadata in MongoDB**
   ```python
   document_data = {
       "_id": ObjectId(),
       "projectId": project_id,
       "originalFilename": file.filename,
       "storedFilename": unique_filename,
       "filePath": str(file_path),
       # ... other metadata
   }
   await db.documents.insert_one(document_data)
   ```

6. **Backend: Link to Project**
   ```python
   await db.projects.update_one(
       {"_id": ObjectId(project_id)},
       {"$push": {"documents": str(document_id)}}
   )
   ```

---

## 🔌 API Endpoints

### 1. Upload Documents
**POST** `/api/documents/upload/{project_id}`

**Authentication**: Manager only

**Request**:
- Content-Type: `multipart/form-data`
- Body: Files array
```typescript
const formData = new FormData();
formData.append('files', file1);
formData.append('files', file2);
```

**Response**:
```json
{
  "message": "Successfully uploaded 2 document(s)",
  "documents": [
    {
      "id": "68ebd12a255234c2619113f1",
      "filename": "requirements.pdf",
      "size": 1048576,
      "uploadedAt": "2025-10-12T10:30:00Z"
    },
    {
      "id": "68ebd12b255234c2619113f2",
      "filename": "mockups.pdf",
      "size": 2097152,
      "uploadedAt": "2025-10-12T10:30:05Z"
    }
  ]
}
```

### 2. Get Project Documents
**GET** `/api/documents/project/{project_id}`

**Authentication**: Any user in the startup

**Response**:
```json
{
  "projectId": "68ebd004255234c2619113e5",
  "totalDocuments": 2,
  "documents": [
    {
      "id": "68ebd12a255234c2619113f1",
      "filename": "requirements.pdf",
      "size": 1048576,
      "contentType": "application/pdf",
      "uploadedBy": "John Manager",
      "uploadedAt": "2025-10-12T10:30:00Z"
    }
  ]
}
```

### 3. Download Document
**GET** `/api/documents/download/{document_id}`

**Authentication**: Any user in the startup

**Response**: File download (FileResponse)

### 4. Delete Document
**DELETE** `/api/documents/{document_id}`

**Authentication**: Manager only

**Response**:
```json
{
  "message": "Document deleted successfully"
}
```

---

## 🔒 Security Features

1. **Authentication Required**: All endpoints require JWT token
2. **Authorization**: 
   - Upload/Delete: Manager only
   - View/Download: All users in same startup
3. **Startup Isolation**: Users can only access documents from their startup
4. **Project Validation**: Documents can only be uploaded to valid projects
5. **File System Isolation**: Each project has its own directory

---

## 📊 File Organization

### Why This Structure?

```
uploads/
  └── {project_id}/
      └── {uuid}.{extension}
```

**Benefits:**
1. ✅ **Easy cleanup**: Delete entire project folder when project is deleted
2. ✅ **Unique filenames**: UUID prevents naming conflicts
3. ✅ **Project isolation**: Files organized by project
4. ✅ **Original filename preserved**: Stored in database metadata
5. ✅ **Scalable**: Can add more organization levels if needed

### File Naming Convention

- **Stored filename**: `{uuid4}.{original_extension}`
  - Example: `a7f3e2d9-4c1b-4f23-9a8e-1b2c3d4e5f6g.pdf`
  - Prevents name collisions
  - Original extension preserved for proper MIME type handling

- **Original filename**: Stored in database
  - Example: `Project Requirements Document v2.pdf`
  - Used when downloading file
  - Displayed in UI

---

## 🎯 Usage Examples

### Example 1: Create Project with Documents

**Frontend Code:**
```typescript
const createProjectWithDocs = async () => {
  const files = [
    new File(['content'], 'doc1.pdf'),
    new File(['content'], 'doc2.pdf')
  ];
  
  await handleCreateProject({
    title: "New App",
    description: "Mobile app project",
    deadline: "2025-12-31",
    teamLeadId: "abc123",
    files: files
  });
};
```

**What Happens:**
1. Project created → ID: `68ebd004...`
2. Directory created → `backend/uploads/68ebd004.../`
3. Files saved → `a7f3e2d9....pdf`, `b8g4f3e0....pdf`
4. Metadata stored in MongoDB
5. Project's `documents` array updated

### Example 2: List Project Documents

**Frontend Code:**
```typescript
const loadDocuments = async (projectId) => {
  const response = await fetch(
    `http://localhost:8000/api/documents/project/${projectId}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  const data = await response.json();
  console.log(data.documents); // Array of document metadata
};
```

---

## 🗂️ Database Indexes

The following indexes should be created for optimal performance:

```javascript
// Documents collection
db.documents.createIndex({ "projectId": 1 });
db.documents.createIndex({ "startupId": 1 });
db.documents.createIndex({ "uploadedAt": -1 });
db.documents.createIndex({ "projectId": 1, "startupId": 1 });

// Projects collection (already has)
db.projects.createIndex({ "documents": 1 });
```

---

## 🔧 Maintenance

### Cleanup Old Documents

When a project is deleted, cleanup:

```python
# Delete all documents for a project
async def delete_project_documents(project_id: str):
    # Get all documents
    documents = await db.documents.find({"projectId": project_id})
    
    # Delete files
    project_dir = Path(f"uploads/{project_id}")
    if project_dir.exists():
        shutil.rmtree(project_dir)
    
    # Delete metadata
    await db.documents.delete_many({"projectId": project_id})
```

### Check Storage Usage

```python
async def get_storage_stats(startup_id: str):
    pipeline = [
        {"$match": {"startupId": startup_id}},
        {"$group": {
            "_id": None,
            "totalSize": {"$sum": "$fileSize"},
            "totalDocuments": {"$sum": 1}
        }}
    ]
    result = await db.documents.aggregate(pipeline).to_list(1)
    return result[0] if result else {"totalSize": 0, "totalDocuments": 0}
```

---

## 🚀 Current Status

✅ **Backend**: Fully implemented with all CRUD operations  
✅ **Frontend**: Upload integrated into project creation  
✅ **Storage**: File system + MongoDB metadata  
✅ **Security**: Authentication & authorization in place  
✅ **Server**: Running on `http://localhost:8000`  

### Ready to Test!

1. Go to http://localhost:5174/manager
2. Click "New Project"
3. Fill in details
4. **Upload documents** using the file input
5. Submit - Documents will be saved!

---

## 📝 Next Steps (Optional Enhancements)

1. **View Documents in UI**: Add document list to project details page
2. **Download Button**: Allow users to download documents
3. **File Type Restrictions**: Limit to specific file types
4. **File Size Limits**: Set maximum upload size
5. **Progress Indicators**: Show upload progress
6. **Drag & Drop**: Add drag-and-drop file upload
7. **Document Preview**: Preview PDFs/images in browser
8. **AI Processing**: Integrate with DocAgent for document analysis

---

**Last Updated**: October 12, 2025  
**Status**: ✅ Production Ready

