import React from 'react';
import './MetricCard.css';

export interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'neutral';
  icon?: React.ReactNode;
  accentColor?: 'lime' | 'violet' | 'blue' | 'calm' | 'neutral' | 'fatigue' | 'stressed' | 'critical';
  subtext?: string;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit,
  delta,
  deltaType = 'neutral',
  icon,
  accentColor = 'blue',
  subtext,
  className = '',
}) => {
  return (
    <div className={`sc-metric-card sc-metric-card--accent-${accentColor} ${className}`}>
      <div className="sc-metric-card__header">
        <span className="sc-metric-card__label text-label">{label}</span>
        {icon && <div className="sc-metric-card__icon">{icon}</div>}
      </div>

      <div className="sc-metric-card__body">
        <div className="sc-metric-card__value-group">
          <span className="sc-metric-card__value font-numeric">{value}</span>
          {unit && <span className="sc-metric-card__unit">{unit}</span>}
        </div>

        {delta && (
          <span className={`sc-metric-card__delta sc-metric-card__delta--${deltaType} font-numeric`}>
            {delta}
          </span>
        )}
      </div>

      {subtext && <div className="sc-metric-card__subtext text-micro">{subtext}</div>}
    </div>
  );
};

export default MetricCard;
