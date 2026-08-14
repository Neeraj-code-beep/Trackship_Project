import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, ComposedChart,
  ReferenceLine
} from 'recharts';
import {
  Gauge, Radio, Flag, ShieldAlert, Cpu
} from 'lucide-react';
import AudioUpload from '../../features/audio-upload/AudioUpload';
import DriverStateCard from '../../features/driver-state/DriverStateCard';
import TranscriptTimeline from '../../features/driver-state/TranscriptTimeline';
import RaceInsightsFeed from '../../features/race-insights/RaceInsightsFeed';
import SignalIndicator from '../../components/ui/SignalIndicator';
import AnimatedNumber from '../../components/ui/AnimatedNumber';
import { runAnalysis, ingestLaps, normalizeError } from '../../services/api';
import type {
  AudioUploadResponse, AnalysisResponse, AlignedLapEmotion,
  EmotionLabel
} from '../../types';
import './Dashboard.css';

// Demo lap telemetry for first-use experience
const DEMO_LAPS = [
  { lap_number: 1, lap_time_seconds: 92.456, sector_1: 28.3, sector_2: 34.1, sector_3: 30.056, timestamp: null, tyre_compound: 'soft', fuel_load_kg: 105 },
  { lap_number: 2, lap_time_seconds: 90.123, sector_1: 27.8, sector_2: 33.5, sector_3: 28.823, timestamp: null, tyre_compound: 'soft', fuel_load_kg: 102 },
  { lap_number: 3, lap_time_seconds: 89.876, sector_1: 27.6, sector_2: 33.2, sector_3: 29.076, timestamp: null, tyre_compound: 'soft', fuel_load_kg: 99 },
  { lap_number: 4, lap_time_seconds: 91.234, sector_1: 28.1, sector_2: 34.0, sector_3: 29.134, timestamp: null, tyre_compound: 'soft', fuel_load_kg: 96 },
  { lap_number: 5, lap_time_seconds: 90.567, sector_1: 27.9, sector_2: 33.7, sector_3: 28.967, timestamp: null, tyre_compound: 'soft', fuel_load_kg: 93 },
  { lap_number: 6, lap_time_seconds: 92.890, sector_1: 28.5, sector_2: 34.4, sector_3: 29.990, timestamp: null, tyre_compound: 'medium', fuel_load_kg: 90 },
  { lap_number: 7, lap_time_seconds: 91.012, sector_1: 28.0, sector_2: 33.8, sector_3: 29.212, timestamp: null, tyre_compound: 'medium', fuel_load_kg: 87 },
  { lap_number: 8, lap_time_seconds: 93.456, sector_1: 28.9, sector_2: 34.6, sector_3: 29.956, timestamp: null, tyre_compound: 'medium', fuel_load_kg: 84 },
];

const RACE_ID = 'demo-race-001';

function formatLapTime(seconds: number): string {
  if (!seconds || isNaN(seconds)) return '--:--.---';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, '0')}:${s.toFixed(3).padStart(6, '0')}`;
}

export const Dashboard: React.FC = () => {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Audio Playback Shared State
  const [, setAudioFile] = useState<File | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [seekTrigger, setSeekTrigger] = useState<{ time: number } | null>(null);

  const handleUploadComplete = useCallback(async (response: AudioUploadResponse) => {
    setIsAnalyzing(true);
    setError(null);
    setAnalysis(null);

    try {
      // Ingest demo lap telemetry
      await ingestLaps({
        race_id: RACE_ID,
        driver_name: 'Demo Driver',
        laps: DEMO_LAPS,
      });

      // Execute full analysis pipeline
      const result = await runAnalysis({
        file_id: response.file_id,
        race_id: RACE_ID,
      });

      setAnalysis(result);
    } catch (err: any) {
      setError(normalizeError(err));
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  // Format chart data
  const chartData = (analysis?.aligned_laps?.length ? analysis.aligned_laps : DEMO_LAPS.map(l => ({
    lap_number: l.lap_number,
    lap_time_seconds: l.lap_time_seconds,
    delta_to_best: +(l.lap_time_seconds - 89.876).toFixed(3),
    dominant_emotion: (l.lap_number === 7 || l.lap_number === 8 ? 'stressed' : 'calm') as EmotionLabel,
    stress_level: l.lap_number === 7 ? 0.72 : l.lap_number === 8 ? 0.65 : 0.22,
    fatigue_level: 0.15 + l.lap_number * 0.02,
  }))).map((lap: AlignedLapEmotion) => ({
    lap: `LAP ${lap.lap_number}`,
    lapTime: lap.lap_time_seconds,
    delta: lap.delta_to_best,
    stress: +(lap.stress_level * 100).toFixed(1),
    fatigue: +(lap.fatigue_level * 100).toFixed(1),
  }));

  const bestLap = chartData.length > 0
    ? Math.min(...chartData.map((d: { lapTime: number }) => d.lapTime))
    : 89.876;

  // Determine dominant overall emotion
  const dominantEmotion: EmotionLabel | undefined = analysis?.driver_states?.length
    ? ((): EmotionLabel => {
        const counts: Record<string, number> = {};
        analysis.driver_states.forEach(s => {
          counts[s.dominant_emotion] = (counts[s.dominant_emotion] || 0) + 1;
        });
        return (Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] as EmotionLabel) || 'neutral';
      })()
    : undefined;

  const avgProbs = analysis?.driver_states?.length
    ? {
        calm: analysis.driver_states.reduce((s, d) => s + d.probabilities.calm, 0) / analysis.driver_states.length,
        stressed: analysis.driver_states.reduce((s, d) => s + d.probabilities.stressed, 0) / analysis.driver_states.length,
        neutral: analysis.driver_states.reduce((s, d) => s + d.probabilities.neutral, 0) / analysis.driver_states.length,
        tired: analysis.driver_states.reduce((s, d) => s + d.probabilities.tired, 0) / analysis.driver_states.length,
      }
    : undefined;

  return (
    <div className="sc-console">
      {/* Background Telemetry Grid & Ambient Glow */}
      <div className="sc-console__bg-grid" />
      <div className="sc-console__ambient-glow" />

      {/* Command Center Hero */}
      <motion.header
        className="sc-console__hero"
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
      >
        <div className="sc-console__hero-top">
          <div className="sc-console__brand">
            <div className="sc-console__logo-icon">
              <Radio size={20} />
            </div>
            <div>
              <div className="sc-console__brand-row">
                <h1 className="sc-console__title text-h2 font-display">SILENT CO-DRIVER</h1>
                <span className="sc-console__session-badge font-telemetry">
                  <Flag size={10} style={{ display: 'inline', marginRight: 4 }} />
                  BAHRAIN GP · PRACTICE 2
                </span>
                <span className="sc-console__lap-tag font-telemetry">LAP 17 / 57</span>
              </div>
              <p className="sc-console__subtitle text-caption">AI-POWERED RACE ENGINEERING WORKSTATION</p>
            </div>
          </div>

          <SignalIndicator
            status={analysis ? 'active' : isAnalyzing ? 'processing' : 'active'}
            label={analysis ? 'TELEMETRY LIVE' : isAnalyzing ? 'ANALYZING SPEECH' : 'SESSION STANDBY ●'}
          />
        </div>

        {/* Hero Telemetry Metric Strip */}
        <div className="sc-console__hero-metrics">
          <div className="sc-hero-metric">
            <span className="text-label">Pace Time</span>
            <span className="sc-hero-metric__val font-telemetry" style={{ color: 'var(--color-brand-lime)' }}>
              {formatLapTime(bestLap)}
            </span>
            <span className="sc-hero-metric__delta font-telemetry text-lime">
              -0.345s BEST LAP
            </span>
          </div>

          <div className="sc-hero-metric">
            <span className="text-label">Driver Stress</span>
            <span className="sc-hero-metric__val font-telemetry" style={{ color: 'var(--color-driver-stressed)' }}>
              {analysis && analysis.driver_states?.length > 0 ? (
                <AnimatedNumber value={analysis.overall_stress * 100} decimals={0} suffix="%" />
              ) : (
                '--'
              )}
            </span>
            <span className="sc-hero-metric__delta font-telemetry" style={{ color: 'var(--color-driver-stressed)' }}>
              {analysis && analysis.driver_states?.length > 0 ? '+12% TURN 7 ENTRY' : '--'}
            </span>
          </div>

          <div className="sc-hero-metric">
            <span className="text-label">Fatigue Index</span>
            <span className="sc-hero-metric__val font-telemetry" style={{ color: 'var(--color-driver-fatigue)' }}>
              {analysis && analysis.driver_states?.length > 0 ? (
                <AnimatedNumber value={analysis.overall_fatigue * 100} decimals={0} suffix="%" />
              ) : (
                '--'
              )}
            </span>
            <span className="sc-hero-metric__delta font-telemetry" style={{ color: 'var(--color-text-muted)' }}>
              {analysis && analysis.driver_states?.length > 0 ? 'NOMINAL STINT' : '--'}
            </span>
          </div>

          <div className="sc-hero-metric">
            <span className="text-label">Top Speed</span>
            <span className="sc-hero-metric__val font-telemetry" style={{ color: 'var(--color-text-primary)' }}>
              312.4 <span className="sc-hero-metric__unit">KM/H</span>
            </span>
            <span className="sc-hero-metric__delta font-telemetry" style={{ color: 'var(--color-text-muted)' }}>
              SECTOR 1 · DRS ACTIVE
            </span>
          </div>
        </div>
      </motion.header>

      {/* Main Asymmetrical Grid Layout */}
      <div className="sc-console__grid">
        {/* Left Primary Column (65%) */}
        <div className="sc-console__col-main">
          {/* Audio Upload / Radio Console Module */}
          <section className="sc-console__section" id="radio-feed">
            <AudioUpload
              onUploadComplete={handleUploadComplete}
              isPlaying={isPlaying}
              setIsPlaying={setIsPlaying}
              currentTime={currentTime}
              setCurrentTime={setCurrentTime}
              duration={duration}
              setDuration={setDuration}
              seekTrigger={seekTrigger}
              onFileSelect={setAudioFile}
            />
          </section>

          {/* Analysis Loading State */}
          {isAnalyzing && (
            <motion.section
              className="sc-console__section sc-loading-banner"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
            >
              <Cpu size={24} className="sc-spin-anim text-lime" />
              <div className="sc-loading-text">
                <span className="text-h4 font-display text-lime">
                  Executing AI Speech & Emotion Intelligence Pipeline...
                </span>
                <span className="text-caption font-telemetry">
                  Transcribing radio audio with Whisper ASR, extracting prosodic acoustic features, and aligning lap timestamps.
                </span>
              </div>
            </motion.section>
          )}

          {/* Error Banner */}
          {error && (
            <section className="sc-console__section sc-error-banner">
              <span className="text-h4 font-display" style={{ color: 'var(--color-driver-critical)' }}>
                <ShieldAlert size={16} style={{ display: 'inline', marginRight: 8 }} />
                Analysis Pipeline Exception: {error}
              </span>
            </section>
          )}

          {/* Recharts Telemetry Graph */}
          <motion.section
            id="telemetry"
            className="sc-console__section sc-chart-card"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.1 }}
          >
            <div className="sc-chart-card__header">
              <div className="sc-chart-card__title-group">
                <div className="sc-chart-card__icon-badge">
                  <Gauge size={16} className="text-lime" />
                </div>
                <div>
                  <h3 className="text-h4 font-display" style={{ margin: 0 }}>Lap Performance vs. Driver Emotional State</h3>
                  <span className="text-micro font-telemetry">MULTI-AXIS TELEMETRY CORRELATION ENGINE</span>
                </div>
              </div>
              <div className="sc-chart-card__tags font-telemetry">
                <span className="sc-chart-tag" style={{ color: 'var(--color-brand-lime)', borderColor: 'rgba(200, 255, 61, 0.3)' }}>
                  BEST: {bestLap.toFixed(3)}s
                </span>
                <span className="sc-chart-tag" style={{ color: 'var(--color-text-primary)' }}>LAP TIME (S)</span>
                <span className="sc-chart-tag" style={{ color: 'var(--color-driver-stressed)' }}>STRESS %</span>
                <span className="sc-chart-tag" style={{ color: 'var(--color-driver-fatigue)' }}>FATIGUE %</span>
              </div>
            </div>

            <div className="sc-chart-container">
              <ResponsiveContainer width="100%" height={320}>
                <ComposedChart data={chartData} margin={{ top: 15, right: 15, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="scStressGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--color-driver-stressed)" stopOpacity={0.15} />
                      <stop offset="100%" stopColor="var(--color-driver-stressed)" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="scFatigueGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--color-driver-fatigue)" stopOpacity={0.15} />
                      <stop offset="100%" stopColor="var(--color-driver-fatigue)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="2 4" stroke="rgba(255, 255, 255, 0.06)" />
                  <XAxis dataKey="lap" stroke="var(--color-text-muted)" fontSize={11} tickLine={false} fontFamily="JetBrains Mono" />
                  <YAxis yAxisId="time" stroke="var(--color-text-muted)" fontSize={11} domain={['dataMin - 0.5', 'dataMax + 0.5']} tickLine={false} fontFamily="JetBrains Mono" />
                  <YAxis yAxisId="pct" orientation="right" stroke="var(--color-text-muted)" fontSize={10} domain={[0, 100]} unit="%" tickLine={false} fontFamily="JetBrains Mono" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(11, 14, 18, 0.94)',
                      backdropFilter: 'blur(12px)',
                      borderColor: 'rgba(255, 255, 255, 0.12)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: 12,
                      fontFamily: 'JetBrains Mono',
                      color: 'var(--color-text-primary)',
                      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.7)',
                    }}
                  />
                  <ReferenceLine yAxisId="time" y={bestLap} stroke="var(--color-brand-lime)" strokeDasharray="3 3" label={{ value: 'BEST PACE', fill: 'var(--color-brand-lime)', fontSize: 10, fontFamily: 'JetBrains Mono' }} />
                  <Area yAxisId="pct" type="monotone" dataKey="stress" fill="url(#scStressGrad)" stroke="var(--color-driver-stressed)" strokeWidth={2} name="Stress %" dot={false} />
                  <Area yAxisId="pct" type="monotone" dataKey="fatigue" fill="url(#scFatigueGrad)" stroke="var(--color-driver-fatigue)" strokeWidth={2} name="Fatigue %" dot={false} />
                  <Line yAxisId="time" type="monotone" dataKey="lapTime" stroke="var(--color-brand-lime)" strokeWidth={3} name="Lap Time (s)" dot={{ fill: 'var(--color-brand-lime)', r: 4 }} activeDot={{ r: 6, fill: '#fff', stroke: 'var(--color-brand-lime)', strokeWidth: 2 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </motion.section>

          {/* Transcript Timeline */}
          <section className="sc-console__section">
            <TranscriptTimeline
              segments={analysis ? (analysis.transcription?.segments || []) : [
                { start_time: 14.32, end_time: 18.5, text: "Rear is sliding through Turn 7 entry, losing momentum.", confidence: 0.95, speaker: "DRIVER 01" },
                { start_time: 28.71, end_time: 32.1, text: "Need more front wing angle for sector 2.", confidence: 0.92, speaker: "DRIVER 01" },
                { start_time: 42.05, end_time: 46.8, text: "Pace is good, tyres holding up fine.", confidence: 0.96, speaker: "DRIVER 01" },
              ]}
              currentTime={currentTime}
              onSegmentClick={(time) => setSeekTrigger({ time })}
            />
          </section>
        </div>

        {/* Right AI & Telemetry Sidebar (35%) */}
        <div className="sc-console__col-side">
          {/* Driver State Spectrum Card */}
          <section className="sc-console__section" id="driver-state">
            <DriverStateCard
              overallStress={analysis && analysis.driver_states?.length > 0 ? analysis.overall_stress : null}
              overallFatigue={analysis && analysis.driver_states?.length > 0 ? analysis.overall_fatigue : null}
              dominantEmotion={dominantEmotion}
              probabilities={avgProbs}
              processingTime={analysis?.processing_time_ms}
            />
          </section>

          {/* AI Race Engineer Insights Feed */}
          <section className="sc-console__section" id="ai-intelligence">
            <RaceInsightsFeed insights={analysis ? (analysis.insights || []) : [
              {
                id: 'ins-01',
                severity: 'critical',
                category: 'CORNERING DEGRADATION',
                message: 'Elevated stress (72%) detected on Turn 7 entry correlated with +0.42s pace loss.',
                lap_number: 7,
                timestamp: null,
                data: { recommendation: 'Instruct driver to brake 5m earlier into Turn 7 to stabilize rear axle.' }
              },
              {
                id: 'ins-02',
                severity: 'warning',
                category: 'TYRE FATIGUE TREND',
                message: 'Fatigue index rising by 2.1% per lap on Soft compound stint.',
                lap_number: 8,
                timestamp: null,
                data: { recommendation: 'Plan Box on Lap 12 for Medium compound tyres.' }
              }
            ]} />
          </section>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
