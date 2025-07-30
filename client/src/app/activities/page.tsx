'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuth } from '../../contexts/AuthContext';
import BottomNav from '../../components/BottomNav';

interface RecentVideo {
  video_id: string;
  timestamp: string;
  detailed_summary: string;
  s3_link?: string;
  file_size?: number;
  processed_at: string;
  user_id?: string;
}

interface RecentVideosResponse {
  total_videos: number;
  recent_videos: RecentVideo[];
}

export default function ActivitiesPage() {
  const { axiosInstance } = useAuth();
  const router = useRouter();
  const [recentVideos, setRecentVideos] = useState<RecentVideo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // State for modal video view
  const [selectedVideo, setSelectedVideo] = useState<RecentVideo | null>(null);
  const [summaryExpanded, setSummaryExpanded] = useState(false);

  useEffect(() => {
    const fetchRecentVideos = async () => {
      try {
        setLoading(true);
        const response = await axiosInstance.get<RecentVideosResponse>('/api/v1/memory/recent-videos');
        console.log('Recent videos response:', response.data);
        setRecentVideos(response.data.recent_videos);
      } catch (err) {
        console.error('Error fetching recent videos:', err);
        setError('Failed to load recent activities');
      } finally {
        setLoading(false);
      }
    };

    fetchRecentVideos();
  }, [axiosInstance]);

  // Handlers for opening/closing modal
  const handleVideoClick = (video: RecentVideo) => {
    setSelectedVideo(video);
  };

  const closeVideoModal = () => {
    setSelectedVideo(null);
    setSummaryExpanded(false);
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

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <motion.div 
          className="text-center space-y-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="text-2xl font-semibold text-text-primary mb-4">Loading Activities...</div>
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
        className="py-4 mt-8 mx-auto w-[301px] z-20 glass-effect border-b border-border"
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
              className="text-2xl font-semibold text-text-primary mx-auto"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              Recent Activities
            </motion.h1>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="flex-1 pt-8 pb-40 px-4">
        <div className="container mx-auto max-w-4xl">
          {recentVideos.length === 0 ? (
            <motion.div 
              className="text-center py-20"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <div className="text-xl text-text-secondary mb-4">No recent activities</div>
              <div className="text-sm text-text-tertiary">
                Your video activities will appear here
              </div>
            </motion.div>
          ) : (
            <motion.div
              className="space-y-4"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              {recentVideos.map((video) => (
                <motion.div
                  key={video.video_id}
                  className="glass-effect rounded-lg p-4 border border-border hover:border-primary/30 transition-all duration-300 cursor-pointer"
                  variants={itemVariants}
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleVideoClick(video)}
                >
                  <div className="flex items-start space-x-4">
                    {/* Video thumbnail */}
                    <div className="flex-shrink-0">
                      <video
                        src={`${video.s3_link}#t=0.001`}
                        className="w-16 h-16 object-cover rounded-lg"
                        preload="metadata"
                        muted
                        playsInline
                      />
                    </div>

                    {/* Video content */}
                    <div className="flex-1 min-w-0">
                      <div className="mb-2 text-sm text-text-tertiary">
                        {formatTimestamp(video.timestamp)}
                      </div>
                      
                      <div className="font-xs mb-2 line-clamp-2">
                        {video.detailed_summary}
                      </div>
                      
                      {/* Empty flex item to preserve layout spacing when needed */}
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
                {selectedVideo.s3_link ? (
                  <video
                    src={`${selectedVideo.s3_link}#t=0.001`}
                    className="w-full h-48 object-cover rounded-lg"
                    controls
                    autoPlay
                    playsInline
                    onError={() => {
                      console.error('Video failed to load in modal:', selectedVideo.s3_link);
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
                    <span className="text-white/60">Timestamp:</span>
                    <div className="text-white">{formatTimestamp(selectedVideo.timestamp)}</div>
                  </div>
                </div>

                {/* Full Summary */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-3">Summary</h3>
                  <div className="bg-[#1a1a1a] rounded-lg p-4">
                    <p className="text-white leading-relaxed whitespace-pre-wrap">
                      {selectedVideo.detailed_summary}
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <BottomNav />
    </div>
  );
} 