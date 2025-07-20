'use client';

import { motion } from 'motion/react';
import { WidgetProps } from './types';

export default function SummaryWidget({ 
  onCardClick, 
  isFlipped = false, 
  dailySummary, 
  loading = false, 
  error = null 
}: WidgetProps) {
  
  const renderSummaryContent = () => {
    if (loading) {
      return (
        <motion.div 
          className="text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="text-lg font-medium text-text-primary mb-2">Loading...</div>
          <div className="text-sm text-text-secondary">Fetching today&apos;s summary</div>
        </motion.div>
      );
    }

    if (error) {
      return (
        <motion.div 
          className="text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="text-lg font-medium text-text-primary mb-2">Error</div>
          <div className="text-sm text-text-secondary">Unable to load summary</div>
        </motion.div>
      );
    }

    if (!dailySummary) {
      return (
        <motion.div 
          className="text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="text-lg font-medium text-text-primary mb-2">No Data</div>
          <div className="text-sm text-text-secondary">No summary available</div>
        </motion.div>
      );
    }

    // Parse the daily recap to extract key information
    const recapLines = dailySummary.daily_recap.split('\n');
    const eventCount = dailySummary.events_count;
    
    // Extract timeline events (lines that contain time)
    const timelineEvents = recapLines
      .filter(line => /\d{1,2}:\d{2}\s[AP]M/.test(line))
      .slice(0, 3); // Show first 3 events

    return (
      <motion.div 
        className="text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div className="text-lg font-medium text-text-primary mb-2">Today&apos;s Summary</div>
        <div className="text-sm text-text-secondary space-y-1">
          <div>• {eventCount} events recorded</div>
          {timelineEvents.length > 0 && (
            <>
              <div className="text-xs text-text-secondary/70 mt-2">Recent:</div>
              {timelineEvents.map((event, index) => (
                <motion.div 
                  key={index} 
                  className="text-xs text-text-secondary/80"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  {event.split(': ')[1]?.substring(0, 30)}...
                </motion.div>
              ))}
            </>
          )}
        </div>
      </motion.div>
    );
  };

  return (
    <motion.div 
      className="relative w-full py-8 space-y-2 cursor-pointer"
      key="summary-widget"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      transition={{ duration: 0.4, type: "spring", stiffness: 200 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onCardClick}
    >
      <motion.div 
        className="relative w-full h-full"
        animate={{ rotateY: isFlipped ? 180 : 0 }}
        transition={{ duration: 0.6, type: "spring", stiffness: 200 }}
        style={{ transformStyle: 'preserve-3d' }}
      >
        {/* Front of card */}
        <motion.div 
          className="absolute inset-0 flex items-center justify-center"
          style={{ backfaceVisibility: 'hidden' }}
          animate={{ opacity: isFlipped ? 0 : 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="text-center">
            <motion.div 
              className="text-3xl text-text-primary mb-2"
              whileHover={{ scale: 1.05 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              Revisit today?
            </motion.div>
            <div className="text-sm text-text-secondary">Tap to see summary</div>
          </div>
        </motion.div>
        
        {/* Back of card */}
        <motion.div 
          className="absolute inset-0 flex items-center justify-center"
          style={{ 
            backfaceVisibility: 'hidden',
            transform: 'rotateY(180deg)'
          }}
          animate={{ opacity: isFlipped ? 1 : 0 }}
          transition={{ duration: 0.3 }}
        >
          {renderSummaryContent()}
        </motion.div>
      </motion.div>
    </motion.div>
  );
} 