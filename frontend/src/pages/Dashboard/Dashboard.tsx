import React, { useCallback, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  ComposedChart,
  ReferenceLine,
} from 'recharts';
import { Gauge, Radio, Flag, ShieldAlert, Cpu } from 'lucide-react';
import AudioUpload from '../../features/audio-upload/AudioUpload';
import DriverStateCard from '../../features/driver-state/DriverStateCard';
import TranscriptTimeline from '../../features/driver-state/TranscriptTimeline';
import RaceInsightsFeed from '../../features/race-insights/RaceInsightsFeed';
import Button from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import SignalIndicator from '../../components/ui/SignalIndicator';
import AnimatedNumber from '../../components/ui/AnimatedNumber';
import { EmptyState } from '../../components/ui/State';
import type {
  AlignedLapEmotion,
  TranscriptSegment,
} from '../../types';
import { useAnalysisSession } from '../../state/AnalysisSessionContext';
import {
  correlationReason,
  formatCorrelation,
  formatLapTime,
  getDriverStateView,
} from '../../features/analysis/analysisView';
import './Dashboard.css';

export const Dashboard: React.FC = () => {
  const {
    audioSession,
    audioPlaybackUrl,
    telemetrySession,
    analysis,
    analysisError,
    telemetryError,
    raceId,
    driverName,
    telemetryVerification,
    isTelemetryUploading,
    isAnalyzing,
    status,
    setRaceId,
    setDriverName,
    setAudioProgress,
    setAudioPlaybackUrl,
    completeAudioUpload,
    resetAudio,
    uploadTelemetry,
    resetTelemetry,
    startAnalysis,
  } = useAnalysisSession();
  const [telemetryFile, setTelemetryFile] = useState<File | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [seekTrigger, setSeekTrigger] = useState<{ time: number } | null>(null);
  const telemetryFileInputRef = useRef<HTMLInputElement>(null);

  const handleAudioReset = useCallback(() => {
    resetAudio();
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);
  }, [resetAudio]);

  const handleTelemetryUpload = useCallback(async () => {
    if (!telemetryFile) return;
    const uploaded = await uploadTelemetry(telemetryFile);
    if (uploaded) {
      setTelemetryFile(null);
      if (telemetryFileInputRef.current) telemetryFileInputRef.current.value = '';
    }
  }, [telemetryFile, uploadTelemetry]);

  const handleResetTelemetry = useCallback(() => {
    resetTelemetry();
    setTelemetryFile(null);
    if (telemetryFileInputRef.current) telemetryFileInputRef.current.value = '';
  }, [resetTelemetry]);

  const alignedLaps: AlignedLapEmotion[] = analysis?.aligned_laps ?? [];
  const chartData = alignedLaps.map((lap) => ({
    lap: `LAP ${lap.lap_number}`,
    lapTime: lap.lap_time_seconds,
    delta: lap.delta_to_best,
    stress: +(lap.stress_level * 100).toFixed(1),
    fatigue: +(lap.fatigue_level * 100).toFixed(1),
  }));
  const bestLap = chartData.length > 0 ? Math.min(...chartData.map((entry) => entry.lapTime)) : null;
  const lapCount = analysis?.aligned_laps.length ?? 0;
  const driverStateView = getDriverStateView(analysis);
  const dominantEmotion = analysis?.summary.dominant_state;
  const stressCorrelation = analysis?.correlations.stress_vs_lap_delta;
  const fatigueCorrelation = analysis?.correlations.fatigue_vs_lap_delta;
  const transcriptSegments: TranscriptSegment[] = analysis?.transcription?.segments ?? [];
  const insights = analysis?.insights ?? [];
  const hasAlignedLapData = chartData.length > 0;
  const chartReady = Boolean(analysis) && hasAlignedLapData;
  const audioReady = Boolean(audioSession?.file_id);
  const telemetryReady = Boolean(telemetrySession?.race_id) && telemetryVerification === 'verified';
  const telemetryLocked = Boolean(telemetrySession);
  const isTelemetryVerifying = telemetryVerification === 'checking';
  const analysisReady = audioReady && telemetryReady;
  const sessionStatusLabel = status === 'analysis_complete'
    ? 'ANALYSIS COMPLETE'
    : status === 'analyzing'
      ? 'ANALYZING SESSION'
      : status === 'analysis_failed'
        ? 'ANALYSIS FAILED'
        : status === 'telemetry_ready'
          ? 'TELEMETRY READY'
          : status === 'radio_connected'
            ? 'RADIO CONNECTED'
            : status === 'uploading_audio'
              ? 'UPLOADING RADIO'
              : status === 'uploading_telemetry' || status === 'verifying_telemetry'
                ? 'PREPARING TELEMETRY'
                : 'WAITING FOR REAL DATA';

  return (
    <div className="sc-console">
      <div className="sc-console__bg-grid" />
      <div className="sc-console__ambient-glow" />

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
                  {telemetrySession?.race_id ?? 'NO RACE SESSION'}
                </span>
                <span className="sc-console__lap-tag font-telemetry">
                  {analysis ? `${sessionStatusLabel} · ${lapCount} LAPS` : sessionStatusLabel}
                </span>
              </div>
              <p className="sc-console__subtitle text-caption">AI-POWERED RACE ENGINEERING WORKSTATION</p>
            </div>
          </div>

          <SignalIndicator
            status={analysis ? 'active' : isAnalyzing ? 'processing' : analysisError ? 'idle' : analysisReady ? 'active' : 'idle'}
            label={sessionStatusLabel}
          />
        </div>

        <div className="sc-console__hero-metrics">
          <div className="sc-hero-metric">
            <span className="text-label">PACE</span>
            <span className="sc-hero-metric__val font-telemetry" style={{ color: 'var(--color-brand-lime)' }}>
              {bestLap !== null ? formatLapTime(bestLap) : '--:--.---'}
            </span>
            <span className="sc-hero-metric__delta font-telemetry text-lime">
              {analysis ? 'BEST ANALYZED LAP' : telemetryReady ? 'AWAITING ANALYSIS' : 'AWAITING TELEMETRY'}
            </span>
          </div>

          <div className="sc-hero-metric">
            <span className="text-label">STRESS</span>
            <span className="sc-hero-metric__val font-telemetry" style={{ color: 'var(--color-driver-stressed)' }}>
              {analysis && analysis.driver_states.length > 0 ? (
                <AnimatedNumber value={analysis.overall_stress * 100} decimals={0} suffix="%" />
              ) : (
                '--'
              )}
            </span>
            <span className="sc-hero-metric__delta font-telemetry" style={{ color: 'var(--color-driver-stressed)' }}>
              {analysis ? 'REAL DRIVER STATE' : telemetryReady ? 'AWAITING ANALYSIS' : 'AWAITING TELEMETRY'}
            </span>
          </div>

          <div className="sc-hero-metric">
            <span className="text-label">FATIGUE</span>
            <span className="sc-hero-metric__val font-telemetry" style={{ color: 'var(--color-driver-fatigue)' }}>
              {analysis && analysis.driver_states.length > 0 ? (
                <AnimatedNumber value={analysis.overall_fatigue * 100} decimals={0} suffix="%" />
              ) : (
                '--'
              )}
            </span>
            <span className="sc-hero-metric__delta font-telemetry" style={{ color: 'var(--color-text-muted)' }}>
              {analysis ? 'REAL DRIVER STATE' : telemetryReady ? 'AWAITING ANALYSIS' : 'AWAITING TELEMETRY'}
            </span>
          </div>

          <div className="sc-hero-metric">
            <span className="text-label">LAPS</span>
            <span className="sc-hero-metric__val font-telemetry" style={{ color: 'var(--color-text-primary)' }}>
              {analysis ? lapCount : telemetrySession?.laps_received ?? '--'}
            </span>
            <span className="sc-hero-metric__delta font-telemetry" style={{ color: 'var(--color-text-muted)' }}>
              {analysis ? 'ALIGNED WITH RADIO' : telemetryReady ? 'TELEMETRY INGESTED' : 'AWAITING TELEMETRY'}
            </span>
          </div>
        </div>
      </motion.header>

      <div className="sc-console__grid">
        <div className="sc-console__col-main">
          <section className="sc-console__section" id="radio-feed">
            <AudioUpload
              onUploadComplete={completeAudioUpload}
              initialUpload={audioSession}
              initialPlaybackUrl={audioPlaybackUrl}
              isPlaying={isPlaying}
              setIsPlaying={setIsPlaying}
              currentTime={currentTime}
              setCurrentTime={setCurrentTime}
              duration={duration}
              setDuration={setDuration}
              seekTrigger={seekTrigger}
              onFileSelect={() => undefined}
              onReset={handleAudioReset}
              onProgressChange={setAudioProgress}
              onPlaybackUrlChange={setAudioPlaybackUrl}
            />
          </section>

          <motion.section
            className="sc-console__section sc-telemetry-card"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.08 }}
          >
            <div className="sc-telemetry-card__header">
              <div className="sc-telemetry-card__title-group">
                <div className="sc-telemetry-card__icon-badge">
                  <Gauge size={16} className="text-lime" />
                </div>
                <div>
                  <h3 className="text-h4 font-display" style={{ margin: 0 }}>
                    Race Telemetry Console
                  </h3>
                  <span className="text-micro font-telemetry">REAL LAP CSV INGESTION</span>
                </div>
              </div>
              <SignalIndicator
                status={telemetryReady ? 'active' : 'idle'}
                label={telemetryReady ? 'TELEMETRY INGESTED' : 'UPLOAD RACE TELEMETRY'}
              />
            </div>

            <div className="sc-telemetry-card__grid">
              <Input
                label="Race Session ID"
                value={raceId}
                onChange={(event) => setRaceId(event.target.value)}
                placeholder="race-2026-08-15-myclub"
                disabled={telemetryLocked || isTelemetryUploading}
              />
              <Input
                label="Driver Name"
                value={driverName}
                onChange={(event) => setDriverName(event.target.value)}
                placeholder="Enter driver name"
                disabled={telemetryLocked || isTelemetryUploading}
              />
            </div>

            <div className="sc-telemetry-card__file">
              <label className="text-label" htmlFor="lap-telemetry-csv">Lap Telemetry CSV</label>
              <input
                id="lap-telemetry-csv"
                ref={telemetryFileInputRef}
                type="file"
                accept=".csv,text/csv"
                onChange={(event) => setTelemetryFile(event.target.files?.[0] ?? null)}
                className="sc-telemetry-card__input"
                disabled={telemetryLocked || isTelemetryUploading}
              />
              <p className="text-caption" style={{ margin: '6px 0 0' }}>
                Upload a real CSV with lap, lap_time, and start_time columns. No synthetic telemetry is generated.
              </p>
              {telemetryFile && (
                <p className="text-micro font-telemetry text-lime" style={{ margin: '6px 0 0' }}>
                  Selected file: {telemetryFile.name}
                </p>
              )}
            </div>

            <div className="sc-telemetry-card__actions">
              <Button
                variant="secondary"
                size="md"
                isLoading={isTelemetryUploading}
                disabled={telemetryLocked || !telemetryFile || !driverName.trim() || !raceId.trim()}
                onClick={handleTelemetryUpload}
              >
                {telemetryLocked ? 'Telemetry already ingested' : 'Upload race telemetry'}
              </Button>
              <Button
                variant="primary"
                size="md"
                isLoading={isAnalyzing}
                disabled={!analysisReady || isAnalyzing || isTelemetryVerifying}
                onClick={startAnalysis}
              >
                Start analysis
              </Button>
              <Button
                variant="ghost"
                size="md"
                disabled={!telemetrySession && !telemetryFile}
                onClick={handleResetTelemetry}
              >
                Reset telemetry
              </Button>
            </div>

            <div className="sc-telemetry-card__status">
              {telemetrySession && telemetryVerification === 'verified' ? (
                <div className="sc-telemetry-card__status-block">
                  <span className="sc-telemetry-card__status-title text-micro font-telemetry">REAL TELEMETRY READY</span>
                  <span className="sc-telemetry-card__status-body text-body-sm">
                    {telemetrySession.laps_received} laps ingested for {telemetrySession.driver_name} in session {telemetrySession.race_id}.
                  </span>
                  <span className="sc-telemetry-card__status-note text-caption">
                    {telemetrySession.message} Uploaded from {telemetrySession.source_filename}.
                  </span>
                </div>
              ) : telemetrySession ? (
                <div className="sc-telemetry-card__status-block">
                  <span className="sc-telemetry-card__status-title text-micro font-telemetry">
                    {isTelemetryVerifying ? 'VERIFYING SAVED TELEMETRY' : 'TELEMETRY VERIFICATION REQUIRED'}
                  </span>
                  <span className="sc-telemetry-card__status-body text-body-sm">
                    Analysis will remain disabled until race session {telemetrySession.race_id} is confirmed by the backend.
                  </span>
                </div>
              ) : (
                <EmptyState
                  icon={<Gauge size={24} />}
                  title="Upload race telemetry"
                  description="Provide a real lap CSV before analysis can run."
                />
              )}
            </div>

            {telemetryError && (
              <div className="sc-telemetry-card__error" role="alert">
                <ShieldAlert size={14} />
                <span>{telemetryError}</span>
              </div>
            )}
          </motion.section>

          {isAnalyzing && (
            <motion.section
              className="sc-console__section sc-loading-banner"
              aria-live="polite"
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

          {analysisError && (
            <section className="sc-console__section sc-error-banner" role="alert">
              <span className="text-h4 font-display" style={{ color: 'var(--color-driver-critical)' }}>
                <ShieldAlert size={16} style={{ display: 'inline', marginRight: 8 }} />
                Analysis Pipeline Exception: {analysisError}
              </span>
            </section>
          )}

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
                  <h3 className="text-h4 font-display" style={{ margin: 0 }}>
                    Lap Performance vs. Driver Emotional State
                  </h3>
                  <span className="text-micro font-telemetry">MULTI-AXIS TELEMETRY CORRELATION ENGINE</span>
                </div>
              </div>
              <div className="sc-chart-card__tags font-telemetry">
                <span
                  className="sc-chart-tag"
                  style={{ color: 'var(--color-brand-lime)', borderColor: 'rgba(200, 255, 61, 0.3)' }}
                >
                  {bestLap !== null ? `BEST: ${bestLap.toFixed(3)}s` : 'BEST: —'}
                </span>
                <span className="sc-chart-tag" style={{ color: 'var(--color-text-primary)' }}>
                  STRESS {formatCorrelation(stressCorrelation)}
                  {stressCorrelation?.pearson_r === null ? ` · ${correlationReason(stressCorrelation)}` : ''}
                </span>
                <span className="sc-chart-tag" style={{ color: 'var(--color-text-primary)' }}>
                  FATIGUE {formatCorrelation(fatigueCorrelation)}
                  {fatigueCorrelation?.pearson_r === null ? ` · ${correlationReason(fatigueCorrelation)}` : ''}
                </span>
                <span className="sc-chart-tag" style={{ color: 'var(--color-text-muted)' }}>
                  TREND {analysis?.fatigue_trend?.trend ?? '—'}
                </span>
              </div>
            </div>

            <div className="sc-chart-container">
              {isAnalyzing ? (
                <EmptyState
                  icon={<Cpu size={32} />}
                  title="Analyzing telemetry"
                  description="Waiting for the backend to finish aligning lap timing with the uploaded radio session."
                />
              ) : chartReady ? (
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
                    <XAxis
                      dataKey="lap"
                      stroke="var(--color-text-muted)"
                      fontSize={11}
                      tickLine={false}
                      fontFamily="JetBrains Mono"
                    />
                    <YAxis
                      yAxisId="time"
                      stroke="var(--color-text-muted)"
                      fontSize={11}
                      domain={['dataMin - 0.5', 'dataMax + 0.5']}
                      tickLine={false}
                      fontFamily="JetBrains Mono"
                    />
                    <YAxis
                      yAxisId="pct"
                      orientation="right"
                      stroke="var(--color-text-muted)"
                      fontSize={10}
                      domain={[0, 100]}
                      unit="%"
                      tickLine={false}
                      fontFamily="JetBrains Mono"
                    />
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
                    {bestLap !== null && (
                      <ReferenceLine
                        yAxisId="time"
                        y={bestLap}
                        stroke="var(--color-brand-lime)"
                        strokeDasharray="3 3"
                        label={{
                          value: 'BEST PACE',
                          fill: 'var(--color-brand-lime)',
                          fontSize: 10,
                          fontFamily: 'JetBrains Mono',
                        }}
                      />
                    )}
                    <Area
                      yAxisId="pct"
                      type="monotone"
                      dataKey="stress"
                      fill="url(#scStressGrad)"
                      stroke="var(--color-driver-stressed)"
                      strokeWidth={2}
                      name="Stress %"
                      dot={false}
                    />
                    <Area
                      yAxisId="pct"
                      type="monotone"
                      dataKey="fatigue"
                      fill="url(#scFatigueGrad)"
                      stroke="var(--color-driver-fatigue)"
                      strokeWidth={2}
                      name="Fatigue %"
                      dot={false}
                    />
                    <Line
                      yAxisId="time"
                      type="monotone"
                      dataKey="lapTime"
                      stroke="var(--color-brand-lime)"
                      strokeWidth={3}
                      name="Lap Time (s)"
                      dot={{ fill: 'var(--color-brand-lime)', r: 4 }}
                      activeDot={{ r: 6, fill: '#fff', stroke: 'var(--color-brand-lime)', strokeWidth: 2 }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              ) : !telemetryReady ? (
                <EmptyState
                  icon={<Gauge size={32} />}
                  title="Upload race telemetry"
                  description="No telemetry is available yet. Upload a real lap CSV to unlock analysis."
                />
              ) : !analysis ? (
                <EmptyState
                  icon={<Cpu size={32} />}
                  title="Awaiting analysis"
                  description="Audio and telemetry are ready. Start analysis to generate the alignment, correlation, and insight views."
                />
              ) : (
                <EmptyState
                  icon={<Gauge size={32} />}
                  title="Insufficient aligned data"
                  description="The backend returned no aligned laps for this session."
                />
              )}
            </div>
          </motion.section>

          <section className="sc-console__section">
            <TranscriptTimeline
              segments={transcriptSegments}
              states={analysis?.driver_states ?? []}
              currentTime={currentTime}
              onSegmentClick={(time) => setSeekTrigger({ time })}
            />
          </section>
        </div>

        <div className="sc-console__col-side">
          <section className="sc-console__section" id="driver-state">
            <DriverStateCard
              stressScore={driverStateView.stressScore}
              fatigueScore={driverStateView.fatigueScore}
              calmScore={driverStateView.calmScore}
              dominantEmotion={dominantEmotion}
              confidence={driverStateView.confidence}
              processingTime={analysis?.processing_time_ms}
            />
          </section>

          <section className="sc-console__section" id="ai-intelligence">
            <RaceInsightsFeed insights={insights} />
          </section>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
