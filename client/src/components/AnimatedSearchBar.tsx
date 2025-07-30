import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useAuth } from '../contexts/AuthContext';

interface SearchResult {
  id: string;
  video_id: string;
  timestamp: string;
  score: number;
  s3_url: string | null;
  detailed_summary: string;
  file_size: number | null;
  processed_at: string | null;
  user_id: string | null;
}

interface AnimatedSearchBarProps {
  placeholder?: string;
  className?: string;
}

export default function AnimatedSearchBar({ 
  placeholder = "Search memories...", 
  className = "" 
}: AnimatedSearchBarProps) {
  const [isFocused, setIsFocused] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResultsModal, setShowResultsModal] = useState(false);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { axiosInstance } = useAuth();

  const handleSearch = async () => {
    if (!searchQuery.trim() || isSearching) return;

    setIsSearching(true);
    setSearchError(null);
    setSearchResults([]);

    try {
      const response = await axiosInstance.post('/api/v1/memory/search', {
        query: searchQuery.trim(),
        limit: 3,
        score_threshold: 0.01
      });

      setSearchResults(response.data.results);
      setShowResultsModal(true);
    } catch (error: unknown) {
      console.error('Search error:', error);
      const errorMessage = error && typeof error === 'object' && 'response' in error 
        ? ((error.response as { data?: { detail?: string } })?.data?.detail) || 'Search failed. Please try again.'
        : 'Search failed. Please try again.';
      setSearchError(errorMessage);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  const handleResultClick = (result: SearchResult) => {
    setSelectedResult(result);
    setShowDetailModal(true);
    setShowResultsModal(false);
  };

  const closeResultsModal = () => {
    setShowResultsModal(false);
    setSearchResults([]);
    setSearchError(null);
  };

  const closeDetailModal = () => {
    setShowDetailModal(false);
    setShowResultsModal(true);
    setSelectedResult(null);
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return timestamp;
    }
  };

  const truncateSummary = (summary: string, maxLength: number = 150) => {
    if (summary.length <= maxLength) return summary;
    return summary.substring(0, maxLength) + '...';
  };

  return (
    <>
      <div className={`relative flex items-center justify-center ${className}`}>
        <div className="absolute z-[-1] w-full h-min-screen"></div>
        <motion.div 
          id="poda" 
          className="relative flex items-center justify-center group"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          transition={{ type: "spring", stiffness: 400, damping: 17 }}
        >
          <div className="absolute z-[-1] overflow-hidden h-full w-full max-h-[70px] max-w-[314px] rounded-xl blur-[3px] opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100 
                          before:absolute before:content-[''] before:z-[-2] before:w-[999px] before:h-[999px] before:bg-no-repeat before:top-1/2 before:left-1/2 before:-translate-x-1/2 before:-translate-y-1/2 before:rotate-60
                          before:bg-[conic-gradient(#0d0d0d,#7a2246_5%,#0d0d0d_38%,#0d0d0d_50%,#f2858e_60%,#0d0d0d_87%)] before:transition-all before:duration-2000
                          group-hover:before:rotate-[-120deg] group-focus-within:before:animate-[spin_4s_linear_infinite]">
          </div>
          <div className="absolute z-[-1] overflow-hidden h-full w-full max-h-[65px] max-w-[312px] rounded-xl blur-[3px] opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100 
                          before:absolute before:content-[''] before:z-[-2] before:w-[600px] before:h-[600px] before:bg-no-repeat before:top-1/2 before:left-1/2 before:-translate-x-1/2 before:-translate-y-1/2 before:rotate-[82deg]
                          before:bg-[conic-gradient(rgba(0,0,0,0),#5a1a35,rgba(0,0,0,0)_10%,rgba(0,0,0,0)_50%,#f2858e,rgba(0,0,0,0)_60%)] before:transition-all before:duration-2000
                          group-hover:before:rotate-[-98deg] group-focus-within:before:animate-[spin_4s_linear_infinite]">
          </div>
          <div className="absolute z-[-1] overflow-hidden h-full w-full max-h-[65px] max-w-[312px] rounded-xl blur-[3px] opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100 
                          before:absolute before:content-[''] before:z-[-2] before:w-[600px] before:h-[600px] before:bg-no-repeat before:top-1/2 before:left-1/2 before:-translate-x-1/2 before:-translate-y-1/2 before:rotate-[82deg]
                          before:bg-[conic-gradient(rgba(0,0,0,0),#5a1a35,rgba(0,0,0,0)_10%,rgba(0,0,0,0)_50%,#f2858e,rgba(0,0,0,0)_60%)] before:transition-all before:duration-2000
                          group-hover:before:rotate-[-98deg] group-focus-within:before:animate-[spin_4s_linear_infinite]">
          </div>
          <div className="absolute z-[-1] overflow-hidden h-full w-full max-h-[65px] max-w-[312px] rounded-xl blur-[3px] opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100 
                          before:absolute before:content-[''] before:z-[-2] before:w-[600px] before:h-[600px] before:bg-no-repeat before:top-1/2 before:left-1/2 before:-translate-x-1/2 before:-translate-y-1/2 before:rotate-[82deg]
                          before:bg-[conic-gradient(rgba(0,0,0,0),#5a1a35,rgba(0,0,0,0)_10%,rgba(0,0,0,0)_50%,#f2858e,rgba(0,0,0,0)_60%)] before:transition-all before:duration-2000
                          group-hover:before:rotate-[-98deg] group-focus-within:before:animate-[spin_4s_linear_infinite]">
          </div>

          <div className="absolute z-[-1] overflow-hidden h-full w-full max-h-[63px] max-w-[307px] rounded-lg blur-[2px] opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100 
                          before:absolute before:content-[''] before:z-[-2] before:w-[600px] before:h-[600px] before:bg-no-repeat before:top-1/2 before:left-1/2 before:-translate-x-1/2 before:-translate-y-1/2 before:rotate-[83deg]
                          before:bg-[conic-gradient(rgba(0,0,0,0)_0%,#7a2246,rgba(0,0,0,0)_8%,rgba(0,0,0,0)_50%,#f2858e,rgba(0,0,0,0)_58%)] before:brightness-140
                          before:transition-all before:duration-2000 group-hover:before:rotate-[-97deg] group-focus-within:before:animate-[spin_4s_linear_infinite]">
          </div>

          <div className="absolute z-[-1] overflow-hidden h-full w-full max-h-[59px] max-w-[303px] rounded-xl blur-[0.5px] opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100 
                          before:absolute before:content-[''] before:z-[-2] before:w-[600px] before:h-[600px] before:bg-no-repeat before:top-1/2 before:left-1/2 before:-translate-x-1/2 before:-translate-y-1/2 before:rotate-70
                          before:bg-[conic-gradient(#1a1a1a,#7a2246_5%,#1a1a1a_14%,#1a1a1a_50%,#f2858e_60%,#1a1a1a_64%)] before:brightness-130
                          before:transition-all before:duration-2000 group-hover:before:rotate-[-110deg] group-focus-within:before:animate-[spin_4s_linear_infinite]">
          </div>

          <div id="main" className="relative group">
            <motion.input 
              ref={inputRef}
              placeholder={placeholder} 
              type="text" 
              name="text" 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-[#0d0d0d] border-none w-[301px] h-[56px] rounded-lg text-white px-[59px] text-lg focus:outline-none placeholder-white/60" 
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              onKeyPress={handleKeyPress}
              whileFocus={{ scale: 1.01 }}
              transition={{ type: "spring", stiffness: 300, damping: 20 }}
            />

            <motion.div 
              id="search-icon" 
              className="absolute left-5 top-[15px]"
              animate={{ 
                rotate: isFocused ? 360 : 0,
                scale: isFocused ? 1.1 : 1
              }}
              transition={{ 
                rotate: { duration: 0.6, ease: "easeInOut" },
                scale: { duration: 0.2, ease: "easeInOut" }
              }}
            >
              {isSearching ? (
                <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" width="24" viewBox="0 0 24 24" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" height="24" fill="none" className="feather feather-search">
                  <circle stroke="url(#search)" r="8" cy="11" cx="11"></circle>
                  <line stroke="url(#searchl)" y2="16.65" y1="22" x2="16.65" x1="22"></line>
                  <defs>
                    <linearGradient gradientTransform="rotate(50)" id="search">
                      <stop stopColor="#f8e7f8" offset="0%"></stop>
                      <stop stopColor="#b6a9b7" offset="50%"></stop>
                    </linearGradient>
                    <linearGradient id="searchl">
                      <stop stopColor="#b6a9b7" offset="0%"></stop>
                      <stop stopColor="#837484" offset="50%"></stop>
                    </linearGradient>
                  </defs>
                </svg>
              )}
            </motion.div>
          </div>
        </motion.div>
      </div>

      {/* Search Results Modal */}
      <AnimatePresence>
        {showResultsModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
            onClick={closeResultsModal}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[#0d0d0d] rounded-2xl p-6 w-full max-w-2xl mx-4 max-h-[80vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-semibold text-white">Search Results</h2>
                <button
                  onClick={closeResultsModal}
                  className="text-white/60 hover:text-white transition-colors"
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>

              {searchError ? (
                <div className="text-red-400 text-center py-8">{searchError}</div>
              ) : searchResults.length === 0 ? (
                <div className="text-white/60 text-center py-8">No results found</div>
              ) : (
                <div className="space-y-4 max-h-[60vh] overflow-y-auto">
                  {searchResults.map((result, index) => (
                    <motion.div
                      key={result.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="bg-[#1a1a1a] rounded-lg p-4 cursor-pointer hover:bg-[#2a2a2a] transition-colors"
                      onClick={() => handleResultClick(result)}
                    >
                      <div className="flex items-start space-x-4">
                        {/* Video Preview */}
                        <div 
                          className="w-20 h-16 rounded-lg flex items-center justify-center flex-shrink-0 overflow-hidden relative group cursor-pointer"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleResultClick(result);
                          }}
                        >
                          {result.s3_url ? (
                            <video
                              src={`${result.s3_url}#t=0.001`}
                              className="w-full h-full object-cover"
                              preload="metadata"
                              muted
                              playsInline
                              onError={() => {
                                console.error('Video failed to load:', result.s3_url);
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
                          ) : (
                            <div className="w-full h-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white">
                                <polygon points="5,3 19,12 5,21"></polygon>
                              </svg>
                            </div>
                          )}
                          
                          {/* Play button overlay */}
                          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-black/20">
                            <div className="w-8 h-8 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center">
                              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M8 5v14l11-7z"/>
                              </svg>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="text-sm text-white/60 mb-1">
                            {formatTimestamp(result.timestamp)}
                          </div>
                          <div className="text-white text-sm leading-relaxed">
                            {truncateSummary(result.detailed_summary)}
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Detail Modal */}
      <AnimatePresence>
        {showDetailModal && selectedResult && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
            onClick={closeDetailModal}
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
                  onClick={closeDetailModal}
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
                {selectedResult.s3_url ? (
                  <video
                    src={`${selectedResult.s3_url}#t=0.001`}
                    className="w-full h-48 object-cover rounded-lg"
                    controls
                    autoPlay
                    playsInline
                    onError={() => {
                      console.error('Video failed to load in detail modal:', selectedResult.s3_url);
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
                    <div className="text-white">{formatTimestamp(selectedResult.timestamp)}</div>
                  </div>
                  <div>
                    <span className="text-white/60">Confidence:</span>
                    <div className="text-white">{(selectedResult.score * 100).toFixed(1)}%</div>
                  </div>
                  {selectedResult.file_size && (
                    <div>
                      <span className="text-white/60">File Size:</span>
                      <div className="text-white">{(selectedResult.file_size / 1024 / 1024).toFixed(2)} MB</div>
                    </div>
                  )}
                  {selectedResult.processed_at && (
                    <div>
                      <span className="text-white/60">Processed:</span>
                      <div className="text-white">{formatTimestamp(selectedResult.processed_at)}</div>
                    </div>
                  )}
                </div>

                {/* Full Summary */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-3">Summary</h3>
                  <div className="bg-[#1a1a1a] rounded-lg p-4">
                    <p className="text-white leading-relaxed whitespace-pre-wrap">
                      {selectedResult.detailed_summary}
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>


    </>
  );
} 