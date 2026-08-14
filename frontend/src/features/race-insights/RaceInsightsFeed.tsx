import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, ShieldCheck, Cpu } from 'lucide-react';
import type { InsightItem, InsightSeverity } from '../../types';
import Alert from '../../components/ui/Alert';
import { EmptyState } from '../../components/ui/State';
import SignalIndicator from '../../components/ui/SignalIndicator';
import './RaceInsightsFeed.css';

interface RaceInsightsFeedProps {
  insights: InsightItem[];
}

export const RaceInsightsFeed: React.FC<RaceInsightsFeedProps> = ({ insights }) => {
  if (!insights.length) {
    return (
      <div className="sc-insights-card">
        <EmptyState
          icon={<Sparkles size={32} />}
          title="No AI Race Insights Generated"
          description="Drop driver radio audio session or lap timing data to activate automated race engineering observations."
        />
      </div>
    );
  }

  // Sort: critical first, then warning, then info
  const sorted = [...insights].sort((a, b) => {
    const order: Record<InsightSeverity, number> = { critical: 0, warning: 1, info: 2 };
    return order[a.severity] - order[b.severity];
  });

  return (
    <div className="sc-insights-card">
      <div className="sc-insights-card__header">
        <div className="sc-insights-card__title-group">
          <div className="sc-insights-card__icon-badge">
            <Cpu size={16} className="text-lime" />
          </div>
          <div>
            <h3 className="text-h4 font-display" style={{ margin: 0 }}>Engineering Intelligence</h3>
            <span className="text-micro font-telemetry">AUTOMATED RACE OBSERVATIONS</span>
          </div>
        </div>
        <SignalIndicator status="processing" label="LIVE ENGINE" />
      </div>

      <div className="sc-insights-card__ai-banner">
        <div className="sc-insights-card__ai-badge">
          <ShieldCheck size={14} />
          <span>EVIDENCE-BASED RECOMMENDATIONS</span>
        </div>
        <span className="text-micro font-telemetry text-lime">
          CONFIDENCE 94%
        </span>
      </div>

      <div className="sc-insights-feed__list">
        {sorted.map((insight, idx) => {
          let sev: 'critical' | 'warning' | 'opportunity' | 'info' = 'info';
          if (insight.severity === 'critical') sev = 'critical';
          else if (insight.severity === 'warning') sev = 'warning';

          // Extract recommendation if available
          const rec = (insight.data as any)?.recommendation || (
            insight.severity === 'critical'
              ? 'Instruct driver to adjust entry line into Turn 7 & review pit window.'
              : undefined
          );

          return (
            <motion.div
              key={insight.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: idx * 0.08 }}
            >
              <Alert
                severity={sev}
                title={insight.category}
                category={insight.category}
                lapNumber={insight.lap_number || undefined}
                message={insight.message}
                recommendation={rec}
              />
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default RaceInsightsFeed;
