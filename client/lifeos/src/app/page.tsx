'use client';

import { useAuth } from "../contexts/AuthContext";
import AuthScreen from "../components/AuthScreen";
import AnimatedSearchBar from "../components/AnimatedSearchBar";
import Widget from "../components/Widget";
import BottomNav from "../components/BottomNav";
import { useEffect } from "react";
import { motion } from "motion/react";

export default function Home() {
  const { isAuthenticated, login, token, loading } = useAuth();

  useEffect(() => {
  }, [isAuthenticated, token, loading]);

  const handleAuthSuccess = (token: string) => {
    login(token);
  };

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <motion.div 
          className="text-center space-y-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="text-2xl font-semibold text-text-primary mb-4">Initializing LifeOS...</div>
          <div className="loader mx-auto mb-4"></div>
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
              className="text-xl text-text-secondary"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.8 }}
            >
              Today you did 3 things.
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
