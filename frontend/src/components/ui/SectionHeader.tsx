import React from 'react';
import './SectionHeader.css';

export interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  subtitle,
  icon,
  action,
  className = '',
}) => {
  return (
    <div className={`sc-section-header ${className}`}>
      <div className="sc-section-header__title-group">
        {icon && <div className="sc-section-header__icon">{icon}</div>}
        <div>
          <h3 className="sc-section-header__title text-h3">{title}</h3>
          {subtitle && <p className="sc-section-header__subtitle text-caption">{subtitle}</p>}
        </div>
      </div>
      {action && <div className="sc-section-header__action">{action}</div>}
    </div>
  );
};

export default SectionHeader;
