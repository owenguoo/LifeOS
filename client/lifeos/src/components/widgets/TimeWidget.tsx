'use client';

import { motion } from 'framer-motion';

interface TimeWidgetProps {
  widgetIndex: number;
}

export default function TimeWidget({ widgetIndex }: TimeWidgetProps) {
  const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  const date = new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric' });

  return (
    <motion.div 
      className="text-center space-y-2"
      key={`time-${widgetIndex}`}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      transition={{ duration: 0.4, type: "spring", stiffness: 200 }}
    >
      <motion.div 
        className="text-3xl font-mono text-text-primary"
        animate={{ scale: [1, 1.05, 1] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      >
        {time}
      </motion.div>
      <div className="text-xl text-text-secondary">{date}</div>
    </motion.div>
  );
} 