import React from 'react';
import './ProgressBar.css';

export type ProgressColor =
  | 'lime'
  | 'violet'
  | 'blue'
  | 'calm'
  | 'neutral'
  | 'fatigue'
  | 'stressed'
  | 'critical';

export interface ProgressBarProps {
  value: number; // 0 to 100
  color?: ProgressColor;
  height?: number;
  showValue?: boolean;
  label?: string;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  color = 'lime',
  height = 6,
  showValue = false,
  label,
  className = '',
}) => {
  const clamped = Math.min(100, Math.max(0, value));

  return (
    <div className={`sc-progress-container ${className}`}>
      {(label || showValue) && (
        <div className="sc-progress__header">
          {label && <span className="sc-progress__label text-label">{label}</span>}
          {showValue && <span className="sc-progress__value font-numeric">{clamped.toFixed(0)}%</span>}
        </div>
      )}
      <div className="sc-progress" style={{ height: `${height}px` }}>
        <div
          className={`sc-progress__fill sc-progress__fill--${color}`}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
