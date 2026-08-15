import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence, type Variants } from 'framer-motion';
import {
  Gauge, Radio, Activity, Cpu, ArrowRight, Play, Pause,
  CheckCircle2, ChevronRight, Zap, ShieldAlert, Volume2, TrendingUp, BarChart3
} from 'lucide-react';
import {
  Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, ComposedChart, ReferenceLine
} from 'recharts';
import Waveform from '../../components/ui/Waveform';
import Button from '../../components/ui/Button';
import './LandingPage.css';

interface LandingPageProps {
  onEnterConsole: () => void;
}

const DEMO_TELEMETRY = [
  { lap: 'LAP 1', pace: 92.456, stress: 22, fatigue: 15 },
  { lap: 'LAP 2', pace: 90.123, stress: 20, fatigue: 17 },
  { lap: 'LAP 3', pace: 89.876, stress: 24, fatigue: 19 },
  { lap: 'LAP 4', pace: 91.234, stress: 35, fatigue: 22 },
  { lap: 'LAP 5', pace: 90.567, stress: 28, fatigue: 25 },
  { lap: 'LAP 6', pace: 92.890, stress: 45, fatigue: 28 },
  { lap: 'LAP 7', pace: 91.012, stress: 72, fatigue: 31 },
  { lap: 'LAP 8', pace: 93.456, stress: 68, fatigue: 34 },
];

export const LandingPage: React.FC<LandingPageProps> = ({ onEnterConsole }) => {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [activeDriverState, setActiveDriverState] = useState<'stressed' | 'calm'>('stressed');
  const [activePipelineStep, setActivePipelineStep] = useState(3);
  const [livePaceCounter, setLivePaceCounter] = useState(142.381);

  // Simulated micro telemetry update
  useEffect(() => {
    const interval = setInterval(() => {
      setLivePaceCounter((prev) => +(prev + (Math.random() * 0.008 - 0.004)).toFixed(3));
    }, 1800);
    return () => clearInterval(interval);
  }, []);

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  // Motion Variants
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.05 }
    }
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 24 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] }
    }
  };

  const cardHoverVariants: Variants = {
    rest: { y: 0, borderColor: 'rgba(255, 255, 255, 0.08)' },
    hover: {
      y: -3,
      borderColor: 'rgba(200, 255, 61, 0.35)',
      transition: { duration: 0.25, ease: [0.16, 1, 0.3, 1] }
    }
  };

  return (
    <div className="sc-landing">
      {/* Background System Grid & Ambient Lighting */}
      <div className="sc-landing__bg-grid" />
      <div className="sc-landing__ambient-glow" />

      {/* ── 01 — HERO SECTION ─────────────────────────────────────────── */}
      <section className="sc-landing__hero" id="hero">
        <div className="sc-landing__container">
          <motion.div
            className="sc-hero-content"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <motion.div className="sc-hero-eyebrow" variants={itemVariants}>
              <span className="sc-hero-badge font-telemetry">
                <span className="sc-hero-badge__dot" />
                AI RACE ENGINEERING INTELLIGENCE
              </span>
              <span className="sc-hero-meta font-telemetry text-micro">
                ILLUSTRATIVE SESSION · BAHRAIN GP · PRACTICE 2
              </span>
            </motion.div>

            <motion.h1 className="sc-hero-title text-display-giant font-display" variants={itemVariants}>
              Your race engineer,<br />
              <span className="text-gradient-lime">before the radio goes quiet.</span>
            </motion.h1>

            <motion.p className="sc-hero-subtitle text-body-lg" variants={itemVariants}>
              Silent Co-Driver unifies driver radio speech, acoustic stress signals, and high-frequency lap telemetry into automated, evidence-backed race engineering decisions.
            </motion.p>

            <motion.div className="sc-hero-cta-group" variants={itemVariants}>
              <Button
                variant="primary"
                size="lg"
                onClick={() => scrollToSection('product-signal')}
              >
                Explore the Intelligence <ArrowRight size={16} />
              </Button>
              <Button
                variant="secondary"
                size="lg"
                onClick={onEnterConsole}
              >
                Launch Command Console <Gauge size={16} />
              </Button>
            </motion.div>
          </motion.div>

          {/* Cinematic Hero Telemetry Workstation Visual */}
          <motion.div
            className="sc-hero-visual"
            initial={{ opacity: 0, scale: 0.97, y: 32 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.65, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="sc-hero-visual__glass">
              {/* Header Bar */}
              <div className="sc-hero-visual__top">
                <div className="sc-hero-visual__live">
                  <span className="sc-live-dot" />
                  <span className="font-telemetry text-micro text-lime">LIVE RACE FEED ● LAP 17</span>
                </div>
                <div className="sc-hero-visual__meta font-telemetry text-micro">
                  CHAMPIONSHIP STINT 02 · SOFT COMPOUND
                </div>
              </div>

              {/* 4 Telemetry Metrics Cards */}
              <div className="sc-hero-visual__metrics">
                <motion.div
                  className="sc-hero-visual__metric"
                  whileHover={{ y: -2, backgroundColor: 'rgba(255, 255, 255, 0.03)' }}
                >
                  <div className="sc-hero-visual__metric-head">
                    <span className="text-label">Pace Time</span>
                    <TrendingUp size={14} className="text-lime" />
                  </div>
                  <span className="telemetry-hero text-lime font-telemetry">
                    01:{(livePaceCounter).toFixed(3).replace('.', ':')}
                  </span>
                  <span className="telemetry-micro text-lime font-telemetry">-0.345s BEST PACE</span>
                </motion.div>

                <motion.div
                  className="sc-hero-visual__metric"
                  whileHover={{ y: -2, backgroundColor: 'rgba(255, 255, 255, 0.03)' }}
                >
                  <div className="sc-hero-visual__metric-head">
                    <span className="text-label">Driver Stress</span>
                    <Zap size={14} className="text-alert" />
                  </div>
                  <span className="telemetry-hero text-alert font-telemetry">68%</span>
                  <span className="telemetry-micro text-alert font-telemetry">+12% TURN 7</span>
                </motion.div>

                <motion.div
                  className="sc-hero-visual__metric"
                  whileHover={{ y: -2, backgroundColor: 'rgba(255, 255, 255, 0.03)' }}
                >
                  <div className="sc-hero-visual__metric-head">
                    <span className="text-label">Fatigue Index</span>
                    <Activity size={14} className="text-warning" />
                  </div>
                  <span className="telemetry-hero text-warning font-telemetry">24%</span>
                  <span className="telemetry-micro text-muted font-telemetry">NOMINAL STINT</span>
                </motion.div>

                <motion.div
                  className="sc-hero-visual__metric"
                  whileHover={{ y: -2, backgroundColor: 'rgba(255, 255, 255, 0.03)' }}
                >
                  <div className="sc-hero-visual__metric-head">
                    <span className="text-label">Top Speed</span>
                    <BarChart3 size={14} style={{ color: 'var(--color-text-secondary)' }} />
                  </div>
                  <span className="telemetry-hero font-telemetry" style={{ color: 'var(--color-text-primary)' }}>312.4</span>
                  <span className="telemetry-micro font-telemetry" style={{ color: 'var(--color-text-secondary)' }}>KM/H DRS</span>
                </motion.div>
              </div>

              {/* Real-time Sector Breakdown */}
              <div className="sc-hero-visual__sectors font-telemetry text-micro">
                <div className="sc-sector-item">
                  <span className="text-muted">SECTOR 1</span>
                  <span className="text-lime">28.421s (-0.112s)</span>
                </div>
                <div className="sc-sector-divider" />
                <div className="sc-sector-item">
                  <span className="text-muted">SECTOR 2</span>
                  <span className="text-warning">39.104s (+0.084s)</span>
                </div>
                <div className="sc-sector-divider" />
                <div className="sc-sector-item">
                  <span className="text-muted">SECTOR 3</span>
                  <span className="text-lime">34.856s (-0.233s)</span>
                </div>
              </div>

              {/* Equalizer Audio Waveform */}
              <div className="sc-hero-visual__waveform-strip">
                <Waveform active barCount={64} color="lime" height={36} />
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Section Divider Motif */}
      <div className="sc-section-divider">
        <div className="sc-section-divider__line" />
        <div className="sc-section-divider__node font-telemetry">SIGNAL PIPELINE</div>
        <div className="sc-section-divider__line" />
      </div>

      {/* ── 02 — PRODUCT SIGNAL SECTION ─────────────────────────────── */}
      <section className="sc-section" id="product-signal">
        <div className="sc-landing__container">
          <div className="sc-section-header text-center">
            <span className="text-label text-lime">02 · CORE TRANSFORMATION</span>
            <h2 className="text-h1 font-display">From Raw Signal to Strategic Race Decision</h2>
            <p className="text-body-lg max-w-2xl mx-auto">
              Silent Co-Driver captures chaotic cockpit radio audio and noisy telemetry, structuring it into automated, evidence-backed race engineering recommendations.
            </p>
          </div>

          <div className="sc-signal-pipeline">
            {/* Animated Signal Particle Track */}
            <div className="sc-signal-pipeline__track">
              <motion.div
                className="sc-signal-pipeline__beam"
                animate={{
                  x: ['0%', '100%'],
                  opacity: [0, 1, 1, 0]
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              />
            </div>

            <motion.div
              className={`sc-pipeline-step ${activePipelineStep === 0 ? 'sc-pipeline-step--active' : ''}`}
              variants={cardHoverVariants}
              initial="rest"
              whileHover="hover"
              onClick={() => setActivePipelineStep(0)}
            >
              <div className="sc-pipeline-step__num font-telemetry">01</div>
              <div className="sc-pipeline-step__icon">
                <Radio size={20} className="text-lime" />
              </div>
              <h3 className="text-h4 font-display">Raw Radio Audio</h3>
              <p className="text-body-sm">Multimodal cockpit audio speech ingested directly during lap stints.</p>
              <span className="sc-pipeline-tag font-telemetry">WHISPER ASR</span>
            </motion.div>

            <div className="sc-pipeline-arrow"><ChevronRight size={18} /></div>

            <motion.div
              className={`sc-pipeline-step ${activePipelineStep === 1 ? 'sc-pipeline-step--active' : ''}`}
              variants={cardHoverVariants}
              initial="rest"
              whileHover="hover"
              onClick={() => setActivePipelineStep(1)}
            >
              <div className="sc-pipeline-step__num font-telemetry">02</div>
              <div className="sc-pipeline-step__icon">
                <Activity size={20} className="text-lime" />
              </div>
              <h3 className="text-h4 font-display">Acoustic Emotion</h3>
              <p className="text-body-sm">Prosodic feature extraction detecting stress, fatigue, and baseline calm states.</p>
              <span className="sc-pipeline-tag font-telemetry">PROSODIC MODEL</span>
            </motion.div>

            <div className="sc-pipeline-arrow"><ChevronRight size={18} /></div>

            <motion.div
              className={`sc-pipeline-step ${activePipelineStep === 2 ? 'sc-pipeline-step--active' : ''}`}
              variants={cardHoverVariants}
              initial="rest"
              whileHover="hover"
              onClick={() => setActivePipelineStep(2)}
            >
              <div className="sc-pipeline-step__num font-telemetry">03</div>
              <div className="sc-pipeline-step__icon">
                <Gauge size={20} className="text-lime" />
              </div>
              <h3 className="text-h4 font-display">Lap Telemetry</h3>
              <p className="text-body-sm">Sector timing, delta tracking, and tyre degradation correlation.</p>
              <span className="sc-pipeline-tag font-telemetry">SECTOR CORRELATION</span>
            </motion.div>

            <div className="sc-pipeline-arrow"><ChevronRight size={18} /></div>

            <motion.div
              className={`sc-pipeline-step sc-pipeline-step--accent ${activePipelineStep === 3 ? 'sc-pipeline-step--active' : ''}`}
              variants={cardHoverVariants}
              initial="rest"
              whileHover="hover"
              onClick={() => setActivePipelineStep(3)}
            >
              <div className="sc-pipeline-step__num font-telemetry text-lime">04</div>
              <div className="sc-pipeline-step__icon">
                <Cpu size={20} className="text-lime" />
              </div>
              <h3 className="text-h4 font-display">Engineer Decision</h3>
              <p className="text-body-sm">Automated evidence-backed recommendations for apex entry & tyre strategy.</p>
              <span className="sc-pipeline-tag sc-pipeline-tag--lime font-telemetry">AI INSIGHT</span>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Section Divider Motif */}
      <div className="sc-section-divider">
        <div className="sc-section-divider__line" />
        <div className="sc-section-divider__node font-telemetry">LIVE INSTRUMENTATION</div>
        <div className="sc-section-divider__line" />
      </div>

      {/* ── 03 — LIVE RACE INTELLIGENCE ─────────────────────────────── */}
      <section className="sc-section" id="telemetry-intelligence">
        <div className="sc-landing__container">
          <div className="sc-grid-2col">
            <div className="sc-text-col">
              <span className="text-label text-lime">03 · LIVE INSTRUMENTATION</span>
              <h2 className="text-h1 font-display">Instrumentation-Grade Telemetry Precision</h2>
              <p className="text-body-lg">
                Engineered specifically for live motorsport telemetry. Numerical values line up with tabular precision, preventing layout jumps under high-frequency updates.
              </p>

              <div className="sc-feature-list">
                <div className="sc-feature-item">
                  <CheckCircle2 size={18} className="text-lime" />
                  <div>
                    <strong className="text-h4">Tabular Monospace Formatting</strong>
                    <p className="text-body-sm">Sub-millisecond lap timing figures (`font-variant-numeric: tabular-nums`).</p>
                  </div>
                </div>
                <div className="sc-feature-item">
                  <CheckCircle2 size={18} className="text-lime" />
                  <div>
                    <strong className="text-h4">Delta-to-Best Tracking</strong>
                    <p className="text-body-sm">Instant visual feedback on lap time gains or sector losses.</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="sc-card-col">
              <motion.div
                className="sc-telemetry-box surface-level-1"
                variants={cardHoverVariants}
                initial="rest"
                whileHover="hover"
              >
                <div className="sc-telemetry-box__header">
                  <span className="font-telemetry text-micro text-lime">LIVE INSTRUMENTATION READOUT</span>
                  <span className="font-telemetry text-micro text-muted">98.4% DATA ACCURACY</span>
                </div>
                <div className="sc-telemetry-box__grid">
                  <div className="sc-metric-unit">
                    <span className="text-label">CURRENT LAP</span>
                    <span className="telemetry-lg text-lime font-telemetry">01:42.381</span>
                  </div>
                  <div className="sc-metric-unit">
                    <span className="text-label">DELTA TO BEST</span>
                    <span className="telemetry-lg text-lime font-telemetry">-0.345s</span>
                  </div>
                  <div className="sc-metric-unit">
                    <span className="text-label">SECTOR 1 TIME</span>
                    <span className="telemetry-lg font-telemetry">28.421s</span>
                  </div>
                  <div className="sc-metric-unit">
                    <span className="text-label">TOP SPEED</span>
                    <span className="telemetry-lg font-telemetry">312.4 <span className="text-body-sm font-telemetry">KM/H</span></span>
                  </div>
                  <div className="sc-metric-unit">
                    <span className="text-label">TYRE WEAR (FL)</span>
                    <span className="telemetry-lg text-warning font-telemetry">18.4%</span>
                  </div>
                  <div className="sc-metric-unit">
                    <span className="text-label">APEX SPEED (T7)</span>
                    <span className="telemetry-lg text-alert font-telemetry">184.2 KM/H</span>
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Section Divider Motif */}
      <div className="sc-section-divider">
        <div className="sc-section-divider__line" />
        <div className="sc-section-divider__node font-telemetry">PHYSIOLOGICAL MODEL</div>
        <div className="sc-section-divider__line" />
      </div>

      {/* ── 04 — DRIVER STATE SPECTRUM ───────────────────────────────── */}
      <section className="sc-section" id="driver-state">
        <div className="sc-landing__container">
          <div className="sc-section-header text-center">
            <span className="text-label text-lime">04 · PHYSIOLOGICAL MODEL</span>
            <h2 className="text-h1 font-display">Driver State & Emotional Spectrum</h2>
            <p className="text-body-lg max-w-2xl mx-auto">
              Acoustic analysis interprets driver stress, fatigue, and calm baseline states from raw cockpit radio transmissions.
            </p>
          </div>

          <div className="sc-state-demo surface-level-1">
            <div className="sc-state-demo__header">
              <div className="sc-state-demo__tabs">
                <button
                  className={`sc-state-tab ${activeDriverState === 'stressed' ? 'sc-state-tab--active' : ''}`}
                  onClick={() => setActiveDriverState('stressed')}
                >
                  STRESSED STATE (72%)
                </button>
                <button
                  className={`sc-state-tab ${activeDriverState === 'calm' ? 'sc-state-tab--active' : ''}`}
                  onClick={() => setActiveDriverState('calm')}
                >
                  CALM STATE (16%)
                </button>
              </div>
              <span className="font-telemetry text-micro text-muted">142ms ACOUSTIC INFERENCE</span>
            </div>

            <div className="sc-state-demo__body">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeDriverState}
                  className="sc-state-hero-box"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25 }}
                  style={{
                    borderColor: activeDriverState === 'stressed' ? 'var(--color-driver-stressed)' : 'var(--color-driver-calm)',
                    backgroundColor: activeDriverState === 'stressed' ? 'rgba(255, 82, 82, 0.06)' : 'rgba(69, 212, 131, 0.06)'
                  }}
                >
                  <div className="sc-state-hero-box__left">
                    <span className="text-micro" style={{ color: activeDriverState === 'stressed' ? 'var(--color-driver-stressed)' : 'var(--color-driver-calm)' }}>
                      DOMINANT PHYSIOLOGICAL STATE
                    </span>
                    <h3 className="text-h2 font-display">
                      {activeDriverState === 'stressed' ? 'ELEVATED STRESS' : 'CALM BASELINE'}
                    </h3>
                    <p className="text-body-sm">
                      {activeDriverState === 'stressed'
                        ? 'Speech pitch variance shifted +14Hz over baseline. High acoustic tremor detected during Turn 7 corner entry.'
                        : 'Acoustic pitch and cadence remain steady within 1.2% nominal variation. Baseline pacing clear.'}
                    </p>
                  </div>
                  <div className="sc-state-hero-box__right">
                    <span className="telemetry-hero font-telemetry" style={{ color: activeDriverState === 'stressed' ? 'var(--color-driver-stressed)' : 'var(--color-driver-calm)' }}>
                      {activeDriverState === 'stressed' ? '72%' : '16%'}
                    </span>
                  </div>
                </motion.div>
              </AnimatePresence>

              {/* Probability Spectrum Bars */}
              <div className="sc-state-spectrum">
                <div className="sc-spectrum-item">
                  <div className="sc-spectrum-meta font-telemetry text-micro">
                    <span className="text-lime">CALM</span>
                    <span>{activeDriverState === 'stressed' ? '16%' : '84%'}</span>
                  </div>
                  <div className="sc-spectrum-bar-track">
                    <motion.div
                      className="sc-spectrum-bar-fill"
                      style={{ backgroundColor: 'var(--color-driver-calm)' }}
                      animate={{ width: activeDriverState === 'stressed' ? '16%' : '84%' }}
                      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                    />
                  </div>
                </div>

                <div className="sc-spectrum-item">
                  <div className="sc-spectrum-meta font-telemetry text-micro">
                    <span style={{ color: 'var(--color-text-secondary)' }}>NEUTRAL</span>
                    <span>{activeDriverState === 'stressed' ? '12%' : '10%'}</span>
                  </div>
                  <div className="sc-spectrum-bar-track">
                    <motion.div
                      className="sc-spectrum-bar-fill"
                      style={{ backgroundColor: 'var(--color-text-secondary)' }}
                      animate={{ width: activeDriverState === 'stressed' ? '12%' : '10%' }}
                      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                    />
                  </div>
                </div>

                <div className="sc-spectrum-item">
                  <div className="sc-spectrum-meta font-telemetry text-micro">
                    <span className="text-warning">FATIGUE</span>
                    <span>{activeDriverState === 'stressed' ? '24%' : '4%'}</span>
                  </div>
                  <div className="sc-spectrum-bar-track">
                    <motion.div
                      className="sc-spectrum-bar-fill"
                      style={{ backgroundColor: 'var(--color-driver-fatigue)' }}
                      animate={{ width: activeDriverState === 'stressed' ? '24%' : '4%' }}
                      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                    />
                  </div>
                </div>

                <div className="sc-spectrum-item">
                  <div className="sc-spectrum-meta font-telemetry text-micro">
                    <span className="text-alert">STRESSED</span>
                    <span>{activeDriverState === 'stressed' ? '72%' : '2%'}</span>
                  </div>
                  <div className="sc-spectrum-bar-track">
                    <motion.div
                      className="sc-spectrum-bar-fill"
                      style={{ backgroundColor: 'var(--color-driver-stressed)' }}
                      animate={{ width: activeDriverState === 'stressed' ? '72%' : '2%' }}
                      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section Divider Motif */}
      <div className="sc-section-divider">
        <div className="sc-section-divider__line" />
        <div className="sc-section-divider__node font-telemetry">AUTOMATED STRATEGY</div>
        <div className="sc-section-divider__line" />
      </div>

      {/* ── 05 — AI RACE ENGINEER ────────────────────────────────────── */}
      <section className="sc-section" id="ai-engineer">
        <div className="sc-landing__container">
          <div className="sc-grid-2col">
            <div className="sc-text-col">
              <span className="text-label text-lime">05 · AUTOMATED STRATEGY</span>
              <h2 className="text-h1 font-display">Actionable AI Race Engineer Recommendations</h2>
              <p className="text-body-lg">
                Engineers don't need raw predictions—they need evidence-backed decisions. Silent Co-Driver correlates driver stress flags with lap sector loss to generate instant engineering instructions.
              </p>
            </div>

            <div className="sc-card-col">
              <motion.div
                className="sc-ai-card surface-level-1"
                variants={cardHoverVariants}
                initial="rest"
                whileHover="hover"
              >
                <div className="sc-ai-card__top">
                  <span className="sc-alert-badge sc-alert-badge--critical">
                    <ShieldAlert size={12} /> CRITICAL
                  </span>
                  <span className="font-telemetry text-micro text-lime">CORNERING DEGRADATION · LAP 07</span>
                </div>
                <h3 className="text-h3 font-display">Turn 7 Rear Axle Instability</h3>
                
                <div className="sc-ai-evidence">
                  <span className="text-micro text-muted">EVIDENCE CORRELATION:</span>
                  <p className="text-body-sm" style={{ margin: '4px 0 0 0' }}>
                    Driver stress surged to 72% correlated with a +0.42s pace loss on Turn 7 corner entry and +14Hz acoustic speech pitch shift.
                  </p>
                </div>

                <div className="sc-ai-recommendation">
                  <span className="text-label text-lime">ENGINEER RECOMMENDATION:</span>
                  <p className="text-body font-grotesk" style={{ color: 'var(--color-text-primary)', margin: '6px 0 0 0', fontWeight: 600 }}>
                    "Instruct driver to brake 8m earlier into Turn 7 to stabilize rear axle and extend tyre life."
                  </p>
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Section Divider Motif */}
      <div className="sc-section-divider">
        <div className="sc-section-divider__line" />
        <div className="sc-section-divider__node font-telemetry">AUDIO SPEECH ALIGNMENT</div>
        <div className="sc-section-divider__line" />
      </div>

      {/* ── 06 — RADIO → INSIGHT PIPELINE ───────────────────────────── */}
      <section className="sc-section" id="radio-insight">
        <div className="sc-landing__container">
          <div className="sc-section-header text-center">
            <span className="text-label text-lime">06 · AUDIO SPEECH ALIGNMENT</span>
            <h2 className="text-h1 font-display">Driver Radio Waveform to Strategic Insight</h2>
            <p className="text-body-lg max-w-2xl mx-auto">
              Synchronized audio transcript timeline with speech emotion extraction.
            </p>
          </div>

          <div className="sc-radio-demo surface-level-1">
            <div className="sc-radio-demo__top">
              <button
                className={`sc-play-btn ${isPlayingAudio ? 'sc-play-btn--active' : ''}`}
                onClick={() => setIsPlayingAudio(!isPlayingAudio)}
              >
                {isPlayingAudio ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: 2 }} />}
              </button>
              <div className="sc-radio-demo__info">
                <span className="font-telemetry text-body font-bold" style={{ color: 'var(--color-text-primary)' }}>
                  DRIVER_RADIO_STINT_02.WAV
                </span>
                <span className="font-telemetry text-micro text-lime">94% SPEECH ASR CONFIDENCE</span>
              </div>
              <div className="sc-radio-demo__status font-telemetry text-micro text-muted">
                <Volume2 size={14} className="text-lime" />
                <span>ACOUSTIC FEED ONLINE</span>
              </div>
            </div>

            <div className="sc-radio-demo__wave">
              <Waveform active={isPlayingAudio} barCount={64} color={isPlayingAudio ? 'lime' : 'neutral'} height={40} />
            </div>

            <div className="sc-transcript-box">
              <div className="sc-transcript-line">
                <span className="font-telemetry text-micro text-muted">00:14.3</span>
                <span className="sc-speaker-tag">DRIVER 01</span>
                <span className="text-body" style={{ color: 'var(--color-text-primary)' }}>
                  "Rear is moving a lot through Turn 7 entry..."
                </span>
                <span className="sc-flag-pill font-telemetry">STRESS ELEVATED (72%)</span>
              </div>
              <div className="sc-transcript-line sc-transcript-line--engineer">
                <span className="font-telemetry text-micro text-muted">00:18.9</span>
                <span className="sc-speaker-tag sc-speaker-tag--engineer">RACE ENGINEER</span>
                <span className="text-body" style={{ color: 'var(--color-text-primary)' }}>
                  "Copy LAP 07 telemetry shows 8m late braking. Shift brake bias +1% forward."
                </span>
                <span className="sc-flag-pill sc-flag-pill--lime font-telemetry">INSTRUCTION SENT</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section Divider Motif */}
      <div className="sc-section-divider">
        <div className="sc-section-divider__line" />
        <div className="sc-section-divider__node font-telemetry">MULTI-AXIS CORRELATION</div>
        <div className="sc-section-divider__line" />
      </div>

      {/* ── 07 — TELEMETRY CORRELATION CHART ────────────────────────── */}
      <section className="sc-section" id="telemetry-chart">
        <div className="sc-landing__container">
          <div className="sc-section-header text-center">
            <span className="text-label text-lime">07 · MULTI-AXIS CORRELATION</span>
            <h2 className="text-h1 font-display">Lap Performance vs. Driver Emotional State</h2>
            <p className="text-body-lg max-w-2xl mx-auto">
              Correlating high-frequency lap times with physiological driver stress and fatigue indices.
            </p>
          </div>

          <div className="sc-chart-card surface-level-1">
            <ResponsiveContainer width="100%" height={320}>
              <ComposedChart data={DEMO_TELEMETRY} margin={{ top: 15, right: 15, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255, 255, 255, 0.06)" />
                <XAxis dataKey="lap" stroke="var(--color-text-muted)" fontSize={11} fontFamily="JetBrains Mono" />
                <YAxis yAxisId="time" stroke="var(--color-text-muted)" fontSize={11} fontFamily="JetBrains Mono" domain={['dataMin - 0.5', 'dataMax + 0.5']} />
                <YAxis yAxisId="pct" orientation="right" stroke="var(--color-text-muted)" fontSize={10} fontFamily="JetBrains Mono" domain={[0, 100]} unit="%" />
                <Tooltip contentStyle={{ backgroundColor: 'rgba(11, 14, 18, 0.94)', borderColor: 'rgba(255, 255, 255, 0.15)', borderRadius: '8px', fontFamily: 'JetBrains Mono' }} />
                <ReferenceLine yAxisId="time" y={89.876} stroke="var(--color-brand-lime)" strokeDasharray="3 3" label={{ value: 'BEST PACE', fill: 'var(--color-brand-lime)', fontSize: 10, fontFamily: 'JetBrains Mono' }} />
                <Area yAxisId="pct" type="monotone" dataKey="stress" fill="rgba(255, 82, 82, 0.15)" stroke="#FF5252" strokeWidth={2} name="Stress %" />
                <Line yAxisId="time" type="monotone" dataKey="pace" stroke="var(--color-brand-lime)" strokeWidth={3} name="Lap Pace (s)" dot={{ fill: 'var(--color-brand-lime)', r: 4 }} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      {/* Section Divider Motif */}
      <div className="sc-section-divider">
        <div className="sc-section-divider__line" />
        <div className="sc-section-divider__node font-telemetry">THE UNIFIED STORY</div>
        <div className="sc-section-divider__line" />
      </div>

      {/* ── 08 — WHY SILENT CO-DRIVER ───────────────────────────────── */}
      <section className="sc-section" id="why-silent">
        <div className="sc-landing__container">
          <div className="sc-section-header text-center">
            <span className="text-label text-lime">08 · THE UNIFIED STORY</span>
            <h2 className="text-h1 font-display">Because Lap Time is Only Half the Story</h2>
          </div>

          <div className="sc-why-grid">
            <motion.div
              className="sc-why-card surface-level-1"
              variants={cardHoverVariants}
              initial="rest"
              whileHover="hover"
            >
              <span className="font-telemetry text-micro text-lime">01 · VEHICLE STATE</span>
              <h3 className="text-h3 font-display">What the Car Did</h3>
              <p className="text-body-sm">High-frequency telemetry logging tyre degradation, fuel load, and sector deltas.</p>
            </motion.div>

            <motion.div
              className="sc-why-card surface-level-1"
              variants={cardHoverVariants}
              initial="rest"
              whileHover="hover"
            >
              <span className="font-telemetry text-micro text-lime">02 · DRIVER PHYSIOLOGY</span>
              <h3 className="text-h3 font-display">What the Driver Felt</h3>
              <p className="text-body-sm">Prosodic acoustic stress detection capturing cockpit anxiety and fatigue indicators.</p>
            </motion.div>

            <motion.div
              className="sc-why-card surface-level-1"
              variants={cardHoverVariants}
              initial="rest"
              whileHover="hover"
            >
              <span className="font-telemetry text-micro text-lime">03 · COCKPIT COMMUNICATIONS</span>
              <h3 className="text-h3 font-display">What the Radio Said</h3>
              <p className="text-body-sm">Whisper ASR speech transcription aligned to exact lap timestamp markers.</p>
            </motion.div>

            <motion.div
              className="sc-why-card surface-level-1"
              variants={cardHoverVariants}
              initial="rest"
              whileHover="hover"
            >
              <span className="font-telemetry text-micro text-lime">04 · RACE ENGINEERING</span>
              <h3 className="text-h3 font-display">What the Engineer Should Do</h3>
              <p className="text-body-sm">Automated evidence-backed recommendations for apex entry & pit strategy.</p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Section Divider Motif */}
      <div className="sc-section-divider">
        <div className="sc-section-divider__line" />
        <div className="sc-section-divider__node font-telemetry">PRODUCT WORKSTATION</div>
        <div className="sc-section-divider__line" />
      </div>

      {/* ── 09 — COMMAND CONSOLE PREVIEW ────────────────────────────── */}
      <section className="sc-section" id="console-preview">
        <div className="sc-landing__container text-center">
          <span className="text-label text-lime">09 · PRODUCT WORKSTATION</span>
          <h2 className="text-h1 font-display">The Live Race Engineering Command Console</h2>
          <p className="text-body-lg max-w-2xl mx-auto mb-8">
            Experience the high-density workstation designed for race engineers under live operational conditions.
          </p>

          <div className="sc-console-preview-btn">
            <Button variant="primary" size="lg" onClick={onEnterConsole}>
              Launch Live Command Console <Gauge size={18} />
            </Button>
          </div>
        </div>
      </section>

      {/* ── 10 — FINAL CTA ───────────────────────────────────────────── */}
      <section className="sc-section sc-section--final" id="final-cta">
        <div className="sc-landing__container text-center">
          <h2 className="text-display-giant font-display">
            Listen deeper.<br />
            <span className="text-gradient-lime">Drive faster.</span>
          </h2>
          <p className="text-body-lg max-w-xl mx-auto my-8">
            Know what the driver can't see. Connect your race telemetry and driver radio feeds today.
          </p>
          <Button variant="primary" size="lg" onClick={onEnterConsole}>
            Enter Silent Co-Driver Console <ArrowRight size={18} />
          </Button>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
