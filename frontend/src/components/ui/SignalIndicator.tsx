import React from 'react';
import './SignalIndicator.css';

export interface SignalIndicatorProps {
  status?: 'active' | 'processing' | 'warning' | 'idle';
  label?: string;
  className?: string;
}

export const SignalIndicator: React.FC<SignalIndicatorProps> = ({
  status = 'active',
  label,
  className = '',
}) => {
  return (
    <div className={`sc-signal sc-signal--${status} ${className}`}>
      <span className="sc-signal__dot">
        <span className="sc-signal__ring" />
      </span>
      {label && <span className="sc-signal__label text-micro">{label}</span>}
    </div>
  );
};

export default SignalIndicator;
