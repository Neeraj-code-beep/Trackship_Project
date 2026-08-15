import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import {
  getHttpStatus,
  getRace,
  normalizeError,
  runAnalysis,
  uploadLapTelemetryCsv,
} from '../services/api';
import type {
  AnalysisResponse,
  AudioUploadResponse,
  RaceOverview,
  UploadProgress,
} from '../types';

const AUDIO_SESSION_KEY = 'silent-co-driver.audio-session';
const TELEMETRY_SESSION_KEY = 'silent-co-driver.telemetry-session';

export interface TelemetrySession {
  race_id: string;
  driver_name: string;
  laps_received: number;
  message: string;
  source_filename: string;
  uploaded_at: string;
}

export type TelemetryVerification = 'idle' | 'checking' | 'verified' | 'unavailable';
export type AnalysisSessionStatus =
  | 'waiting'
  | 'uploading_audio'
  | 'radio_connected'
  | 'uploading_telemetry'
  | 'verifying_telemetry'
  | 'telemetry_ready'
  | 'analyzing'
  | 'analysis_complete'
  | 'analysis_failed';

interface AnalysisSessionContextValue {
  audioSession: AudioUploadResponse | null;
  audioPlaybackUrl: string | null;
  telemetrySession: TelemetrySession | null;
  raceOverview: RaceOverview | null;
  analysis: AnalysisResponse | null;
  analysisError: string | null;
  telemetryError: string | null;
  raceId: string;
  driverName: string;
  audioProgress: UploadProgress;
  telemetryVerification: TelemetryVerification;
  isTelemetryUploading: boolean;
  isAnalyzing: boolean;
  status: AnalysisSessionStatus;
  setRaceId: (value: string) => void;
  setDriverName: (value: string) => void;
  setAudioProgress: (value: UploadProgress) => void;
  setAudioPlaybackUrl: (value: string | null) => void;
  completeAudioUpload: (response: AudioUploadResponse) => void;
  resetAudio: () => void;
  uploadTelemetry: (file: File) => Promise<boolean>;
  resetTelemetry: () => void;
  startAnalysis: () => Promise<boolean>;
}

const AnalysisSessionContext = createContext<AnalysisSessionContextValue | null>(null);

const idleAudioProgress: UploadProgress = {
  status: 'idle',
  progress: 0,
  message: 'Drop driver radio audio session or click to select file',
};

function createRaceId(): string {
  const randomId = typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  return `race-${randomId}`;
}

function readStoredValue<T>(key: string): T | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(key);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    window.localStorage.removeItem(key);
    return null;
  }
}

export function AnalysisSessionProvider({ children }: { children: ReactNode }) {
  const storedTelemetryRef = useRef(readStoredValue<TelemetrySession>(TELEMETRY_SESSION_KEY));
  const [audioSession, setAudioSession] = useState<AudioUploadResponse | null>(() =>
    readStoredValue<AudioUploadResponse>(AUDIO_SESSION_KEY)
  );
  const [telemetrySession, setTelemetrySession] = useState<TelemetrySession | null>(
    storedTelemetryRef.current
  );
  const [raceOverview, setRaceOverview] = useState<RaceOverview | null>(null);
  const [raceId, setRaceId] = useState(storedTelemetryRef.current?.race_id ?? createRaceId());
  const [driverName, setDriverName] = useState(storedTelemetryRef.current?.driver_name ?? '');
  const [audioProgress, setAudioProgress] = useState<UploadProgress>(() =>
    audioSession
      ? { status: 'complete', progress: 100, message: `Session restored: ${audioSession.filename}` }
      : idleAudioProgress
  );
  const [audioPlaybackUrl, setAudioPlaybackUrl] = useState<string | null>(null);
  const [telemetryVerification, setTelemetryVerification] = useState<TelemetryVerification>(
    storedTelemetryRef.current ? 'checking' : 'idle'
  );
  const [isTelemetryUploading, setIsTelemetryUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [telemetryError, setTelemetryError] = useState<string | null>(null);
  const telemetryUploadInFlightRef = useRef(false);
  const analysisInFlightRef = useRef(false);

  useEffect(() => {
    if (audioSession) {
      window.localStorage.setItem(AUDIO_SESSION_KEY, JSON.stringify(audioSession));
    } else {
      window.localStorage.removeItem(AUDIO_SESSION_KEY);
    }
  }, [audioSession]);

  useEffect(() => {
    if (telemetrySession) {
      window.localStorage.setItem(TELEMETRY_SESSION_KEY, JSON.stringify(telemetrySession));
    } else {
      window.localStorage.removeItem(TELEMETRY_SESSION_KEY);
    }
  }, [telemetrySession]);

  useEffect(() => {
    const storedTelemetry = storedTelemetryRef.current;
    if (!storedTelemetry) return;

    let active = true;
    setTelemetryVerification('checking');
    getRace(storedTelemetry.race_id)
      .then((race) => {
        if (!active) return;
        setRaceOverview(race);
        setTelemetrySession((current) => current && current.race_id === race.race_id
          ? {
              ...current,
              driver_name: race.driver_name,
              laps_received: race.total_laps,
              message: `Reusing ${race.total_laps} validated laps from race '${race.race_id}'.`,
            }
          : current
        );
        setRaceId(race.race_id);
        setDriverName(race.driver_name);
        setTelemetryError(null);
        setTelemetryVerification('verified');
      })
      .catch((error: unknown) => {
        if (!active) return;
        if (getHttpStatus(error) === 404) {
          setTelemetrySession(null);
          setRaceOverview(null);
          setRaceId(createRaceId());
          setDriverName('');
          setTelemetryVerification('idle');
          setTelemetryError(
            'The saved race session is no longer available on this backend. Upload race telemetry for a new session.'
          );
          return;
        }
        setTelemetryVerification('unavailable');
        setTelemetryError(
          `Saved race telemetry could not be verified: ${normalizeError(error)} Analysis remains disabled until verification succeeds.`
        );
      });

    return () => {
      active = false;
    };
  }, []);

  const completeAudioUpload = useCallback((response: AudioUploadResponse) => {
    setAudioSession(response);
    setAudioProgress({ status: 'complete', progress: 100, message: `Session ingested: ${response.filename}` });
    setAnalysis(null);
    setAnalysisError(null);
  }, []);

  const resetAudio = useCallback(() => {
    if (audioPlaybackUrl) URL.revokeObjectURL(audioPlaybackUrl);
    setAudioSession(null);
    setAudioPlaybackUrl(null);
    setAudioProgress(idleAudioProgress);
    setAnalysis(null);
    setAnalysisError(null);
    setIsAnalyzing(false);
  }, [audioPlaybackUrl]);

  const uploadTelemetry = useCallback(async (file: File): Promise<boolean> => {
    if (telemetryUploadInFlightRef.current) return false;
    if (telemetrySession) {
      setTelemetryError(
        'Telemetry is already stored for this race session. Reuse it for analysis, or reset telemetry to start a new session.'
      );
      return false;
    }
    if (!driverName.trim()) {
      setTelemetryError('Driver name is required for telemetry ingestion.');
      return false;
    }
    if (!raceId.trim()) {
      setTelemetryError('Race session ID is required for telemetry ingestion.');
      return false;
    }

    telemetryUploadInFlightRef.current = true;
    setIsTelemetryUploading(true);
    setTelemetryError(null);
    setAnalysisError(null);
    setAnalysis(null);
    let telemetryWasStored = false;

    try {
      const response = await uploadLapTelemetryCsv({
        raceId: raceId.trim(),
        driverName: driverName.trim(),
        file,
      });
      const nextTelemetry: TelemetrySession = {
        race_id: response.race_id,
        driver_name: response.driver_name,
        laps_received: response.laps_received,
        message: response.message,
        source_filename: file.name,
        uploaded_at: new Date().toISOString(),
      };
      telemetryWasStored = true;

      setTelemetrySession(nextTelemetry);
      setRaceId(response.race_id);
      setDriverName(response.driver_name);
      setTelemetryVerification('checking');

      // A successful CSV POST is verified with a race read before analysis is enabled.
      const race = await getRace(response.race_id);
      setRaceOverview(race);
      setTelemetrySession((current) => current && current.race_id === race.race_id
        ? { ...current, driver_name: race.driver_name, laps_received: race.total_laps }
        : current
      );
      setTelemetryVerification('verified');
      return true;
    } catch (error: unknown) {
      setTelemetryError(normalizeError(error));
      setTelemetryVerification(telemetryWasStored || telemetrySession ? 'unavailable' : 'idle');
      return false;
    } finally {
      telemetryUploadInFlightRef.current = false;
      setIsTelemetryUploading(false);
    }
  }, [driverName, raceId, telemetrySession]);

  const resetTelemetry = useCallback(() => {
    setTelemetrySession(null);
    setRaceOverview(null);
    setTelemetryVerification('idle');
    setTelemetryError(null);
    setAnalysis(null);
    setAnalysisError(null);
    setRaceId(createRaceId());
    setDriverName('');
  }, []);

  const startAnalysis = useCallback(async (): Promise<boolean> => {
    if (analysisInFlightRef.current) return false;
    if (!audioSession?.file_id) {
      setAnalysisError('Upload real driver audio before starting analysis.');
      return false;
    }
    if (!telemetrySession?.race_id) {
      setAnalysisError('Upload race telemetry before starting analysis.');
      return false;
    }
    if (telemetryVerification !== 'verified') {
      setAnalysisError('Race telemetry must be verified by the backend before analysis can start.');
      return false;
    }

    analysisInFlightRef.current = true;
    setIsAnalyzing(true);
    setAnalysisError(null);
    setAnalysis(null);

    try {
      const result = await runAnalysis({
        file_id: audioSession.file_id,
        race_id: telemetrySession.race_id,
      });
      setAnalysis(result);
      return true;
    } catch (error: unknown) {
      setAnalysisError(normalizeError(error));
      return false;
    } finally {
      analysisInFlightRef.current = false;
      setIsAnalyzing(false);
    }
  }, [audioSession?.file_id, telemetrySession?.race_id, telemetryVerification]);

  const status: AnalysisSessionStatus = analysis
    ? 'analysis_complete'
    : isAnalyzing
      ? 'analyzing'
      : analysisError
        ? 'analysis_failed'
        : isTelemetryUploading
          ? 'uploading_telemetry'
          : telemetryVerification === 'checking'
            ? 'verifying_telemetry'
            : telemetryVerification === 'verified' && telemetrySession
              ? 'telemetry_ready'
              : audioProgress.status === 'uploading'
                ? 'uploading_audio'
                : audioSession
                  ? 'radio_connected'
                  : 'waiting';

  const value = useMemo<AnalysisSessionContextValue>(() => ({
    audioSession,
    audioPlaybackUrl,
    telemetrySession,
    raceOverview,
    analysis,
    analysisError,
    telemetryError,
    raceId,
    driverName,
    audioProgress,
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
  }), [
    analysis,
    analysisError,
    audioProgress,
    audioPlaybackUrl,
    audioSession,
    completeAudioUpload,
    driverName,
    isAnalyzing,
    isTelemetryUploading,
    raceId,
    raceOverview,
    resetAudio,
    resetTelemetry,
    startAnalysis,
    status,
    telemetryError,
    telemetrySession,
    telemetryVerification,
    uploadTelemetry,
  ]);

  return <AnalysisSessionContext.Provider value={value}>{children}</AnalysisSessionContext.Provider>;
}

// The provider and its consumer hook intentionally share this single lightweight session module.
// oxlint-disable-next-line react/only-export-components
export function useAnalysisSession(): AnalysisSessionContextValue {
  const context = useContext(AnalysisSessionContext);
  if (!context) {
    throw new Error('useAnalysisSession must be used inside AnalysisSessionProvider.');
  }
  return context;
}
