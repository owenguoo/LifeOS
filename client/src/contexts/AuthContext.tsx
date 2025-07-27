'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios, { AxiosInstance } from 'axios';
import config from '@/config';
import { API_ENDPOINTS } from '@/config';

interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  loading: boolean;
  login: (token: string) => void;
  logout: () => Promise<void>;
  axiosInstance: AxiosInstance;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Create axios instance with auth interceptor
  const axiosInstance: AxiosInstance = axios.create({
    baseURL: config.apiHost,
  });

  // Add auth token to requests
  axiosInstance.interceptors.request.use((config) => {
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  const login = (newToken: string) => {
    setToken(newToken);
    setIsAuthenticated(true);
    localStorage.setItem('auth_token', newToken);
  };

  const logout = async () => {
    // Try to end video system before logout
    if (token) {
      try {
        await axiosInstance.post(API_ENDPOINTS.SYSTEM.END);
        console.log('Video system ended on logout');
      } catch (error) {
        console.error('Failed to end video system on logout:', error);
      }
    }
    
    setToken(null);
    setIsAuthenticated(false);
    localStorage.removeItem('auth_token');
  };

  // Check for existing token on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token');
    if (savedToken) {
      setToken(savedToken);
      setIsAuthenticated(true);
    }
    setLoading(false);
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated, token, loading, login, logout, axiosInstance }}>
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