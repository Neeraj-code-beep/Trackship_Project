import React from 'react';
import { motion } from 'framer-motion';
import { Activity, Heart, Minus, Moon, Zap, ShieldCheck } from 'lucide-react';
import type { EmotionProbabilities, EmotionLabel } from '../../types';
import ProgressBar from '../../components/ui/ProgressBar';
import { EmptyState } from '../../components/ui/State';
import './DriverState.css';

interface DriverStateCardProps {
  overallStress: number | null;
  overallFatigue: number | null;
  dominantEmotion?: EmotionLabel;
  probabilities?: EmotionProbabilities;
  processingTime?: number;
}

const emotionConfig: Record<EmotionLabel, { icon: React.ReactNode; color: string; label: string; bg: string }> = {
  calm: {
    icon: <Heart size={18} />,
    color: 'var(--color-driver-calm)',
    label: 'CALM / NOMINAL',
    bg: 'rgba(69, 212, 131, 0.06)',
  },
  stressed: {
    icon: <Zap size={18} />,
    color: 'var(--color-driver-stressed)',
    label: 'ELEVATED STRESS',
    bg: 'rgba(255, 82, 82, 0.06)',
  },
  neutral: {
    icon: <Minus size={18} />,
    color: 'var(--color-text-secondary)',
    label: 'NEUTRAL BASELINE',
    bg: 'rgba(161, 168, 182, 0.06)',
  },
  tired: {
    icon: <Moon size={18} />,
    color: 'var(--color-driver-fatigue)',
    label: 'FATIGUE WARNING',
    bg: 'rgba(255, 184, 77, 0.06)',
  },
};

export const DriverStateCard: React.FC<DriverStateCardProps> = ({
  overallStress,
  overallFatigue,
  dominantEmotion = 'neutral',
  probabilities,
  processingTime,
}) => {
  if (overallStress === null || overallFatigue === null || !probabilities) {
    return (
      <div className="sc-driver-card">
        <div className="sc-driver-card__header">
          <div className="sc-driver-card__title-group">
            <div className="sc-driver-card__header-icon" style={{ color: 'var(--color-brand-lime)' }}>
              <Activity size={16} />
            </div>
            <div>
              <h3 className="text-h4 font-display" style={{ margin: 0 }}>Driver State Spectrum</h3>
              <span className="text-micro font-telemetry">ACOUSTIC & PHYSIOLOGICAL EMOTION MODEL</span>
            </div>
          </div>
        </div>
        <EmptyState
          icon={<Activity size={32} />}
          title="Awaiting Driver Telemetry"
          description="Driver stress and fatigue levels will be analyzed and plotted here upon audio session ingestion."
        />
      </div>
    );
  }

  const config = emotionConfig[dominantEmotion] || emotionConfig.neutral;

  const calmVal = (probabilities?.calm ?? 0) * 100;
  const stressVal = (probabilities?.stressed ?? overallStress) * 100;
  const neutralVal = (probabilities?.neutral ?? 0) * 100;
  const fatigueVal = (probabilities?.tired ?? overallFatigue) * 100;

  // Max probability
  const dominantPct = Math.max(calmVal, stressVal, neutralVal, fatigueVal);

  return (
    <div className="sc-driver-card">
      <div className="sc-driver-card__header">
        <div className="sc-driver-card__title-group">
          <div className="sc-driver-card__header-icon" style={{ color: 'var(--color-brand-lime)' }}>
            <Activity size={16} />
          </div>
          <div>
            <h3 className="text-h4 font-display" style={{ margin: 0 }}>Driver State Spectrum</h3>
            <span className="text-micro font-telemetry">ACOUSTIC & PHYSIOLOGICAL EMOTION MODEL</span>
          </div>
        </div>
        {processingTime !== undefined && (
          <span className="sc-driver-card__latency font-telemetry text-micro">
            {processingTime.toFixed(0)}ms INFERENCE
          </span>
        )}
      </div>

      {/* Main Dominant Emotion Hero Module */}
      <motion.div
        className="sc-driver-card__hero"
        style={{ borderColor: config.color, backgroundColor: config.bg }}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="sc-driver-card__dominant-left">
          <div className="sc-driver-card__icon-badge" style={{ color: config.color, borderColor: 'rgba(255,255,255,0.08)' }}>
            {config.icon}
          </div>
          <div className="sc-driver-card__dominant-text">
            <span className="text-micro" style={{ color: config.color }}>DOMINANT EMOTIONAL STATE</span>
            <h2 className="sc-driver-card__dominant-title font-display text-h3" style={{ color: 'var(--color-text-primary)' }}>{config.label}</h2>
          </div>
        </div>

        <div className="sc-driver-card__dominant-right">
          <div className="sc-driver-card__pct-box">
            <span className="sc-driver-card__pct-val font-telemetry" style={{ color: config.color }}>
              {dominantPct.toFixed(0)}%
            </span>
            <span className="text-micro font-telemetry" style={{ color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: 2 }}>
              <ShieldCheck size={10} /> CONFIDENCE
            </span>
          </div>
        </div>
      </motion.div>

      {/* Probability Spectrum List */}
      <div className="sc-driver-card__spectrum">
        <div className="sc-driver-card__spectrum-header">
          <span className="text-micro">PROBABILITY DISTRIBUTION SPECTRUM</span>
        </div>

        <div className="sc-driver-card__bar-item">
          <div className="sc-driver-card__bar-meta font-telemetry text-micro">
            <span className="font-display" style={{ color: 'var(--color-text-primary)' }}>Stressed</span>
            <span style={{ color: 'var(--color-driver-stressed)' }}>
              {stressVal.toFixed(1)}%
            </span>
          </div>
          <ProgressBar value={stressVal} color="stressed" height={6} />
        </div>

        <div className="sc-driver-card__bar-item">
          <div className="sc-driver-card__bar-meta font-telemetry text-micro">
            <span className="font-display" style={{ color: 'var(--color-text-primary)' }}>Calm / Nominal</span>
            <span style={{ color: 'var(--color-driver-calm)' }}>
              {calmVal.toFixed(1)}%
            </span>
          </div>
          <ProgressBar value={calmVal} color="calm" height={6} />
        </div>

        <div className="sc-driver-card__bar-item">
          <div className="sc-driver-card__bar-meta font-telemetry text-micro">
            <span className="font-display" style={{ color: 'var(--color-text-primary)' }}>Fatigue / Fatigue Index</span>
            <span style={{ color: 'var(--color-driver-fatigue)' }}>
              {fatigueVal.toFixed(1)}%
            </span>
          </div>
          <ProgressBar value={fatigueVal} color="fatigue" height={6} />
        </div>

        <div className="sc-driver-card__bar-item">
          <div className="sc-driver-card__bar-meta font-telemetry text-micro">
            <span className="font-display" style={{ color: 'var(--color-text-primary)' }}>Neutral Baseline</span>
            <span style={{ color: 'var(--color-text-secondary)' }}>
              {neutralVal.toFixed(1)}%
            </span>
          </div>
          <ProgressBar value={neutralVal} color="neutral" height={6} />
        </div>
      </div>
    </div>
  );
};

export default DriverStateCard;
