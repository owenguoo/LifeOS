'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { useAuth } from '@/contexts/AuthContext';
import AuthScreen from '@/components/AuthScreen';
import BottomNav from '@/components/BottomNav';

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  processing?: boolean;
}

interface ChatbotResponse {
  original_input: string;
  refined_query: string;
  video_found: boolean;
  ai_response: string;
  video_id?: string;
  timestamp?: string;
  summary?: string;
  confidence_score?: number;
  processing_time_ms?: number;
}

export default function ChatPage() {
  const { isAuthenticated, login, token, loading } = useAuth();
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleAuthSuccess = (token: string) => {
    login(token);
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_HOST}/api/v1/memory/chatbot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_input: userMessage.content,
          confidence_threshold: 0.01,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ChatbotResponse = await response.json();

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.ai_response,
        isUser: false,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
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
          <div className="text-2xl font-semibold text-text-primary mb-4">Initializing LifeOS...</div>
          <div className="loader mx-auto mb-4"></div>
        </motion.div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthScreen onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
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
              className="text-2xl font-semibold text-text-primary mx-auto"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              Chat with LifeOS
            </motion.h1>
          </div>
        </div>
      </motion.header>

      {/* Messages */}
      <main className="flex-1 pt-40 pb-56 px-6 overflow-y-auto">
        <div className="container mx-auto max-w-2xl px-4">
          <AnimatePresence>
            {messages.length === 0 ? (
              <motion.div
                className="flex items-center justify-center h-full text-center py-12"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                <div className="space-y-4">
                  <div className="text-4xl mb-4">💬</div>
                  <h2 className="text-xl font-semibold text-text-primary">Start a conversation</h2>
                  <p className="text-text-muted">Ask me about your memories, activities, or anything else!</p>
                </div>
              </motion.div>
            ) : (
              <div className="space-y-4 py-4">
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                    className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] p-4 rounded-lg ${
                        message.isUser
                          ? 'bg-primary text-white'
                          : 'glass-effect text-text-primary'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    </div>
                  </motion.div>
                ))}
                {isLoading && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex justify-start"
                  >
                    <div className="glass-effect p-4 rounded-lg max-w-[80%]">
                      <div className="flex items-center space-x-2">
                        <div className="loader" style={{ '--height-of-loader': '3px' } as React.CSSProperties}></div>
                        <span className="text-text-muted text-sm">Thinking...</span>
                      </div>
                    </div>
                  </motion.div>
                )}
              </div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input */}
      <motion.div 
        className="fixed bottom-40 left-4 right-4 z-20 py-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <div className="container mx-auto max-w-2xl px-6">
          <div className="relative bg-[#0d0d0d] border border-gray-400 rounded-lg flex items-center">
            <motion.textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me about anything..."
              className="flex-1 bg-transparent border-none px-4 py-3 text-white placeholder-white/60 resize-none min-h-[48px] max-h-32 focus:outline-none text-lg"
              rows={1}
              disabled={isLoading}
              style={{
                scrollbarWidth: 'thin',
                scrollbarColor: 'var(--border) transparent',
              }}
            />
            <motion.button
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="disabled:opacity-50 disabled:cursor-not-allowed p-3 mr-1 transition-opacity"
              whileHover={{ scale: !inputValue.trim() || isLoading ? 1 : 1.1 }}
              whileTap={{ scale: !inputValue.trim() || isLoading ? 1 : 0.9 }}
            >
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </motion.button>
          </div>
        </div>
      </motion.div>

      <BottomNav />
    </div>
  );
}