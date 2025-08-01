'use client';

import { motion } from 'motion/react';
import { useRouter, usePathname } from 'next/navigation';

export default function BottomNav() {
  const router = useRouter();
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path;

  return (
    <motion.nav 
      className="fixed bottom-0 left-0 right-0 z-20 glass-effect border-t border-border mb-16 max-w-[301px] mx-auto py-2"
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
    >
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-around">
            {/* Chat Tab */}
            <motion.button 
                className="flex flex-col items-center p-2 rounded-lg transition-colors group relative"
                whileHover={{ scale: 1.1, y: -2 }}
                whileTap={{ scale: 0.95 }}
                transition={{ type: "spring", stiffness: 400, damping: 17 }}
                onClick={() => router.push('/chat')}
            >
            <motion.svg
                className={`w-6 h-6 ${isActive('/') ? 'text-text-primary' : 'text-text-secondary'}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                whileHover={{ rotate: 5 }}
                transition={{ type: "spring", stiffness: 300 }}
            >
                <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
            </motion.svg>
            <motion.span 
                className={`text-xs ${isActive('/') ? 'text-text-primary' : 'text-text-secondary'} opacity-0 group-hover:opacity-100 absolute top-full mt-1 whitespace-nowrap`}
                initial={{ opacity: 0, y: 5 }}
                whileHover={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
            >
                Chat
            </motion.span>
        </motion.button>

          {/* Highlights Tab */}
          <motion.button 
            className="flex flex-col items-center p-2 rounded-lg transition-colors group relative"
            whileHover={{ scale: 1.1, y: -2 }}
            whileTap={{ scale: 0.95 }}
            transition={{ type: "spring", stiffness: 400, damping: 17 }}
            onClick={() => router.push('/highlights')}
          >
            <motion.img
              src="/highlights.svg"
              className={`w-6 h-6 ${isActive('/highlights') ? 'text-text-primary' : 'text-text-secondary'}`}
              whileHover={{ rotate: 5 }}
              transition={{ type: "spring", stiffness: 300 }}
              alt="Highlights"
            />
            <motion.span 
              className={`text-xs ${isActive('/highlights') ? 'text-text-primary' : 'text-text-secondary'} opacity-0 group-hover:opacity-100 absolute top-full mt-1 whitespace-nowrap`}
              initial={{ opacity: 0, y: 5 }}
              whileHover={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              Highlights
            </motion.span>
          </motion.button>

          {/* Activity Tab */}
          <motion.button 
            className="flex flex-col items-center p-2 rounded-lg transition-colors group relative"
            whileHover={{ scale: 1.1, y: -2 }}
            whileTap={{ scale: 0.95 }}
            transition={{ type: "spring", stiffness: 400, damping: 17 }}
            onClick={() => router.push('/activities')}
          >
            <motion.svg
              className={`w-6 h-6 ${isActive('/activities') ? 'text-text-primary' : 'text-text-secondary'}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              whileHover={{ rotate: 5 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </motion.svg>
            <motion.span 
              className={`text-xs ${isActive('/activities') ? 'text-text-primary' : 'text-text-secondary'} opacity-0 group-hover:opacity-100 absolute top-full mt-1 whitespace-nowrap`}
              initial={{ opacity: 0, y: 5 }}
              whileHover={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              Activity
            </motion.span>
          </motion.button>

          {/* Automations Tab */}
          <motion.button 
            className="flex flex-col items-center p-2 rounded-lg transition-colors group relative"
            whileHover={{ scale: 1.1, y: -2 }}
            whileTap={{ scale: 0.95 }}
            transition={{ type: "spring", stiffness: 400, damping: 17 }}
            onClick={() => router.push('/settings')}
          >
            <motion.svg
              className={`w-6 h-6 ${isActive('/settings') ? 'text-text-primary' : 'text-text-secondary'}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              whileHover={{ rotate: -5 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </motion.svg>
            <motion.span 
              className={`text-xs ${isActive('/settings') ? 'text-text-primary' : 'text-text-secondary'} opacity-0 group-hover:opacity-100 absolute top-full mt-1 whitespace-nowrap`}
              initial={{ opacity: 0, y: 5 }}
              whileHover={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              Automations
            </motion.span>
          </motion.button>
        </div>
      </div>
    </motion.nav>
  );
}
