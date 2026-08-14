import React from 'react';
import './State.css';

export interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = 20,
  borderRadius = 'var(--radius-sm)',
  className = '',
}) => {
  return (
    <div
      className={`sc-skeleton ${className}`}
      style={{
        width,
        height,
        borderRadius,
      }}
    />
  );
};

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className = '',
}) => {
  return (
    <div className={`sc-empty-state ${className}`}>
      {icon && <div className="sc-empty-state__icon">{icon}</div>}
      <h4 className="sc-empty-state__title text-h3">{title}</h4>
      {description && <p className="sc-empty-state__description text-body">{description}</p>}
      {action && <div className="sc-empty-state__action">{action}</div>}
    </div>
  );
};
