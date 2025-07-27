'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import axios from 'axios';

interface AuthScreenProps {
  onAuthSuccess: (token: string) => void;
}

type AuthMode = 'welcome' | 'login' | 'register';

export default function AuthScreen({ onAuthSuccess }: AuthScreenProps) {
  const [authMode, setAuthMode] = useState<AuthMode>('welcome');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleGetStarted = () => {
    setAuthMode('login');
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${process.env.NEXT_PUBLIC_API_HOST}/api/v1/auth/login`, {
        username,
        password
      });

      const token = response.data.token || response.data.access_token;
      
      if (token) {
        setSuccess(true);
        setTimeout(() => {
          onAuthSuccess(token);
        }, 1000);
      } else {
        setError('No token received from server');
      }
    } catch (err: unknown) {
      const errorMessage = err && typeof err === 'object' && 'response' in err 
        ? ((err.response as { data?: { detail?: string } })?.data?.detail) || 'Login failed'
        : 'Login failed';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${process.env.NEXT_PUBLIC_API_HOST}/api/v1/auth/register`, {
        username,
        password
      });

      const token = response.data.token || response.data.access_token;
      
      if (token) {
        setSuccess(true);
        setTimeout(() => {
          onAuthSuccess(token);
        }, 1000);
      } else {
        setError('No token received from server');
      }
    } catch (err: unknown) {
      const errorMessage = err && typeof err === 'object' && 'response' in err 
        ? ((err.response as { data?: { detail?: string } })?.data?.detail) || 'Registration failed'
        : 'Registration failed';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const switchMode = (mode: 'login' | 'register') => {
    setAuthMode(mode);
    setError('');
    setUsername('');
    setPassword('');
  };

  const resetForm = () => {
    setUsername('');
    setPassword('');
    setError('');
    setLoading(false);
    setSuccess(false);
  };

  return (
    <div className="min-h-screen px-8 bg-background flex items-center justify-center">
      <AnimatePresence mode="wait">
        {authMode === 'welcome' ? (
          <motion.div
            key="welcome"
            initial={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -100 }}
            transition={{ duration: 0.5, ease: "easeInOut" }}
            className="text-center"
          >
            <motion.h1 
              className="text-8xl font-bold text-text-primary mb-12 glow-light"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            >
              LifeOS
            </motion.h1>
            <motion.button
              onClick={handleGetStarted}
              className="px-16 py-4 text-white rounded-lg text-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300 relative overflow-hidden"
              style={{
                background: `
                  radial-gradient(circle at 20% 80%, var(--bg-blur-secondary) 0%, transparent 70%),
                  radial-gradient(circle at 80% 20%, var(--bg-blur-accent) 0%, transparent 70%),
                  var(--bg-blur-primary)
                `,
              }}
              whileTap={{ scale: 0.95 }}
            >
              <span className="relative z-10">Get Started</span>
            </motion.button>
          </motion.div>
        ) : (
          <motion.div
            key="auth-form"
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, ease: "easeInOut" }}
            className="w-full max-w-md mx-4"
          >
            {success ? (
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="text-center"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                  className="w-16 h-16 bg-green-500 rounded-full mx-auto mb-4 flex items-center justify-center"
                >
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </motion.div>
                <h2 className="text-2xl font-bold text-text-primary mb-2">Success!</h2>
                <p className="text-text-secondary">Redirecting to LifeOS...</p>
              </motion.div>
            ) : (
              <>
                {/* Tab Navigation */}
                <motion.div
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.2 }}
                  className="flex bg-surface rounded-lg p-1 mb-8"
                >
                  <button
                    onClick={() => switchMode('login')}
                    className={`flex-1 py-3 px-4 rounded-md text-sm font-medium transition-all duration-200 ${
                      authMode === 'login'
                        ? 'bg-primary text-white shadow-sm'
                        : 'text-text-secondary hover:text-text-primary'
                    }`}
                  >
                    Sign In
                  </button>
                  <button
                    onClick={() => switchMode('register')}
                    className={`flex-1 py-3 px-4 rounded-md text-sm font-medium transition-all duration-200 ${
                      authMode === 'register'
                        ? 'bg-primary text-white shadow-sm'
                        : 'text-text-secondary hover:text-text-primary'
                    }`}
                  >
                    Sign Up
                  </button>
                </motion.div>

                {/* Form Header */}
                <motion.div
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.3 }}
                  className="text-center mb-8"
                >
                  <h2 className="text-3xl font-bold text-text-primary mb-2">
                    {authMode === 'login' ? 'Welcome Back' : 'Create Account'}
                  </h2>
                  <p className="text-text-secondary">
                    {authMode === 'login' 
                      ? 'Sign in to continue to LifeOS' 
                      : 'Join LifeOS to get started'
                    }
                  </p>
                </motion.div>

                {/* Auth Form */}
                <AnimatePresence mode="wait">
                  <motion.form
                    key={authMode}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                    onSubmit={authMode === 'login' ? handleLogin : handleRegister}
                    className="space-y-6"
                  >
                    <div>
                      <label htmlFor="username" className="block text-sm font-medium text-text-primary mb-2">
                        Username
                      </label>
                      <input
                        type="text"
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="w-full px-4 py-3 border border-border rounded-lg bg-background text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200"
                        placeholder="Enter your username"
                        required
                      />
                    </div>

                    <div>
                      <label htmlFor="password" className="block text-sm font-medium text-text-primary mb-2">
                        Password
                      </label>
                      <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full px-4 py-3 border border-border rounded-lg bg-background text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200"
                        placeholder="Enter your password"
                        required
                      />
                    </div>

                    {error && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-red-500 text-sm text-center bg-red-500/10 border border-red-500/20 rounded-lg p-3"
                      >
                        {error}
                      </motion.div>
                    )}

                    <motion.button
                      type="submit"
                      disabled={loading}
                      className="w-full px-6 py-3 text-white rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed relative overflow-hidden"
                      style={{
                        background: `
                          radial-gradient(circle at 20% 80%, var(--bg-blur-secondary) 0%, transparent 70%),
                          radial-gradient(circle at 80% 20%, var(--bg-blur-accent) 0%, transparent 70%),
                          var(--bg-blur-primary)
                        `,
                      }}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <span className="relative z-10">
                        {loading 
                          ? (authMode === 'login' ? 'Signing In...' : 'Creating Account...') 
                          : (authMode === 'login' ? 'Sign In' : 'Create Account')
                        }
                      </span>
                    </motion.button>
                  </motion.form>
                </AnimatePresence>

                {/* Back to Welcome */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.6 }}
                  className="text-center mt-6"
                >
                  <button
                    onClick={() => {
                      setAuthMode('welcome');
                      resetForm();
                    }}
                    className="text-text-secondary hover:text-text-primary text-sm transition-colors duration-200"
                  >
                    ← Back to Welcome
                  </button>
                </motion.div>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
} 