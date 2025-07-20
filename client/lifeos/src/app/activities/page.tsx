'use client';

import { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuth } from '../../contexts/AuthContext';
import BottomNav from '../../components/BottomNav';

interface RecentVideo {
  video_id: string;
  timestamp: string;
  summary: string;
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
              <Image src="/home.svg" alt="Home" width={24} height={24} className="w-6 h-6" />
            </motion.button>
            <motion.h1 
              className="text-2xl font-semibold text-text-primary"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              Recent Activities
            </motion.h1>
            <motion.div 
              className="text-sm text-text-secondary"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
            >
              {recentVideos.length} activities
            </motion.div>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="flex-1 pt-40 pb-20 px-4">
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
                  className="glass-effect rounded-lg p-4 border border-border hover:border-primary/30 transition-all duration-300"
                  variants={itemVariants}
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className="flex items-start space-x-4">
                    {/* Video thumbnail or icon */}
                    <div className="flex-shrink-0">
                      <div className="w-16 h-16 bg-gradient-to-br from-primary/20 to-primary/40 rounded-lg flex items-center justify-center">
                        <svg className="w-8 h-8 text-primary" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M8 5v14l11-7z"/>
                        </svg>
                      </div>
                    </div>

                    {/* Video content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-sm text-text-tertiary">
                          {formatTimestamp(video.timestamp)}
                        </div>
                        {video.file_size && (
                          <div className="text-xs text-text-tertiary">
                            {formatFileSize(video.file_size)}
                          </div>
                        )}
                      </div>
                      
                      <div className="text-text-primary font-medium mb-2 line-clamp-2">
                        {video.summary}
                      </div>
                      
                      <div className="flex items-center space-x-4 text-xs text-text-secondary">
                        <span>ID: {video.video_id.slice(0, 8)}...</span>
                        {video.processed_at && (
                          <span>Processed: {formatTimestamp(video.processed_at)}</span>
                        )}
                      </div>
                    </div>

                    {/* Action button */}
                    {video.s3_link && (
                      <div className="flex-shrink-0">
                        <button
                          onClick={() => window.open(video.s3_link, '_blank')}
                          className="p-2 text-text-secondary hover:text-primary transition-colors"
                          title="View video"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </button>
                      </div>
                    )}
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