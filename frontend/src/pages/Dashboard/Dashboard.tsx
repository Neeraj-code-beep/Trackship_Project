import React, { useState, useCallback } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, ComposedChart, Bar, Legend,
  ReferenceLine
} from 'recharts';
import {
  Gauge, Radio, Activity, Timer, TrendingUp, Cpu
} from 'lucide-react';
import AudioUpload from '../../features/audio-upload/AudioUpload';
import DriverStateCard from '../../features/driver-state/DriverStateCard';
import TranscriptTimeline from '../../features/driver-state/TranscriptTimeline';
import RaceInsightsFeed from '../../features/race-insights/RaceInsightsFeed';
import { runAnalysis, ingestLaps } from '../../services/api';
import type {
  AudioUploadResponse, AnalysisResponse, AlignedLapEmotion,
  TranscriptSegment, InsightItem, EmotionLabel
} from '../../types';
import './Dashboard.css';

// Demo lap data for first-use experience
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

export const Dashboard: React.FC = () => {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [uploadedFileId, setUploadedFileId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUploadComplete = useCallback(async (response: AudioUploadResponse) => {
    setUploadedFileId(response.file_id);
    setIsAnalyzing(true);
    setError(null);

    try {
      // Ingest demo lap data first
      await ingestLaps({
        race_id: RACE_ID,
        driver_name: 'Demo Driver',
        laps: DEMO_LAPS,
      });

      // Then run full analysis
      const result = await runAnalysis({
        file_id: response.file_id,
        race_id: RACE_ID,
      });

      setAnalysis(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  // Prepare chart data
  const chartData = analysis?.aligned_laps?.map((lap: AlignedLapEmotion) => ({
    lap: `L${lap.lap_number}`,
    lapTime: lap.lap_time_seconds,
    delta: lap.delta_to_best,
    stress: +(lap.stress_level * 100).toFixed(1),
    fatigue: +(lap.fatigue_level * 100).toFixed(1),
  })) || [];

  const bestLap = chartData.length > 0
    ? Math.min(...chartData.map((d: { lapTime: number }) => d.lapTime))
    : 0;

  // Determine dominant overall emotion
  const dominantEmotion: EmotionLabel = analysis?.driver_states?.length
    ? ((): EmotionLabel => {
        const counts: Record<string, number> = {};
        analysis.driver_states.forEach(s => {
          counts[s.dominant_emotion] = (counts[s.dominant_emotion] || 0) + 1;
        });
        return (Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] as EmotionLabel) || 'neutral';
      })()
    : 'neutral';

  // Average probabilities
  const avgProbs = analysis?.driver_states?.length
    ? {
        calm: analysis.driver_states.reduce((s, d) => s + d.probabilities.calm, 0) / analysis.driver_states.length,
        stressed: analysis.driver_states.reduce((s, d) => s + d.probabilities.stressed, 0) / analysis.driver_states.length,
        neutral: analysis.driver_states.reduce((s, d) => s + d.probabilities.neutral, 0) / analysis.driver_states.length,
        tired: analysis.driver_states.reduce((s, d) => s + d.probabilities.tired, 0) / analysis.driver_states.length,
      }
    : undefined;

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard__header">
        <div className="dashboard__logo">
          <div className="dashboard__logo-icon">
            <Radio size={24} />
          </div>
          <div>
            <h1 className="dashboard__title">Silent Co-Driver</h1>
            <p className="dashboard__subtitle">AI Race Engineering Intelligence</p>
          </div>
        </div>
        <div className="dashboard__status">
          <div className={`status-dot ${analysis ? 'status-dot--active' : ''}`} />
          <span>{analysis ? 'Analysis Active' : 'Awaiting Data'}</span>
        </div>
      </header>

      {/* Top Stats Row */}
      {analysis && (
        <div className="dashboard__stats">
          <div className="stat-card">
            <Activity size={18} className="stat-card__icon stat-card__icon--stress" />
            <div>
              <span className="stat-card__value">{(analysis.overall_stress * 100).toFixed(0)}%</span>
              <span className="stat-card__label">Stress Level</span>
            </div>
          </div>
          <div className="stat-card">
            <Timer size={18} className="stat-card__icon stat-card__icon--fatigue" />
            <div>
              <span className="stat-card__value">{(analysis.overall_fatigue * 100).toFixed(0)}%</span>
              <span className="stat-card__label">Fatigue Index</span>
            </div>
          </div>
          <div className="stat-card">
            <TrendingUp size={18} className="stat-card__icon stat-card__icon--laps" />
            <div>
              <span className="stat-card__value">{analysis.aligned_laps?.length || 0}</span>
              <span className="stat-card__label">Laps Analyzed</span>
            </div>
          </div>
          <div className="stat-card">
            <Cpu size={18} className="stat-card__icon stat-card__icon--time" />
            <div>
              <span className="stat-card__value">{analysis.processing_time_ms.toFixed(0)}ms</span>
              <span className="stat-card__label">Processing</span>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="dashboard__grid">
        {/* Left Column */}
        <div className="dashboard__col dashboard__col--main">
          {/* Audio Upload */}
          <section className="dashboard__section">
            <AudioUpload onUploadComplete={handleUploadComplete} />
          </section>

          {/* Loading State */}
          {isAnalyzing && (
            <section className="dashboard__section dashboard__loading">
              <div className="loading-spinner" />
              <p>Analyzing audio — transcribing, detecting emotions, correlating with lap data...</p>
            </section>
          )}

          {/* Error State */}
          {error && (
            <section className="dashboard__section dashboard__error">
              <p>⚠️ {error}</p>
            </section>
          )}

          {/* Lap Performance Chart */}
          {chartData.length > 0 && (
            <section className="dashboard__section chart-section">
              <h2 className="section-title">
                <Gauge size={20} />
                Lap Performance vs. Driver State
              </h2>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height={320}>
                  <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="stressGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#f87171" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#f87171" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="fatigueGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#fbbf24" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#fbbf24" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="lap" stroke="rgba(255,255,255,0.3)" fontSize={12} />
                    <YAxis yAxisId="time" stroke="rgba(255,255,255,0.3)" fontSize={12} domain={['dataMin - 1', 'dataMax + 1']} />
                    <YAxis yAxisId="pct" orientation="right" stroke="rgba(255,255,255,0.2)" fontSize={11} domain={[0, 100]} unit="%" />
                    <Tooltip
                      contentStyle={{
                        background: 'rgba(15,15,25,0.95)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: 10,
                        fontSize: 12,
                        color: '#fff',
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12, color: 'rgba(255,255,255,0.5)' }} />
                    <ReferenceLine yAxisId="time" y={bestLap} stroke="#34d399" strokeDasharray="5 5" label={{ value: 'Best', fill: '#34d399', fontSize: 11 }} />
                    <Area yAxisId="pct" type="monotone" dataKey="stress" fill="url(#stressGrad)" stroke="#f87171" strokeWidth={2} name="Stress %" dot={false} />
                    <Area yAxisId="pct" type="monotone" dataKey="fatigue" fill="url(#fatigueGrad)" stroke="#fbbf24" strokeWidth={2} name="Fatigue %" dot={false} />
                    <Line yAxisId="time" type="monotone" dataKey="lapTime" stroke="#818cf8" strokeWidth={3} name="Lap Time (s)" dot={{ fill: '#818cf8', r: 4 }} activeDot={{ r: 6, fill: '#a78bfa' }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </section>
          )}

          {/* Transcript Timeline */}
          {analysis?.transcription && (
            <section className="dashboard__section">
              <TranscriptTimeline segments={analysis.transcription.segments} />
            </section>
          )}
        </div>

        {/* Right Column */}
        <div className="dashboard__col dashboard__col--side">
          {/* Driver State Card */}
          <section className="dashboard__section">
            <DriverStateCard
              overallStress={analysis?.overall_stress ?? 0}
              overallFatigue={analysis?.overall_fatigue ?? 0}
              dominantEmotion={dominantEmotion}
              probabilities={avgProbs}
              processingTime={analysis?.processing_time_ms}
            />
          </section>

          {/* Race Engineer Insights */}
          <section className="dashboard__section">
            <RaceInsightsFeed insights={analysis?.insights ?? []} />
          </section>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
