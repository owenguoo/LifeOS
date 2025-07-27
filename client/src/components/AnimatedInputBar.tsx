import React, { useState, useRef } from 'react';
import { motion } from 'motion/react';

interface AnimatedInputBarProps {
  value: string;
  onChange: (val: string) => void;
  onKeyPress?: (e: React.KeyboardEvent) => void;
  onSend: () => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export default function AnimatedInputBar({
  value,
  onChange,
  onKeyPress,
  onSend,
  placeholder = 'Ask me about anything...',
  disabled = false,
  className = '',
}: AnimatedInputBarProps) {
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      <motion.div
        className="relative flex items-center justify-center group w-full"
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        transition={{ type: 'spring', stiffness: 400, damping: 17 }}
      >
        {/* Layered animated gradients (borrowed from AnimatedSearchBar) */}
        <div
          className="absolute z-[-1] overflow-hidden inset-x-0 top-0 bottom-1 rounded-lg blur-[3px] opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100 
                          before:absolute before:content-[''] before:z-[-2] before:w-[999px] before:h-[999px] before:bg-no-repeat before:top-1/2 before:left-1/2 before:-translate-x-1/2 before:-translate-y-1/2 before:rotate-60
                          before:bg-[conic-gradient(#0d0d0d,#7a2246_5%,#0d0d0d_38%,#0d0d0d_50%,#f2858e_60%,#0d0d0d_87%)] before:transition-all before:duration-2000
                          group-hover:before:rotate-[-120deg] group-focus-within:before:animate-[spin_4s_linear_infinite]"
        />

        <div
          className="absolute z-[-1] overflow-hidden inset-x-0 top-0 bottom-2 rounded-lg blur-[3px] opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100 
                          before:absolute before:content-[''] before:z-[-2] before:w-[600px] before:h-[600px] before:bg-no-repeat before:top-1/2 before:left-1/2 before:-translate-x-1/2 before:-translate-y-1/2 before:rotate-[82deg]
                          before:bg-[conic-gradient(rgba(0,0,0,0),#5a1a35,rgba(0,0,0,0)_10%,rgba(0,0,0,0)_50%,#f2858e,rgba(0,0,0,0)_60%)] before:transition-all before:duration-2000
                          group-hover:before:rotate-[-98deg] group-focus-within:before:animate-[spin_4s_linear_infinite]"
        />

        <div
          className="absolute z-[-1] overflow-hidden inset-x-0 top-0 bottom-2 rounded-lg blur-[3px] opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100 
                          before:absolute before:content-[''] before:z-[-2] before:w-[600px] before:h-[600px] before:bg-no-repeat before:top-1/2 before:left-1/2 before:-translate-x-1/2 before:-translate-y-1/2 before:rotate-[82deg]
                          before:bg-[conic-gradient(rgba(0,0,0,0),#5a1a35,rgba(0,0,0,0)_10%,rgba(0,0,0,0)_50%,#f2858e,rgba(0,0,0,0)_60%)] before:transition-all before:duration-2000
                          group-hover:before:rotate-[-98deg] group-focus-within:before:animate-[spin_4s_linear_infinite]"
        />

        <div
          className="absolute z-[-1] overflow-hidden inset-x-0 top-0 bottom-2 rounded-lg blur-[2px] opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100 
                          before:absolute before:content-[''] before:z-[-2] before:w-[600px] before:h-[600px] before:bg-no-repeat before:top-1/2 before:left-1/2 before:-translate-x-1/2 before:-translate-y-1/2 before:rotate-[83deg]
                          before:bg-[conic-gradient(rgba(0,0,0,0)_0%,#7a2246,rgba(0,0,0,0)_8%,rgba(0,0,0,0)_50%,#f2858e,rgba(0,0,0,0)_58%)] before:brightness-140
                          before:transition-all before:duration-2000 group-hover:before:rotate-[-97deg] group-focus-within:before:animate-[spin_4s_linear_infinite]"
        />

        <div
          className="absolute z-[-1] overflow-hidden inset-x-0 top-0 bottom-2 rounded-lg blur-[0.5px] opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100 
                          before:absolute before:content-[''] before:z-[-2] before:w-[600px] before:h-[600px] before:bg-no-repeat before:top-1/2 before:left-1/2 before:-translate-x-1/2 before:-translate-y-1/2 before:rotate-70
                          before:bg-[conic-gradient(#1a1a1a,#7a2246_5%,#1a1a1a_14%,#1a1a1a_50%,#f2858e_60%,#1a1a1a_64%)] before:brightness-130
                          before:transition-all before:duration-2000 group-hover:before:rotate-[-110deg] group-focus-within:before:animate-[spin_4s_linear_infinite]"
        />

        <div className="relative group w-full">
          <motion.textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyPress={onKeyPress}
            placeholder={placeholder}
            rows={1}
            disabled={disabled}
            className="bg-background border-none w-full rounded-lg text-white px-[20px] pr-14 py-3 text-lg focus:outline-none placeholder-white/60"
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            whileFocus={{ scale: 1.01 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            style={{
              scrollbarWidth: 'thin',
              scrollbarColor: 'var(--border) transparent',
            }}
          />

          <motion.button
            onClick={onSend}
            disabled={!value.trim() || disabled}
            className="disabled:opacity-50 disabled:cursor-not-allowed absolute right-2 top-1/2 -translate-y-1/2 p-3 transition-opacity"
            whileHover={{ scale: !value.trim() || disabled ? 1 : 1.1 }}
            whileTap={{ scale: !value.trim() || disabled ? 1 : 0.9 }}
          >
            <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
} 