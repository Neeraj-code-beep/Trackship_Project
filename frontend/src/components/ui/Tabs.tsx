import React from 'react';
import './Tabs.css';

export interface TabItem {
  id: string;
  label: string;
  badge?: string | number;
  icon?: React.ReactNode;
}

export interface TabsProps {
  items: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({
  items,
  activeId,
  onChange,
  className = '',
}) => {
  return (
    <div className={`sc-tabs ${className}`}>
      {items.map((tab) => {
        const isActive = tab.id === activeId;
        return (
          <button
            key={tab.id}
            className={`sc-tab ${isActive ? 'sc-tab--active' : ''}`}
            onClick={() => onChange(tab.id)}
            type="button"
          >
            {tab.icon && <span className="sc-tab__icon">{tab.icon}</span>}
            <span className="sc-tab__label">{tab.label}</span>
            {tab.badge !== undefined && (
              <span className={`sc-tab__badge ${isActive ? 'sc-tab__badge--active' : ''}`}>
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};

export default Tabs;
