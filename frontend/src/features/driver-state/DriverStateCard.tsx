import React from 'react';
import { Heart, Zap, Minus, Moon } from 'lucide-react';
import type { EmotionProbabilities, EmotionLabel } from '../../types';
import './DriverState.css';

interface DriverStateCardProps {
  overallStress: number;
  overallFatigue: number;
  dominantEmotion?: EmotionLabel;
  probabilities?: EmotionProbabilities;
  processingTime?: number;
}

const emotionConfig: Record<EmotionLabel, { icon: React.ReactNode; color: string; gradient: string }> = {
  calm: {
    icon: <Heart size={20} />,
    color: '#34d399',
    gradient: 'linear-gradient(135deg, rgba(52,211,153,0.2), rgba(52,211,153,0.05))',
  },
  stressed: {
    icon: <Zap size={20} />,
    color: '#f87171',
    gradient: 'linear-gradient(135deg, rgba(248,113,113,0.2), rgba(248,113,113,0.05))',
  },
  neutral: {
    icon: <Minus size={20} />,
    color: '#60a5fa',
    gradient: 'linear-gradient(135deg, rgba(96,165,250,0.2), rgba(96,165,250,0.05))',
  },
  tired: {
    icon: <Moon size={20} />,
    color: '#fbbf24',
    gradient: 'linear-gradient(135deg, rgba(251,191,36,0.2), rgba(251,191,36,0.05))',
  },
};

export const DriverStateCard: React.FC<DriverStateCardProps> = ({
  overallStress,
  overallFatigue,
  dominantEmotion = 'neutral',
  probabilities,
  processingTime,
}) => {
  const config = emotionConfig[dominantEmotion];

  const metrics = [
    { label: 'Calm', value: probabilities?.calm ?? 0, color: '#34d399', key: 'calm' },
    { label: 'Stressed', value: probabilities?.stressed ?? overallStress, color: '#f87171', key: 'stressed' },
    { label: 'Neutral', value: probabilities?.neutral ?? 0, color: '#60a5fa', key: 'neutral' },
    { label: 'Fatigue', value: probabilities?.tired ?? overallFatigue, color: '#fbbf24', key: 'tired' },
  ];

  return (
    <div className="driver-state-card" style={{ background: config.gradient }}>
      <div className="driver-state-card__header">
        <div className="driver-state-card__icon" style={{ color: config.color }}>
          {config.icon}
        </div>
        <div>
          <h3 className="driver-state-card__title">Driver State</h3>
          <span className="driver-state-card__dominant" style={{ color: config.color }}>
            {dominantEmotion.charAt(0).toUpperCase() + dominantEmotion.slice(1)}
          </span>
        </div>
        {processingTime !== undefined && (
          <span className="driver-state-card__time">{processingTime.toFixed(0)}ms</span>
        )}
      </div>

      <div className="driver-state-card__metrics">
        {metrics.map((m) => (
          <div className="metric" key={m.key}>
            <div className="metric__header">
              <span className="metric__label">{m.label}</span>
              <span className="metric__value" style={{ color: m.color }}>
                {(m.value * 100).toFixed(0)}%
              </span>
            </div>
            <div className="metric__bar">
              <div
                className="metric__bar-fill"
                style={{
                  width: `${m.value * 100}%`,
                  background: m.color,
                  boxShadow: `0 0 8px ${m.color}40`,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DriverStateCard;
