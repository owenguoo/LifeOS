'use client';

import { useAuth } from "../contexts/AuthContext";
import AuthScreen from "../components/AuthScreen";
import AnimatedSearchBar from "../components/AnimatedSearchBar";
import Widget from "../components/Widget";
import BottomNav from "../components/BottomNav";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";

export default function Home() {
  const { isAuthenticated, login, token, loading, axiosInstance } = useAuth();
  const [systemStarting, setSystemStarting] = useState(false);
  const [systemStatus, setSystemStatus] = useState<'stopped' | 'starting' | 'running' | 'error'>('stopped');
  const [currentActivityIndex, setCurrentActivityIndex] = useState(0);

  // TODO: Add an API route to get the daily activities
  const activities = [
    "pitched your project.",
    "reunited with Owen.", 
    "won at Hack the 6ix.",
    "talked to recruiters.",
  ];

  // Cycle through activities every 4 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentActivityIndex((prevIndex) => (prevIndex + 1) % activities.length);
    }, 4000);

    return () => clearInterval(interval);
  }, [activities.length]);

  // Start video system when user is authenticated
  useEffect(() => {
    const startVideoSystem = async () => {
      if (isAuthenticated && token && systemStatus === 'stopped' && !systemStarting) {
        setSystemStarting(true);
        setSystemStatus('starting');
        
        try {
          console.log('Starting video ingestion system...');
          const response = await axiosInstance.post('/api/v1/system/start');
          console.log('Video system started:', response.data);
          setSystemStatus('running');
        } catch (error) {
          console.error('Failed to start video system:', error);
          setSystemStatus('error');
        } finally {
          setSystemStarting(false);
        }
      }
    };

    startVideoSystem();
  }, [isAuthenticated, token, systemStatus, systemStarting, axiosInstance]);

  // Cleanup: Stop video system when component unmounts or user logs out
  useEffect(() => {
    const handleBeforeUnload = async () => {
      if (isAuthenticated && systemStatus === 'running') {
        try {
          await axiosInstance.post('/api/v1/system/end');
          console.log('Video system ended on page unload');
        } catch (error) {
          console.error('Failed to end video system:', error);
        }
      }
    };

    // Add event listener for page unload
    window.addEventListener('beforeunload', handleBeforeUnload);

    // Cleanup function (when component unmounts)
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      
      // Also try to end system when component unmounts
      if (isAuthenticated && systemStatus === 'running') {
        axiosInstance.post('/api/v1/system/end').catch(console.error);
      }
    };
  }, [isAuthenticated, systemStatus, axiosInstance]);

  const handleAuthSuccess = (token: string) => {
    login(token);
  };

  // Show loading state while checking authentication or starting system
  if (loading || systemStarting) {
    const statusMessage = loading 
      ? "Initializing LifeOS..." 
      : systemStarting 
        ? "Starting video capture system..." 
        : "Initializing LifeOS...";

    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <motion.div 
          className="text-center space-y-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="text-2xl font-semibold text-text-primary mb-4">{statusMessage}</div>
          <div className="loader mx-auto mb-4"></div>
          {systemStatus === 'error' && (
            <div className="text-red-500 text-sm mt-2">
              Failed to start video system. Please check console for details.
            </div>
          )}
        </motion.div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthScreen onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <div className="min-h-screen flex flex-col">
      <motion.header 
        className="fixed top-20 md:top-12 left-0 right-0 z-20"
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
      >
        <div className="container mx-auto px-4 py-4">
          <div className="flex flex-col items-center text-center gap-8">
            <motion.h1 
              className="text-6xl font-semibold text-text-primary glow-light"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 1, delay: 0.4, type: "spring", stiffness: 100 }}
            >
              LifeOS
            </motion.h1>
            <motion.div 
              className="text-xl text-text-secondary flex items-center justify-center gap-1"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.8 }}
            >
              <span className="pr-0.5">Today you</span>
              <div className="relative w-48 h-8">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={currentActivityIndex}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 1 }}
                    className="absolute inset-0 flex items-center justify-start"
                  >
                    {activities[currentActivityIndex]}
                  </motion.div>
                </AnimatePresence>
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-text-secondary pr-8"></div>
              </div>
            </motion.div>
          </div>
        </div>
      </motion.header>

      <main className="flex-1 pt-20 pb-20 px-4 flex flex-col justify-center">
        <div className="container mx-auto max-w-md mx-auto px-16 space-y-12">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 1.0 }}
          >
            <AnimatedSearchBar placeholder="Search memories" />
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 1.2 }}
          >
            <Widget />
          </motion.div>
        </div>
      </main>

      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 1.4 }}
      >
        <BottomNav />
      </motion.div>
    </div>
  );
}
