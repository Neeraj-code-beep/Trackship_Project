import React from 'react';
import { AlertOctagon, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import './Alert.css';

export type AlertSeverity = 'critical' | 'warning' | 'opportunity' | 'info';

export interface AlertProps {
  severity?: AlertSeverity;
  title: string;
  category?: string;
  message: string;
  recommendation?: string;
  lapNumber?: number;
  onDismiss?: () => void;
  className?: string;
}

const severityConfig: Record<AlertSeverity, { icon: React.ReactNode; label: string }> = {
  critical: {
    icon: <AlertOctagon size={18} />,
    label: 'CRITICAL',
  },
  warning: {
    icon: <AlertTriangle size={18} />,
    label: 'WARNING',
  },
  opportunity: {
    icon: <CheckCircle size={18} />,
    label: 'OPPORTUNITY',
  },
  info: {
    icon: <Info size={18} />,
    label: 'INFO',
  },
};

export const Alert: React.FC<AlertProps> = ({
  severity = 'info',
  title,
  category,
  message,
  recommendation,
  lapNumber,
  onDismiss,
  className = '',
}) => {
  const cfg = severityConfig[severity];

  return (
    <div className={`sc-alert sc-alert--${severity} ${className}`}>
      <div className="sc-alert__icon-col">{cfg.icon}</div>

      <div className="sc-alert__content-col">
        <div className="sc-alert__header">
          <div className="sc-alert__meta">
            {category && <span className="sc-alert__category text-micro">{category}</span>}
            {lapNumber !== undefined && lapNumber !== null && (
              <span className="sc-alert__lap text-micro">Lap {lapNumber}</span>
            )}
            <span className="sc-alert__severity text-micro">{cfg.label}</span>
          </div>
          <h4 className="sc-alert__title text-h3">{title}</h4>
        </div>

        <p className="sc-alert__message text-body">{message}</p>

        {recommendation && (
          <div className="sc-alert__recommendation">
            <span className="sc-alert__rec-label text-micro">RECOMMENDATION</span>
            <p className="sc-alert__rec-text text-body-sm">{recommendation}</p>
          </div>
        )}
      </div>

      {onDismiss && (
        <button className="sc-alert__dismiss" onClick={onDismiss} aria-label="Dismiss">
          ×
        </button>
      )}
    </div>
  );
};

export default Alert;
