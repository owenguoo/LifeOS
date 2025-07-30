'use client';

import { useState } from 'react';
import { motion } from 'motion/react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import BottomNav from '../../components/BottomNav';
import CustomToggle from '../../components/CustomToggle';

interface Automation {
  id: string;
  name: string;
  enabled: boolean;
}

export default function SettingsPage() {
  const router = useRouter();
  const [automations, setAutomations] = useState<Automation[]>([
    {
      id: 'highlights',
      name: 'Highlights',
      enabled: true,
    },
    {
      id: 'daily-summarizer',
      name: 'Daily Summarizer',
      enabled: false,
    },
    {
      id: 'google-calendar',
      name: 'Google Calendar',
      enabled: true,
    },
  ]);

  const toggleAutomation = (id: string) => {
    setAutomations(prev => 
      prev.map(automation => 
        automation.id === id 
          ? { ...automation, enabled: !automation.enabled }
          : automation
      )
    );
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
      },
    },
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <motion.header 
        className="py-3 mt-6 mx-auto w-[280px] z-20 glass-effect border-b border-border"
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <div className="container mx-auto px-3 py-3">
          <div className="flex items-center justify-between">
            <motion.button
              onClick={() => router.push('/')}
              className="flex items-center text-text-secondary hover:text-text-primary transition-colors"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
            >
              <Image src="/home.svg" alt="Home" width={24} height={24} className="w-6 h-6" />
            </motion.button>
            <motion.h1 
              className="text-2xl font-semibold text-text-primary mx-auto"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              Automations
            </motion.h1>
            <motion.div 
              className="w-6 h-6"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
            />
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="flex-1 pt-6 pb-40 px-3">
        <div className="container mx-auto max-w-3xl">
          <motion.div
            className="space-y-4"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {automations.map((automation) => (
              <motion.div
                key={automation.id}
                className="glass-effect rounded-lg p-3 border border-border hover:border-primary/30"
                variants={itemVariants}
                whileHover={{ scale: 1.02, y: -2 }}
                whileTap={{ scale: 0.98 }}
                transition={{ duration: 0.2, ease: "easeOut" }}
              >
                <div className="flex items-center justify-between gap-2">
                  {/* Icon */}
                  <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center">
                    {automation.id === 'highlights' && (
                      <svg className="w-5 h-5 text-text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                      </svg>
                    )}
                    {automation.id === 'daily-summarizer' && (
                      <svg className="w-5 h-5 text-text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    )}
                    {automation.id === 'google-calendar' && (
                      <Image src="/google_calendar.svg" alt="Google Calendar" width={20} height={20} className="w-5 h-5" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-semibold text-text-primary mb-1">
                      {automation.name}
                    </h3>
                  </div>
                  
                  {/* Toggle Switch */}
                  <div className="flex-shrink-0">
                    <CustomToggle
                      id={`toggle-${automation.id}`}
                      checked={automation.enabled}
                      onChange={(checked) => toggleAutomation(automation.id)}
                    />
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="mt-8 cursor-pointer"
          >
            <motion.button
               onClick={() => window.open('https://github.com/owenguoo/LifeOS', '_blank')}
               className="w-full glass-effect rounded-lg p-3 border border-border hover:border-primary/30 flex items-center justify-center gap-3 group"
               whileHover={{ scale: 1.02, y: -2 }}
               whileTap={{ scale: 0.98 }}
               transition={{ duration: 0.1 }}
             >
               <svg className="w-5 h-5 text-text-accent group-hover:rotate-90 transition-transform duration-150" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              <span className="text-base font-semibold text-text-primary">Add an automation</span>
            </motion.button>
          </motion.div>
        </div>
      </main>

      <BottomNav />
    </div>
  );
} 