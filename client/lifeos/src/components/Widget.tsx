'use client';

import { useState, useRef } from 'react';

export default function Widget() {
    const [currentWidget, setCurrentWidget] = useState(0);
    const [touchStart, setTouchStart] = useState(0);
    const [touchEnd, setTouchEnd] = useState(0);
    const [isFlipped, setIsFlipped] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    const date = new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric' });

    // Minimum swipe distance (in px)
    const minSwipeDistance = 50;

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
                return (
                    <div className="text-center space-y-2">
                        <div className="text-3xl font-mono text-text-primary">{time}</div>
                        <div className="text-xl text-text-secondary">{date}</div>
                    </div>
                );
            case 1:
                return (
                    <div 
                        className="relative w-full py-8 space-y-2 cursor-pointer transition-transform duration-500"
                        style={{
                            transformStyle: 'preserve-3d',
                            transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)'
                        }}
                        onClick={handleCardClick}
                    >
                        {/* Front of card */}
                        <div 
                            className={`absolute inset-0 flex items-center justify-center transition-opacity duration-300 ${
                                isFlipped ? 'opacity-0' : 'opacity-100'
                            }`}
                            style={{ backfaceVisibility: 'hidden' }}
                        >
                            <div className="text-center">
                                <div className="text-3xl text-text-primary mb-2">Revisit today?</div>
                                <div className="text-sm text-text-secondary">Tap to see summary</div>
                            </div>
                        </div>
                        
                        {/* Back of card */}
                        <div 
                            className={`absolute inset-0 flex items-center justify-center transition-opacity duration-300 ${
                                isFlipped ? 'opacity-100' : 'opacity-0'
                            }`}
                            style={{ 
                                backfaceVisibility: 'hidden',
                                transform: 'rotateY(180deg)'
                            }}
                        >
                            <div className="text-center">
                                <div className="text-lg font-medium text-text-primary mb-2">Today's Summary</div>
                                <div className="text-sm text-text-secondary">
                                    <div>• 3 tasks completed</div>
                                    <div>• 2 meetings attended</div>
                                    <div>• 1 new contact added</div>
                                </div>
                            </div>
                        </div>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div className="flex flex-col items-center justify-center max-w-[301px] mx-auto">
            {/* Widget Container */}
            <div 
                ref={containerRef}
                className="glass-effect py-8 w-full"
                onTouchStart={onTouchStart}
                onTouchMove={onTouchMove}
                onTouchEnd={onTouchEnd}
            >
                {renderWidgetContent()}
            </div>
            
            {/* Dots Indicator */}
            <div className="flex space-x-2 mt-4">
                {[0, 1, 2].map((index) => (
                    <div
                        key={index}
                        className={`w-2 h-2 rounded-full transition-all duration-300 ${
                            index === currentWidget 
                                ? 'bg-text-primary' 
                                : 'bg-text-secondary/30'
                        }`}
                    />
                ))}
            </div>
        </div>
    );
}