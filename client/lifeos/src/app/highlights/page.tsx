'use client';

import { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import BottomNav from '../../components/BottomNav';

interface Highlight {
  highlight_id: string;
  created_at: string;
  videos: {
    video_id: string;
    title?: string;
    s3_link: string; // Changed from s3_url to s3_link based on database schema
    thumbnail_url?: string;
    duration?: number;
    detailed_summary?: string;
  };
}

interface HighlightsResponse {
  highlights: Highlight[];
  total: number;
}

export default function HighlightsPage() {
  const { token } = useAuth();
  const router = useRouter();
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHighlights = async () => {
      try {
        setLoading(true);
        const response = await axios.get<HighlightsResponse>(
          'http://localhost:8000/api/v1/highlights/list',
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          }
        );
        console.log('Highlights response:', response.data);
        setHighlights(response.data.highlights);
      } catch (err) {
        console.error('Error fetching highlights:', err);
        setError('Failed to load highlights');
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchHighlights();
    }
  }, [token]);

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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <motion.div 
          className="text-center space-y-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="text-2xl font-semibold text-text-primary mb-4">Loading Highlights...</div>
          <div className="loader mx-auto mb-4"></div>
        </motion.div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <motion.div 
          className="text-center space-y-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="text-xl text-red-500 mb-4">{error}</div>
          <button 
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/80 transition-colors"
          >
            Try Again
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <motion.header 
        className="fixed py-4 top-12 left-12 right-12 z-20 glass-effect border-b border-border"
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <motion.button
              onClick={() => router.push('/')}
              className="flex items-center text-text-secondary hover:text-text-primary transition-colors"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
            >
              <img src="/home.svg" alt="Home" className="w-6 h-6" />
            </motion.button>
            <motion.h1 
              className="text-2xl font-semibold text-text-primary"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              Highlights
            </motion.h1>
            <motion.div 
              className="text-sm text-text-secondary"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
            >
              {highlights.length} videos
            </motion.div>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="flex-1 pt-40 pb-20 px-4">
        <div className="container mx-auto max-w-4xl">
          {highlights.length === 0 ? (
            <motion.div 
              className="text-center py-20"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <div className="text-xl text-text-secondary mb-4">No highlights yet</div>
              <div className="text-sm text-text-tertiary">
                Your video highlights will appear here
              </div>
            </motion.div>
          ) : (
            <motion.div
              className="grid grid-cols-3 gap-2"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              {highlights.map((highlight) => (
                <motion.div
                  key={highlight.highlight_id}
                  className="aspect-square relative group cursor-pointer overflow-hidden rounded-lg"
                  variants={itemVariants}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <video
                    src={highlight.videos.s3_link}
                    className="w-full h-full object-cover"
                    poster={highlight.videos.thumbnail_url}
                    preload="metadata"
                    muted
                    onError={(e) => {
                      console.error('Video failed to load:', highlight.videos.s3_link);
                      // You could show a fallback image or message here
                    }}
                    onMouseEnter={(e) => {
                      const video = e.currentTarget as HTMLVideoElement;
                      video.play().catch(() => {
                        // Ignore autoplay errors
                      });
                    }}
                    onMouseLeave={(e) => {
                      const video = e.currentTarget as HTMLVideoElement;
                      video.pause();
                      video.currentTime = 0;
                    }}
                  />
                  
                  {/* Overlay with video info */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <div className="absolute bottom-2 left-2 right-2">
                      <div className="text-white text-xs font-medium truncate">
                        {highlight.videos.title || highlight.videos.detailed_summary?.substring(0, 30) || 'Untitled'}
                      </div>
                      {highlight.videos.duration && (
                        <div className="text-white/80 text-xs">
                          {Math.floor(highlight.videos.duration / 60)}:{(highlight.videos.duration % 60).toString().padStart(2, '0')}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Play button overlay */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center">
                      <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z"/>
                      </svg>
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}
        </div>
      </main>

      <BottomNav />
    </div>
  );
} 