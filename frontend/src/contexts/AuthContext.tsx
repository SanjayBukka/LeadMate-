import React, { createContext, useContext, useState, ReactNode } from 'react';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'manager' | 'teamlead';
  initials: string;
  startupId: string; // Add startupId to User interface
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<User | null>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Backend API URL
const API_BASE_URL = 'http://localhost:8000';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = async (email: string, password: string): Promise<User | null> => {
    try {
      console.log('Attempting login with:', { email });
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      console.log('Login response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Login successful, token received');
        
        // Store token
        const token = data.access_token;
        localStorage.setItem('authToken', token);
        
        // Fetch user data using the token
        const userResponse = await fetch(`${API_BASE_URL}/api/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (userResponse.ok) {
          const userData = await userResponse.json();
          console.log('User data fetched:', userData);
          
          // Transform to match expected format
          const user: User = {
            id: userData._id,
            name: userData.name,
            email: userData.email,
            role: userData.role,
            initials: userData.initials,
            startupId: userData.startupId // Include startupId
          };
          
          setUser(user);
          return user;
        } else {
          console.error('Failed to fetch user data');
          return null;
        }
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.log('Login failed, error data:', errorData);
        return null;
      }
    } catch (error) {
      console.error('Login error:', error);
      return null;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('authToken');
  };

  const value = {
    user,
    login,
    logout,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}