import React from 'react';
import { Activity, AlertTriangle, CheckCircle2, Clock, Loader2, Radio, XCircle } from 'lucide-react';
import Badge from './Badge';

export type StatusType =
  | 'LIVE'
  | 'ANALYZING'
  | 'PROCESSING'
  | 'READY'
  | 'COMPLETE'
  | 'WARNING'
  | 'CRITICAL'
  | 'ERROR'
  | 'INACTIVE';

export interface StatusBadgeProps {
  status: StatusType;
  label?: string;
  className?: string;
}

const statusConfig: Record<StatusType, { variant: any; icon: React.ReactNode; defaultText: string }> = {
  LIVE: {
    variant: 'lime',
    icon: <Radio size={12} className="sc-pulse-anim" />,
    defaultText: 'LIVE',
  },
  ANALYZING: {
    variant: 'violet',
    icon: <Loader2 size={12} className="sc-spin-anim" />,
    defaultText: 'ANALYZING',
  },
  PROCESSING: {
    variant: 'blue',
    icon: <Activity size={12} className="sc-spin-anim" />,
    defaultText: 'PROCESSING',
  },
  READY: {
    variant: 'lime',
    icon: <CheckCircle2 size={12} />,
    defaultText: 'READY',
  },
  COMPLETE: {
    variant: 'calm',
    icon: <CheckCircle2 size={12} />,
    defaultText: 'COMPLETE',
  },
  WARNING: {
    variant: 'fatigue',
    icon: <AlertTriangle size={12} />,
    defaultText: 'WARNING',
  },
  CRITICAL: {
    variant: 'critical',
    icon: <AlertTriangle size={12} />,
    defaultText: 'CRITICAL',
  },
  ERROR: {
    variant: 'stressed',
    icon: <XCircle size={12} />,
    defaultText: 'ERROR',
  },
  INACTIVE: {
    variant: 'default',
    icon: <Clock size={12} />,
    defaultText: 'INACTIVE',
  },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  className = '',
}) => {
  const cfg = statusConfig[status] || statusConfig.INACTIVE;

  return (
    <Badge variant={cfg.variant} icon={cfg.icon} className={className}>
      {label || cfg.defaultText}
    </Badge>
  );
};

export default StatusBadge;
