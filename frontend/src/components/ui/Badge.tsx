import React from 'react';
import './Badge.css';

export type BadgeVariant =
  | 'default'
  | 'lime'
  | 'violet'
  | 'blue'
  | 'calm'
  | 'neutral'
  | 'fatigue'
  | 'stressed'
  | 'critical';

export interface BadgeProps {
  variant?: BadgeVariant;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  icon,
  children,
  className = '',
}) => {
  return (
    <span className={`sc-badge sc-badge--${variant} ${className}`}>
      {icon && <span className="sc-badge__icon">{icon}</span>}
      <span className="sc-badge__label">{children}</span>
    </span>
  );
};

export default Badge;
