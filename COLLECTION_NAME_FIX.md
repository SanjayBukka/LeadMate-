# ChromaDB Collection Name Fix

## Problem
When clicking "Analyze Doc" on a project, the following error occurred:

```
Error syncing documents: Expected collection name that (1) contains 3-63 characters, 
(2) starts and ends with an alphanumeric character, (3) otherwise contains only 
alphanumeric characters, underscores or hyphens (-), (4) contains no two consecutive 
periods (..) and (5) is not a valid IPv4 address, got 
startup_6908485a5d6f534d894af9d5_project_690849bf5d6f534d894af9d9_documents
```

**Root Cause:** The collection name was 79 characters long, exceeding ChromaDB's 63-character limit.

## Solution

Fixed collection name generation in two services:

### 1. `backend/services/vector_store_service.py`
- Updated `get_collection_name()` method to:
  - Sanitize IDs (remove invalid characters)
  - Enforce 63-character maximum length
  - Ensure names start/end with alphanumeric characters
  - Use hash-based approach for long IDs to maintain uniqueness while staying within limits

### 2. `backend/services/project_data_service.py`
- Updated `get_project_collection_name()` method:
  - Changed length check from 200 to 63 characters (ChromaDB limit)
  - Added proper sanitization and validation
  - Implemented hash-based fallback for long IDs

## How It Works

### For Short IDs:
If the full name `startup_{id}_project_{id}_{type}` fits within 63 characters, it uses the normal format.

### For Long IDs:
When IDs are too long, the system:
1. Generates an MD5 hash from: `{startup_id}_{project_id}_{collection_type}`
2. Creates a shortened name: `s_{hash1}_p_{hash2}_{type}` (where hash is split)
3. If still too long: `s_{hash}_{type_short}`
4. Final fallback: `col_{hash}_{type}` or `c{hash}`

This ensures:
- ✅ Names are always 3-63 characters
- ✅ Names start and end with alphanumeric characters
- ✅ Only contains alphanumeric, underscores, or hyphens
- ✅ No consecutive periods
- ✅ Uniqueness through hash-based naming

## Testing

To test the fix:
1. Restart your backend server
2. Try clicking "Analyze Doc" on a project
3. The collection should be created successfully without errors

## Example

**Before (79 chars - FAILED):**
```
startup_6908485a5d6f534d894af9d5_project_690849bf5d6f534d894af9d9_documents
```

**After (hash-based, ~30 chars - VALID):**
```
s_a1b2c3d4_p_e5f6g7h8_documents
```

## Files Modified

1. `backend/services/vector_store_service.py` - Line 23-109
2. `backend/services/project_data_service.py` - Line 45-70

## Next Steps

1. **Restart Backend Server:** The changes require a server restart to take effect
2. **Clear Old Collections (Optional):** If you have existing invalid collections, you may need to manually delete them from ChromaDB
3. **Test with Real Data:** Try analyzing documents on your project again

The fix ensures all future collection names will comply with ChromaDB's naming rules.

