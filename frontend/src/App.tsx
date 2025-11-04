import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ProtectedRoute } from './components/ProtectedRoute';

// Pages
import { Home } from './pages/Home';
import { Login } from './pages/Login';
import { ManagerDashboard } from './pages/Manager/ManagerDashboard';
import { TeamManagement } from './pages/Manager/TeamManagement';
import { Dashboard } from './pages/TeamLead/Dashboard';
import { TaskBoard } from './pages/TeamLead/TaskBoard';
import { TeamMembers } from './pages/TeamLead/TeamMembers';
import { AIAssistant } from './pages/TeamLead/AIAssistant';
import { Management } from './pages/TeamLead/Management';
import { AgentsHub } from './pages/TeamLead/AgentsHub';
import { DocAgent } from './pages/TeamLead/Agents/DocAgent';
import { AIAgents } from './pages/TeamLead/AIAgents';

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            
            {/* Manager Routes */}
            <Route
              path="/manager"
              element={
                <ProtectedRoute requiredRole="manager">
                  <ManagerDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/manager/team"
              element={
                <ProtectedRoute requiredRole="manager">
                  <TeamManagement />
                </ProtectedRoute>
              }
            />
            
            {/* Team Lead Routes */}
            <Route
              path="/lead/dashboard"
              element={
                <ProtectedRoute requiredRole="teamlead">
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/lead/taskboard"
              element={
                <ProtectedRoute requiredRole="teamlead">
                  <TaskBoard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/lead/members"
              element={
                <ProtectedRoute requiredRole="teamlead">
                  <TeamMembers />
                </ProtectedRoute>
              }
            />
            <Route
              path="/lead/agents"
              element={
                <ProtectedRoute requiredRole="teamlead">
                  <AIAgents />
                </ProtectedRoute>
              }
            />
            <Route
              path="/lead/agents/doc-agent"
              element={
                <ProtectedRoute requiredRole="teamlead">
                  <DocAgent />
                </ProtectedRoute>
              }
            />
            <Route
              path="/lead/agents/stack-agent"
              element={
                <ProtectedRoute requiredRole="teamlead">
                  <AIAssistant />
                </ProtectedRoute>
              }
            />
            <Route
              path="/lead/agents/team-agent"
              element={
                <ProtectedRoute requiredRole="teamlead">
                  <AIAssistant />
                </ProtectedRoute>
              }
            />
            <Route
              path="/lead/agents/code-clarity"
              element={
                <ProtectedRoute requiredRole="teamlead">
                  <AIAssistant />
                </ProtectedRoute>
              }
            />
            <Route
              path="/lead/management"
              element={
                <ProtectedRoute requiredRole="teamlead">
                  <Management />
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;