import React from 'react';
import './Card.css';

export interface CardProps {
  level?: 1 | 2 | 3;
  glass?: boolean;
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  level = 1,
  glass = false,
  children,
  className = '',
  onClick,
}) => {
  const levelClass = `surface-level-${level}`;
  const glassClass = glass ? 'glass-subtle' : '';

  return (
    <div
      className={`sc-card ${levelClass} ${glassClass} ${onClick ? 'sc-card--interactive' : ''} ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

export default Card;
