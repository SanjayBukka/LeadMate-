# 🔔 Notification System Implementation Guide

## Overview
A real-time notification system has been implemented for the LeadMate application. Team leads now receive notifications when they are assigned to projects.

---

## 🎯 Features Implemented

### Backend Features
1. **Notification Model** - Complete MongoDB schema for storing notifications
2. **Notification API Endpoints** - RESTful API for managing notifications
3. **Auto-Notification Generation** - Notifications automatically created when projects are assigned
4. **Database Indexing** - Optimized queries for fast notification retrieval

### Frontend Features
1. **NotificationDropdown Component** - Interactive notification bell with dropdown
2. **Real-time Unread Count** - Badge showing number of unread notifications
3. **Mark as Read** - Individual or bulk mark notifications as read
4. **Delete Notifications** - Remove individual notifications
5. **Auto-refresh** - Notification count updates every 30 seconds
6. **Beautiful UI** - Dark mode support, smooth animations, and responsive design

---

## 📁 Files Created/Modified

### Backend Files Created
- `backend/models/notification.py` - Notification Pydantic models
- `backend/routers/notifications.py` - Notification API endpoints

### Backend Files Modified
- `backend/models/__init__.py` - Added notification exports
- `backend/database.py` - Added notification collection indexes
- `backend/main.py` - Included notifications router
- `backend/routers/projects.py` - Added notification creation on project assignment

### Frontend Files Created
- `frontend/src/components/NotificationDropdown.tsx` - Main notification UI component

### Frontend Files Modified
- `frontend/src/components/Navbar.tsx` - Integrated NotificationDropdown

---

## 🔌 API Endpoints

### GET `/api/notifications`
Get all notifications for the current user.

**Query Parameters:**
- `unread_only` (optional): If `true`, returns only unread notifications

**Response:**
```json
[
  {
    "_id": "string",
    "type": "project_assigned",
    "title": "New Project Assigned",
    "message": "You have been assigned to project: Project Name",
    "relatedId": "project_id",
    "isRead": false,
    "createdAt": "2025-01-01T00:00:00.000Z"
  }
]
```

### GET `/api/notifications/count`
Get count of unread notifications.

**Response:**
```json
{
  "count": 3
}
```

### PUT `/api/notifications/{notification_id}/read`
Mark a specific notification as read.

**Response:**
```json
{
  "_id": "string",
  "isRead": true,
  ...
}
```

### PUT `/api/notifications/mark-all-read`
Mark all notifications as read for the current user.

**Response:**
```json
{
  "modified_count": 5
}
```

### DELETE `/api/notifications/{notification_id}`
Delete a specific notification.

**Response:** `204 No Content`

---

## 🗄️ Database Schema

### Notifications Collection

```javascript
{
  _id: ObjectId,
  userId: String,              // Team lead who receives notification
  startupId: String,           // Company ID
  type: String,                // "project_assigned" | "project_updated" | etc.
  title: String,               // Notification title
  message: String,             // Notification message
  relatedId: String,           // Related project/document ID (optional)
  isRead: Boolean,             // Read status
  createdAt: DateTime          // Timestamp
}
```

### Indexes Created
- `userId` - Fast lookup by user
- `startupId` - Filter by company
- `userId + isRead` - Efficient unread queries
- `userId + createdAt (desc)` - Sorted chronological retrieval

---

## 🎨 UI Components

### NotificationDropdown Component

**Location:** `frontend/src/components/NotificationDropdown.tsx`

**Features:**
- 🔔 Bell icon with badge showing unread count
- 📋 Dropdown panel with notification list
- ✅ Mark individual or all notifications as read
- 🗑️ Delete individual notifications
- ⏰ Relative timestamps ("2h ago", "Just now")
- 🎨 Emoji icons based on notification type
- 🌓 Full dark mode support
- 📱 Responsive design
- 🔄 Auto-refresh every 30 seconds
- 🖱️ Click outside to close

**Notification Types & Icons:**
- `project_assigned` → 📋
- `project_updated` → 🔄
- `project_completed` → ✅
- `team_added` → 👥

---

## 🔄 How It Works

### When a Project is Assigned

1. **Manager creates a project** via `/api/projects` POST endpoint
2. **Backend creates notification** if `teamLeadId` is provided:
   ```python
   notification = NotificationInDB(
       userId=teamLeadId,
       startupId=startupId,
       type="project_assigned",
       title="New Project Assigned",
       message=f"You have been assigned to project: {title}",
       relatedId=project_id,
       isRead=False
   )
   ```
3. **Notification stored** in MongoDB `notifications` collection
4. **Team lead sees notification** immediately:
   - Badge appears on bell icon
   - Dropdown shows new notification
   - Notification marked as unread (blue indicator)

### When Team Lead Opens Notifications

1. **Click bell icon** → Opens dropdown
2. **Fetches notifications** from `/api/notifications`
3. **Displays list** with newest first
4. **Unread notifications** have blue background and dot indicator
5. **Click ✅ button** → Marks as read
6. **Click 🗑️ button** → Deletes notification

---

## 🧪 Testing the System

### Test Scenario

1. **Login as Manager (Vastav)**
   - Email: `vastav@woxsen.edu.in`
   - Navigate to Manager Dashboard

2. **Create a New Project**
   - Click "+ New Project" button
   - Fill in project details
   - Assign to Nikunj (team lead)
   - Submit

3. **Login as Team Lead (Nikunj)**
   - Email: `Nikunj@woxsen.edu.in`
   - Password: `123Nikunj`
   - Navigate to `http://localhost:5173/lead/dashboard`

4. **Check Notifications**
   - See red badge on bell icon (e.g., "1")
   - Click bell icon
   - See notification: "New Project Assigned"
   - Message: "You have been assigned to project: [Project Name]"

5. **Interact with Notification**
   - Click ✅ to mark as read → Badge count decreases
   - Click 🗑️ to delete → Notification removed

---

## 🎯 Current Users

| Name   | Email                      | Role      | Password   |
|--------|----------------------------|-----------|------------|
| Vastav | vastav@woxsen.edu.in       | Manager   | (set)      |
| Nikunj | Nikunj@woxsen.edu.in       | Team Lead | 123Nikunj  |
| Sanjay | sanjay@woxsen.edu.in       | Team Lead | (set)      |

---

## 🚀 Future Enhancements

Potential features to add:
1. **Push Notifications** - Browser notifications when app is in background
2. **Email Notifications** - Send email for important notifications
3. **Notification Preferences** - Let users choose which notifications to receive
4. **Notification Sounds** - Audio alert for new notifications
5. **Project Updates** - Notify on project progress changes
6. **Comments/Mentions** - Notify when mentioned in comments
7. **Deadline Reminders** - Notify when project deadline is approaching
8. **WebSocket Integration** - Real-time notifications without refresh

---

## 📝 Key Implementation Details

### Auto-refresh Strategy
```typescript
// Fetch unread count every 30 seconds
useEffect(() => {
  fetchUnreadCount();
  const interval = setInterval(fetchUnreadCount, 30000);
  return () => clearInterval(interval);
}, [token]);
```

### Notification Creation Hook
```python
# In backend/routers/projects.py -> create_project()
if project_data.teamLeadId:
    notification = NotificationInDB(
        userId=project_data.teamLeadId,
        startupId=current_user.startupId,
        type="project_assigned",
        title="New Project Assigned",
        message=f"You have been assigned to project: {project_data.title}",
        relatedId=str(result.inserted_id),
        isRead=False
    )
    await db.notifications.insert_one(notification.model_dump(by_alias=True, exclude=['id']))
```

### Click Outside to Close
```typescript
useEffect(() => {
  function handleClickOutside(event: MouseEvent) {
    if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
      setIsOpen(false);
    }
  }
  if (isOpen) {
    document.addEventListener('mousedown', handleClickOutside);
  }
  return () => {
    document.removeEventListener('mousedown', handleClickOutside);
  };
}, [isOpen]);
```

---

## ✅ Completed Features

- [x] Notification model and MongoDB schema
- [x] Notification API endpoints (get, count, mark read, delete)
- [x] Auto-notification on project assignment
- [x] NotificationDropdown UI component
- [x] Unread count badge
- [x] Mark as read functionality
- [x] Delete notification functionality
- [x] Mark all as read
- [x] Auto-refresh every 30 seconds
- [x] Dark mode support
- [x] Responsive design
- [x] Click outside to close
- [x] Relative timestamps
- [x] Emoji icons by type

---

## 🎉 Success!

The notification system is now fully functional! Team leads will receive real-time notifications when they are assigned to projects, making collaboration and project management much more efficient.

**Test it now:**
1. Start backend: `cd backend && python main.py`
2. Start frontend: `cd frontend && npm run dev`
3. Login as Nikunj at `http://localhost:5173/lead/dashboard`
4. Look for the bell icon with notification badge! 🔔

