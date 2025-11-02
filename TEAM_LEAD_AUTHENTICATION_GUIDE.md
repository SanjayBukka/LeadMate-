# Team Lead Authentication & Access Guide

## 🔐 Complete Authentication Flow

### 1. **Manager Creates Team Lead Account**

**Location**: Manager Dashboard → "Manage Team" button

**What Manager Does:**
1. Clicks "Manage Team" button
2. Clicks "Add Team Lead"
3. Fills in form:
   - Name: `John Developer`
   - Email: `john@yourcompany.com`
   - Password: `securepass123`
4. Submits form

**What Happens in Backend:**
```python
# POST /api/auth/users/add-lead
{
  "name": "John Developer",
  "email": "john@yourcompany.com",
  "password": "securepass123",
  "role": "teamlead",
  "startupId": "68ebacad..."  # Automatically set from manager's startup
}
```

**Database Storage:**
```javascript
// users collection
{
  _id: ObjectId("..."),
  name: "John Developer",
  email: "john@yourcompany.com",
  hashedPassword: "$2b$12$...",  // Bcrypt hashed
  role: "teamlead",
  startupId: "68ebacad...",
  initials: "JD",
  isActive: true,
  createdBy: "68ebacad...",  // Manager's ID
  createdAt: ISODate("2025-10-12...")
}
```

---

### 2. **Team Lead Logs In**

**Location**: http://localhost:5174/login

**What Team Lead Does:**
1. Enters email: `john@yourcompany.com`
2. Enters password: `securepass123`
3. Clicks "Sign In"

**What Happens:**

**Step 1**: Login Request
```javascript
// POST /api/auth/login
// Uses OAuth2 password flow (username = email)
{
  username: "john@yourcompany.com",
  password: "securepass123"
}
```

**Step 2**: Backend Validates
```python
# backend/routers/auth.py
# 1. Find user by email
user = await db.users.find_one({"email": "john@yourcompany.com"})

# 2. Verify password
if not verify_password("securepass123", user["hashedPassword"]):
    return 401 Unauthorized

# 3. Check if active
if not user["isActive"]:
    return 400 Bad Request

# 4. Create JWT token
token = create_access_token({
    "sub": user["email"],
    "user_id": str(user["_id"]),
    "startup_id": user["startupId"],
    "role": user["role"]
})

# 5. Update last login
await db.users.update_one({"_id": user["_id"]}, {"$set": {"lastLogin": now}})

# 6. Return token
return {"access_token": token, "token_type": "bearer"}
```

**Step 3**: Frontend Stores Token
```javascript
// AuthContext.tsx
localStorage.setItem('authToken', token);
```

**Step 4**: Frontend Fetches User Data
```javascript
// GET /api/auth/me
// Headers: { Authorization: Bearer {token} }
const userData = await fetch('/api/auth/me');
// Returns: { _id, name, email, role, initials, ... }
```

**Step 5**: Frontend Redirects Based on Role
```javascript
// Login.tsx
if (user.role === "manager") {
    navigate("/manager");
} else if (user.role === "teamlead") {
    navigate("/lead/dashboard");  // ← Team Lead goes here!
}
```

---

### 3. **Team Lead Accesses Dashboard**

**URL**: http://localhost:5174/lead/dashboard

**What Team Lead Sees:**
- ✅ **Only projects assigned to them** (filtered by backend)
- Statistics:
  - Active Projects
  - Completed Projects  
  - Total Projects
  - Due This Week

**How Backend Filters Projects:**
```python
# backend/routers/projects.py
@router.get("/api/projects")
async def get_projects(current_user: User):
    if current_user.role == "manager":
        # Managers see ALL projects in their startup
        query = {"startupId": current_user.startupId}
    else:  # teamlead
        # Team leads see ONLY their assigned projects
        query = {
            "startupId": current_user.startupId,
            "teamLeadId": str(current_user.id)  # ← Filtered!
        }
    
    projects = await db.projects.find(query)
    return projects
```

---

## 🔑 JWT Token Structure

```javascript
// Encoded Token (what's stored)
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

// Decoded Payload
{
  "sub": "john@yourcompany.com",        // Email (subject)
  "user_id": "68ebacad2d41fb7462747405", // User ID
  "startup_id": "68ebacad2d41fb7462747403", // Startup ID
  "role": "teamlead",                    // Role
  "exp": 1728825600                      // Expiration (24 hours)
}
```

**Token Lifetime**: 24 hours (configurable in `config.py`)

---

## 🛡️ Protected Routes

### Frontend Protection
```typescript
// App.tsx
<Route
  path="/lead/dashboard"
  element={
    <ProtectedRoute requiredRole="teamlead">
      <Dashboard />
    </ProtectedRoute>
  }
/>
```

**What `ProtectedRoute` Does:**
1. Checks if user is logged in
2. Checks if user has correct role
3. Redirects to `/login` if not authenticated
4. Redirects to home if wrong role

### Backend Protection
```python
# routers/projects.py
@router.get("/api/projects")
async def get_projects(current_user: User = Depends(get_current_user)):
    # ↑ This dependency:
    # 1. Extracts JWT token from Authorization header
    # 2. Validates token signature
    # 3. Checks expiration
    # 4. Fetches user from database
    # 5. Returns user object or raises 401 Unauthorized
```

---

## 📱 Complete User Journey

### Scenario: Manager Assigns Project to Team Lead

**Step 1**: Manager creates team lead
```
Manager → Manage Team → Add Team Lead
Name: Sarah Johnson
Email: sarah@company.com
Password: sarah123
```

**Step 2**: Manager creates project and assigns to Sarah
```
Manager → New Project
Title: Mobile App Redesign
Description: ...
Deadline: 2025-12-31
Team Lead: Sarah Johnson  ← Selected from dropdown
```

**Step 3**: Sarah logs in
```
URL: http://localhost:5174/login
Email: sarah@company.com
Password: sarah123
→ Redirected to: /lead/dashboard
```

**Step 4**: Sarah sees her assigned project
```
Team Lead Dashboard
├── Statistics
│   ├── Active Projects: 1
│   ├── Completed: 0
│   ├── Total Projects: 1
│   └── Due This Week: 1
└── Active Projects
    └── Mobile App Redesign
        • Assigned to: Sarah Johnson
        • Progress: 0%
        • Deadline: Dec 31, 2025
```

---

## 🔄 Session Management

### Token Storage
```javascript
// Stored in browser localStorage
localStorage.getItem('authToken')
// Returns: "eyJhbGciOiJIUzI1NiIs..."
```

### Token Usage
Every API request includes token:
```javascript
fetch('/api/projects', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

### Logout
```javascript
// AuthContext.tsx
const logout = () => {
  localStorage.removeItem('authToken');
  setUser(null);
  navigate('/login');
};
```

### Token Expiration
- **Default**: 24 hours
- **What happens**: User gets 401 Unauthorized
- **User action**: Must log in again

---

## 🎯 Key Points

### For Managers:
- ✅ Create team lead accounts
- ✅ Assign projects to team leads
- ✅ View all projects in startup
- ✅ Add/remove team leads
- ✅ Activate/deactivate team leads

### For Team Leads:
- ✅ Login with provided credentials
- ✅ View ONLY assigned projects
- ✅ See project details
- ✅ Track progress
- ✅ Cannot see other team leads' projects

### Security:
- ✅ Passwords hashed with bcrypt
- ✅ JWT tokens for authentication
- ✅ Role-based access control
- ✅ Startup isolation (multi-tenancy)
- ✅ Protected routes (frontend + backend)

---

## 🧪 Testing the Flow

### 1. Create Team Lead
```
1. Login as manager
2. Go to /manager/team
3. Click "Add Team Lead"
4. Fill: Name=Test Lead, Email=test@company.com, Password=test123
5. Submit
```

### 2. Login as Team Lead
```
1. Logout (or open incognito window)
2. Go to /login
3. Enter: test@company.com / test123
4. Should redirect to /lead/dashboard
```

### 3. Verify Data Isolation
```
1. As manager, create 2 projects:
   - Project A → Assign to Test Lead
   - Project B → No team lead assigned
   
2. As Test Lead, login and check dashboard:
   - Should see: Project A only
   - Should NOT see: Project B
```

---

## 📊 Database Collections

### users
```javascript
{
  _id: ObjectId,
  name: String,
  email: String (unique),
  hashedPassword: String,
  role: "manager" | "teamlead",
  startupId: String (ObjectId),
  initials: String,
  isActive: Boolean,
  createdAt: DateTime,
  createdBy: String (ObjectId, optional)
}
```

### projects
```javascript
{
  _id: ObjectId,
  title: String,
  description: String,
  deadline: DateTime,
  status: String,
  teamLeadId: String (ObjectId, optional),  // ← Links to team lead
  startupId: String (ObjectId),
  managerId: String (ObjectId),
  progress: Number,
  documents: Array[String],
  createdAt: DateTime
}
```

---

**Status**: ✅ Fully Implemented and Working!

**Last Updated**: October 12, 2025

