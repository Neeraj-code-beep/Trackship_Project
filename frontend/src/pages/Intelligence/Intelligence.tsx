import { motion } from 'framer-motion';
import { Activity, AudioLines, BrainCircuit, Gauge, ShieldAlert, Sparkles } from 'lucide-react';
import DriverStateCard from '../../features/driver-state/DriverStateCard';
import TranscriptTimeline from '../../features/driver-state/TranscriptTimeline';
import RaceInsightsFeed from '../../features/race-insights/RaceInsightsFeed';
import SignalIndicator from '../../components/ui/SignalIndicator';
import { EmptyState } from '../../components/ui/State';
import { useAnalysisSession } from '../../state/AnalysisSessionContext';
import {
  correlationReason,
  formatCorrelation,
  getDriverStateView,
} from '../../features/analysis/analysisView';
import type { CorrelationResult } from '../../types';
import './Intelligence.css';

function CorrelationCard({ label, result }: { label: string; result: CorrelationResult }) {
  const available = result.pearson_r !== null;
  return (
    <div className={`sc-intelligence__correlation ${available ? '' : 'sc-intelligence__correlation--empty'}`}>
      <span className="text-label">{label}</span>
      <strong className="font-telemetry">{formatCorrelation(result)}</strong>
      <span className="text-caption">
        {available
          ? `${result.sample_size} aligned laps · ${result.metric}`
          : `${correlationReason(result)} · ${result.sample_size} aligned samples`}
      </span>
    </div>
  );
}

export default function Intelligence() {
  const {
    analysis,
    analysisError,
    telemetryError,
    audioProgress,
    audioSession,
    telemetrySession,
    raceOverview,
    isAnalyzing,
    isTelemetryUploading,
    telemetryVerification,
    status,
  } = useAnalysisSession();
  const driverState = getDriverStateView(analysis);
  const uploadInProgress = audioProgress.status === 'uploading' || isTelemetryUploading;
  const uploadFailed = audioProgress.status === 'error' ? audioProgress.message : null;

  if (uploadInProgress) {
    return (
      <div className="sc-intelligence sc-intelligence--centered">
        <EmptyState
          icon={<AudioLines size={36} />}
          title="UPLOADING SESSION DATA"
          description={audioProgress.status === 'uploading'
            ? `${audioProgress.message} (${audioProgress.progress}%)`
            : 'Uploading real race telemetry for backend validation.'}
        />
      </div>
    );
  }

  if (isAnalyzing) {
    return (
      <div className="sc-intelligence sc-intelligence--centered">
        <section className="sc-intelligence__processing" aria-live="polite">
          <BrainCircuit size={42} className="sc-spin-anim text-lime" />
          <span className="text-label text-lime">REAL MODEL PIPELINE</span>
          <h1 className="text-h1">ANALYZING SESSION</h1>
          <p className="text-body">The backend is processing the uploaded driver radio and verified race telemetry.</p>
          <div className="sc-intelligence__stage-list font-telemetry text-caption">
            <span>Transcribing driver radio</span>
            <span>Extracting acoustic signals</span>
            <span>Fusing driver state</span>
            <span>Aligning telemetry</span>
            <span>Generating insights</span>
          </div>
          <p className="text-caption">These are pipeline operations, not per-stage completion indicators.</p>
        </section>
      </div>
    );
  }

  if (analysisError || uploadFailed || telemetryError) {
    return (
      <div className="sc-intelligence sc-intelligence--centered">
        <EmptyState
          icon={<ShieldAlert size={36} />}
          title={analysisError ? 'ANALYSIS FAILED' : 'SESSION DATA FAILED'}
          description={analysisError ?? uploadFailed ?? telemetryError ?? 'The real analysis pipeline did not complete.'}
        />
      </div>
    );
  }

  if (!analysis) {
    const preparation = telemetryVerification === 'checking'
      ? `Verifying race session ${telemetrySession?.race_id ?? ''} with the backend.`
      : telemetrySession
        ? 'Real telemetry is ready. Upload driver audio and start analysis in Command Console.'
        : audioSession
          ? 'Driver radio is connected. Upload race telemetry in Command Console.'
          : 'Driver intelligence will appear after real audio and race telemetry are analyzed.';
    return (
      <div className="sc-intelligence sc-intelligence--centered">
        <EmptyState
          icon={<BrainCircuit size={40} />}
          title="AWAITING ANALYSIS"
          description={preparation}
        />
      </div>
    );
  }

  const stressCorrelation = analysis.correlations.stress_vs_lap_delta;
  const fatigueCorrelation = analysis.correlations.fatigue_vs_lap_delta;
  const correlationUnavailable = stressCorrelation.pearson_r === null && fatigueCorrelation.pearson_r === null;

  return (
    <div className="sc-intelligence">
      <motion.header
        className="sc-intelligence__header"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div>
          <span className="text-label text-lime">ANALYTICAL SESSION VIEW</span>
          <h1 className="text-h1">DRIVER INTELLIGENCE</h1>
          <p className="text-body">
            One canonical analysis response, presented as evidence for race engineering review.
          </p>
        </div>
        <div className="sc-intelligence__session">
          <SignalIndicator status="active" label="ANALYSIS COMPLETE" />
          <span className="font-telemetry text-micro">{analysis.race_id ?? 'NO RACE ID'}</span>
          <span className="font-telemetry text-micro">{analysis.analysis_id}</span>
        </div>
      </motion.header>

      <section className="sc-intelligence__metrics" aria-label="Analysis summary">
        <div><span className="text-label">STRESS</span><strong className="font-telemetry">{driverState.stressScore?.toFixed(0) ?? '--'}{driverState.stressScore !== null ? '%' : ''}</strong></div>
        <div><span className="text-label">FATIGUE</span><strong className="font-telemetry">{driverState.fatigueScore?.toFixed(0) ?? '--'}{driverState.fatigueScore !== null ? '%' : ''}</strong></div>
        <div><span className="text-label">ALIGNED LAPS</span><strong className="font-telemetry">{analysis.aligned_laps.length}</strong></div>
        <div><span className="text-label">PIPELINE TIME</span><strong className="font-telemetry">{analysis.processing_time_ms.toFixed(0)}ms</strong></div>
      </section>

      <div className="sc-intelligence__layout">
        <section className="sc-intelligence__section" aria-labelledby="intelligence-driver-state">
          <div className="sc-intelligence__section-heading">
            <Activity size={16} />
            <div><span className="text-label">01</span><h2 id="intelligence-driver-state">DRIVER STATE</h2></div>
          </div>
          <DriverStateCard
            stressScore={driverState.stressScore}
            fatigueScore={driverState.fatigueScore}
            calmScore={driverState.calmScore}
            dominantEmotion={analysis.summary.dominant_state}
            confidence={driverState.confidence}
            processingTime={analysis.processing_time_ms}
          />
        </section>

        <section className="sc-intelligence__section" aria-labelledby="intelligence-voice-signals">
          <div className="sc-intelligence__section-heading">
            <AudioLines size={16} />
            <div><span className="text-label">02</span><h2 id="intelligence-voice-signals">VOICE SIGNALS</h2></div>
          </div>
          <div className="sc-intelligence__signal-meta font-telemetry">
            <span>{analysis.transcription?.segments.length ?? 0} transcript segments</span>
            <span>{analysis.acoustic_analysis.segments.length} acoustic windows</span>
            <span>{analysis.transcription?.language ? `Language: ${analysis.transcription.language}` : 'Language: not reported'}</span>
          </div>
          <TranscriptTimeline
            segments={analysis.transcription?.segments ?? []}
            states={analysis.driver_states}
            currentTime={-1}
          />
        </section>

        <section className="sc-intelligence__section sc-intelligence__section--wide" aria-labelledby="intelligence-correlation">
          <div className="sc-intelligence__section-heading">
            <Gauge size={16} />
            <div><span className="text-label">03</span><h2 id="intelligence-correlation">PERFORMANCE CORRELATION</h2></div>
          </div>
          {correlationUnavailable && (
            <div className="sc-intelligence__insufficient">
              <strong>INSUFFICIENT ALIGNED DATA</strong>
              <span>Additional radio or telemetry samples are required to calculate a reliable correlation.</span>
            </div>
          )}
          <div className="sc-intelligence__correlation-grid">
            <CorrelationCard label="STRESS ↔ LAP DELTA" result={stressCorrelation} />
            <CorrelationCard label="FATIGUE ↔ LAP DELTA" result={fatigueCorrelation} />
          </div>
          <p className="text-caption sc-intelligence__causation">
            Correlation describes association within this analyzed session; it does not establish causation.
          </p>
        </section>

        <section className="sc-intelligence__section sc-intelligence__section--wide" aria-labelledby="intelligence-evidence">
          <div className="sc-intelligence__section-heading">
            <Sparkles size={16} />
            <div><span className="text-label">04</span><h2 id="intelligence-evidence">EVIDENCE / INSIGHTS</h2></div>
          </div>
          <RaceInsightsFeed insights={analysis.insights} />
        </section>
      </div>

      <footer className="sc-intelligence__footer font-telemetry text-micro">
        <span>{raceOverview ? `${raceOverview.total_laps} validated source laps` : 'Race overview unavailable'}</span>
        <span>{status.replaceAll('_', ' ').toUpperCase()}</span>
      </footer>
    </div>
  );
}
