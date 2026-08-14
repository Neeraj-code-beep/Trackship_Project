import React from 'react';
import { AlertTriangle, Info, AlertOctagon, Lightbulb } from 'lucide-react';
import type { InsightItem, InsightSeverity } from '../../types';
import './RaceInsightsFeed.css';

interface RaceInsightsFeedProps {
  insights: InsightItem[];
}

const severityConfig: Record<InsightSeverity, { icon: React.ReactNode; color: string; bg: string }> = {
  info: {
    icon: <Info size={16} />,
    color: '#60a5fa',
    bg: 'rgba(96, 165, 250, 0.08)',
  },
  warning: {
    icon: <AlertTriangle size={16} />,
    color: '#fbbf24',
    bg: 'rgba(251, 191, 36, 0.08)',
  },
  critical: {
    icon: <AlertOctagon size={16} />,
    color: '#f87171',
    bg: 'rgba(248, 113, 113, 0.08)',
  },
};

export const RaceInsightsFeed: React.FC<RaceInsightsFeedProps> = ({ insights }) => {
  if (!insights.length) {
    return (
      <div className="insights-feed insights-feed--empty">
        <Lightbulb size={32} className="insights-feed__empty-icon" />
        <p>No insights yet. Upload audio and lap data to generate race engineering observations.</p>
      </div>
    );
  }

  // Sort: critical first, then warning, then info
  const sorted = [...insights].sort((a, b) => {
    const order: Record<InsightSeverity, number> = { critical: 0, warning: 1, info: 2 };
    return order[a.severity] - order[b.severity];
  });

  return (
    <div className="insights-feed">
      <div className="insights-feed__header">
        <Lightbulb size={18} />
        <h3>Race Engineer Insights</h3>
        <span className="insights-feed__count">{insights.length}</span>
      </div>

      <div className="insights-feed__list">
        {sorted.map((insight) => {
          const cfg = severityConfig[insight.severity];
          return (
            <div
              className="insight-card"
              key={insight.id}
              style={{ background: cfg.bg, borderLeftColor: cfg.color }}
            >
              <div className="insight-card__icon" style={{ color: cfg.color }}>
                {cfg.icon}
              </div>
              <div className="insight-card__body">
                <div className="insight-card__meta">
                  <span className="insight-card__category">{insight.category}</span>
                  {insight.lap_number && (
                    <span className="insight-card__lap">Lap {insight.lap_number}</span>
                  )}
                  <span className="insight-card__severity" style={{ color: cfg.color }}>
                    {insight.severity.toUpperCase()}
                  </span>
                </div>
                <p className="insight-card__message">{insight.message}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RaceInsightsFeed;
