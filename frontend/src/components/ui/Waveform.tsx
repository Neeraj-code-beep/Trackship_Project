import React from 'react';
import './Waveform.css';

export interface WaveformProps {
  active?: boolean;
  barCount?: number;
  color?: 'violet' | 'lime' | 'blue' | 'stressed' | 'neutral';
  height?: number;
  className?: string;
}

export const Waveform: React.FC<WaveformProps> = ({
  active = false,
  barCount = 28,
  color = 'violet',
  height = 36,
  className = '',
}) => {
  const bars = Array.from({ length: barCount }, (_, i) => {
    // Generate organic pseudo-random heights
    const h = Math.sin(i * 0.5) * 35 + Math.cos(i * 0.3) * 25 + 40;
    return Math.max(15, Math.min(95, h));
  });

  return (
    <div
      className={`sc-waveform sc-waveform--${color} ${active ? 'sc-waveform--active' : ''} ${className}`}
      style={{ height: `${height}px` }}
    >
      {bars.map((pct, idx) => (
        <div
          key={idx}
          className="sc-waveform__bar"
          style={{
            height: `${pct}%`,
            animationDelay: active ? `${(idx % 7) * 0.12}s` : '0s',
          }}
        />
      ))}
    </div>
  );
};

export default Waveform;
