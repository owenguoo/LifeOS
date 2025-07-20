'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import { DailySummary } from './types';
import TimeWidget from './TimeWidget';
import SummaryWidget from './SummaryWidget';

export default function WidgetContainer() {
  const [currentWidget, setCurrentWidget] = useState(0);
  const [touchStart, setTouchStart] = useState(0);
  const [touchEnd, setTouchEnd] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [dailySummary, setDailySummary] = useState<DailySummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { axiosInstance } = useAuth();

  // Minimum swipe distance (in px)
  const minSwipeDistance = 50;

  const fetchDailySummary = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axiosInstance.get('/api/v1/insights/summary');
      setDailySummary(response.data);
    } catch (err) {
      setError('Failed to fetch daily summary');
      console.error('Error fetching daily summary:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDailySummary();
  }, [axiosInstance]);

  const onTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(0);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const onTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    if (isLeftSwipe) {
      setCurrentWidget((prev) => (prev + 1) % 3);
      setIsFlipped(false); // Reset flip state when changing widgets
    } else if (isRightSwipe) {
      setCurrentWidget((prev) => (prev - 1 + 3) % 3);
      setIsFlipped(false); // Reset flip state when changing widgets
    }
  };

  const handleCardClick = () => {
    if (currentWidget === 1) {
      setIsFlipped(!isFlipped);
    }
  };

  const renderWidgetContent = () => {
    switch (currentWidget) {
      case 0:
      case 2:
        return <TimeWidget widgetIndex={currentWidget} />;
      case 1:
        return (
          <SummaryWidget
            onCardClick={handleCardClick}
            isFlipped={isFlipped}
            dailySummary={dailySummary}
            loading={loading}
            error={error}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col items-center justify-center max-w-[301px] mx-auto">
      {/* Widget Container */}
      <motion.div 
        ref={containerRef}
        className="glass-effect py-8 w-full"
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
        whileHover={{ scale: 1.01 }}
        transition={{ type: "spring", stiffness: 100, damping: 20 }}
      >
        <AnimatePresence mode="wait">
          {renderWidgetContent()}
        </AnimatePresence>
      </motion.div>
      
      {/* Dots Indicator */}
      <div className="flex space-x-2 mt-4">
        {[0, 1, 2].map((index) => (
          <motion.div
            key={index}
            className={`w-2 h-2 rounded-full ${
              index === currentWidget 
                ? 'bg-text-primary' 
                : 'bg-text-secondary/30'
            }`}
            whileHover={{ scale: 1.2 }}
            whileTap={{ scale: 0.8 }}
            animate={{ 
              scale: index === currentWidget ? 1.2 : 1,
            }}
            transition={{ duration: 0.2, type: "spring", stiffness: 300 }}
            onClick={() => setCurrentWidget(index)}
            style={{ cursor: 'pointer' }}
          />
        ))}
      </div>
    </div>
  );
} 