'use client';

import { motion } from 'motion/react';

interface CustomToggleProps {
  id: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

export default function CustomToggle({ id, checked, onChange }: CustomToggleProps) {
  return (
    <label className="switch-button" htmlFor={id}>
      <div className="switch-outer">
        <input 
          id={id} 
          type="checkbox" 
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
        />
        <div className="button">
          <span className="button-toggle"></span>
          <span className="button-indicator"></span>
        </div>
      </div>
    </label>
  );
} 