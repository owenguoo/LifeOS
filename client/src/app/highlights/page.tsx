'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import BottomNav from '../../components/BottomNav';

interface Highlight {
  highlight_id: string;
  created_at: string;
  videos: {
    video_id: string;
    title?: string;
    s3_link: string;
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
  const [selectedVideo, setSelectedVideo] = useState<Highlight | null>(null);
  const [captionExpanded, setCaptionExpanded] = useState(false);

  useEffect(() => {
    const fetchHighlights = async () => {
      try {
        setLoading(true);
        const response = await axios.get<HighlightsResponse>(
          `${process.env.NEXT_PUBLIC_API_HOST}/api/v1/highlights/list`,
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

  const handleVideoClick = (highlight: Highlight) => {
    setSelectedVideo(highlight);
  };

  const closeVideoModal = () => {
    setSelectedVideo(null);
    setCaptionExpanded(false);
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return 'Unknown time';
    }
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
        className="fixed py-4 top-12 left-0 right-0 mx-auto max-w-[301px] z-20 glass-effect border-b border-border"
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
              <Image src="/home.svg" alt="Home" width={24} height={24} className="w-6 h-6" />
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
                  onClick={() => handleVideoClick(highlight)}
                >
                  <video
                    src={`${highlight.videos.s3_link}#t=0.001`}
                    className="w-full h-full object-cover"
                    poster={highlight.videos.thumbnail_url}
                    preload="metadata"
                    muted
                    playsInline
                    onError={() => {
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
                        {'Summary'}
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

      {/* Video Modal */}
      <AnimatePresence>
        {selectedVideo && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeVideoModal}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[#0d0d0d] rounded-2xl p-6 w-full max-w-3xl mx-4 max-h-[90vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-semibold text-white">Video Details</h2>
                <button
                  onClick={closeVideoModal}
                  className="text-white/60 hover:text-white transition-colors"
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>

              <div className="space-y-6 max-h-[70vh] overflow-y-auto">
                {/* Video Preview */}
                {selectedVideo.videos.s3_link ? (
                  <video
                    src={`${selectedVideo.videos.s3_link}#t=0.001`}
                    className="w-full h-48 object-cover rounded-lg"
                    poster={selectedVideo.videos.thumbnail_url}
                    controls
                    autoPlay
                    playsInline
                    onError={() => {
                      console.error('Video failed to load in modal:', selectedVideo.videos.s3_link);
                    }}
                  />
                ) : (
                  <div className="w-full h-48 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white">
                      <polygon points="5,3 19,12 5,21"></polygon>
                    </svg>
                  </div>
                )}

                {/* Metadata */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-white/60">Created:</span>
                    <div className="text-white">{formatTimestamp(selectedVideo.created_at)}</div>
                  </div>
                  {selectedVideo.videos.duration && (
                    <div>
                      <span className="text-white/60">Duration:</span>
                      <div className="text-white">{Math.floor(selectedVideo.videos.duration / 60)}:{(selectedVideo.videos.duration % 60).toString().padStart(2, '0')}</div>
                    </div>
                  )}
                </div>

                {/* Full Summary */}
                {selectedVideo.videos.detailed_summary && (
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-3">Summary</h3>
                    <div className="bg-[#1a1a1a] rounded-lg p-4">
                      <p className="text-white leading-relaxed whitespace-pre-wrap">
                        {selectedVideo.videos.detailed_summary}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <BottomNav />
    </div>
  );
} 