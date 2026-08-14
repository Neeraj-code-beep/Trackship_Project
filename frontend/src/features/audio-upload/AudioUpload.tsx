import React, { useCallback, useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileAudio, AlertCircle, Loader2, Radio, Play, Pause, Volume2, ShieldCheck, RefreshCw } from 'lucide-react';
import { uploadAudio, normalizeError } from '../../services/api';
import type { AudioUploadResponse, UploadProgress } from '../../types';
import Waveform from '../../components/ui/Waveform';
import SignalIndicator from '../../components/ui/SignalIndicator';
import Button from '../../components/ui/Button';
import './AudioUpload.css';

const ALLOWED_TYPES = ['.wav', '.mp3', '.m4a', '.flac'];
const MAX_SIZE_MB = 50;

interface AudioUploadProps {
  onUploadComplete: (response: AudioUploadResponse) => void;
  isPlaying: boolean;
  setIsPlaying: (playing: boolean) => void;
  currentTime: number;
  setCurrentTime: (time: number) => void;
  duration: number;
  setDuration: (duration: number) => void;
  seekTrigger: { time: number } | null;
  onFileSelect: (file: File | null) => void;
}

function formatTime(seconds: number): string {
  if (isNaN(seconds)) return '00:00.0';
  const m = Math.floor(seconds / 60);
  const s = (seconds % 60).toFixed(1);
  return `${m.toString().padStart(2, '0')}:${s.padStart(4, '0')}`;
}

export const AudioUpload: React.FC<AudioUploadProps> = ({
  onUploadComplete,
  isPlaying,
  setIsPlaying,
  currentTime,
  setCurrentTime,
  duration,
  setDuration,
  seekTrigger,
  onFileSelect,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [progress, setProgress] = useState<UploadProgress>({
    status: 'idle',
    progress: 0,
    message: 'Drop driver radio audio session or click to select file',
  });
  const [uploadedFile, setUploadedFile] = useState<AudioUploadResponse | null>(null);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const audioHtmlRef = useRef<HTMLAudioElement | null>(null);
  const [audioUrl, setAudioUrl] = useState<string>('');

  const validateFile = (file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_TYPES.includes(ext)) {
      return `Unsupported format '${ext}'. Allowed: ${ALLOWED_TYPES.join(', ')}`;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File size (${(file.size / (1024 * 1024)).toFixed(1)}MB) exceeds limit (${MAX_SIZE_MB}MB)`;
    }
    return null;
  };

  const handleUpload = useCallback(async (file: File) => {
    const error = validateFile(file);
    if (error) {
      setProgress({ status: 'error', progress: 0, message: error });
      return;
    }

    setProgress({ status: 'uploading', progress: 0, message: 'Ingesting Driver Radio Telemetry...' });

    try {
      const response = await uploadAudio(file, (pct) => {
        setProgress({ status: 'uploading', progress: pct, message: `Ingesting Driver Radio Audio... ${pct}%` });
      });

      // Set file and blob URL for browser playback
      const url = URL.createObjectURL(file);
      setAudioUrl(url);
      onFileSelect(file);

      setUploadedFile(response);
      setProgress({
        status: 'complete',
        progress: 100,
        message: `✓ Session Ingested: ${response.filename}`,
      });
      onUploadComplete(response);
    } catch (err: any) {
      const msg = normalizeError(err);
      setProgress({ status: 'error', progress: 0, message: msg });
    }
  }, [onUploadComplete, onFileSelect]);

  // Audio Playback Effects
  useEffect(() => {
    if (audioHtmlRef.current) {
      if (isPlaying) {
        audioHtmlRef.current.play().catch(() => setIsPlaying(false));
      } else {
        audioHtmlRef.current.pause();
      }
    }
  }, [isPlaying, setIsPlaying]);

  // Listen to Seek Trigger
  useEffect(() => {
    if (seekTrigger && audioHtmlRef.current) {
      audioHtmlRef.current.currentTime = seekTrigger.time;
      setCurrentTime(seekTrigger.time);
      if (!isPlaying) {
        setIsPlaying(true);
      }
    }
  }, [seekTrigger, setCurrentTime, isPlaying, setIsPlaying]);

  const handleTimeUpdate = () => {
    if (audioHtmlRef.current) {
      setCurrentTime(audioHtmlRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioHtmlRef.current) {
      setDuration(audioHtmlRef.current.duration);
    }
  };

  const handleAudioEnded = () => {
    setIsPlaying(false);
    setCurrentTime(0);
  };

  const handleScrub = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!audioHtmlRef.current || duration === 0) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const width = rect.width;
    const pct = clickX / width;
    const newTime = pct * duration;
    audioHtmlRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files?.[0]) {
      handleUpload(e.dataTransfer.files[0]);
    }
  }, [handleUpload]);

  const reset = () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    setProgress({ status: 'idle', progress: 0, message: 'Drop driver radio audio session or click to select file' });
    setUploadedFile(null);
    setAudioUrl('');
    onFileSelect(null);
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="sc-radio-uploader">
      {/* HTML5 Audio Player */}
      {audioUrl && (
        <audio
          ref={audioHtmlRef}
          src={audioUrl}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onEnded={handleAudioEnded}
          style={{ display: 'none' }}
        />
      )}

      <div className="sc-radio-uploader__header">
        <div className="sc-radio-uploader__title-group">
          <div className="sc-radio-uploader__icon-badge">
            <Radio size={16} className="text-lime" />
          </div>
          <div>
            <h3 className="text-h4 font-display" style={{ margin: 0 }}>Driver Radio Console</h3>
            <span className="text-micro font-telemetry">LIVE AUDIO SIGNAL CHANNEL 01</span>
          </div>
        </div>
        <SignalIndicator
          status={progress.status === 'uploading' ? 'processing' : progress.status === 'complete' ? 'active' : 'idle'}
          label={progress.status === 'complete' ? 'RADIO ACTIVE' : progress.status === 'uploading' ? 'INGESTING' : 'STANDBY'}
        />
      </div>

      <motion.div
        className={`sc-dropzone ${dragActive ? 'sc-dropzone--active' : ''} ${progress.status === 'error' ? 'sc-dropzone--error' : ''} ${progress.status === 'complete' ? 'sc-dropzone--complete' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => progress.status !== 'uploading' && progress.status !== 'complete' && inputRef.current?.click()}
        whileHover={{ scale: progress.status === 'idle' ? 1.002 : 1 }}
        whileTap={{ scale: 0.998 }}
        style={{ cursor: progress.status === 'complete' ? 'default' : 'pointer' }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ALLOWED_TYPES.join(',')}
          onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
          className="sc-dropzone__input"
        />

        <AnimatePresence mode="wait">
          {progress.status === 'idle' && (
            <motion.div
              key="idle"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              className="sc-dropzone__content"
            >
              <div className="sc-dropzone__icon-wrapper">
                <Upload size={22} />
              </div>
              <div className="sc-dropzone__text-group">
                <p className="sc-dropzone__title text-h4 font-display">Drop Driver Radio Session</p>
                <p className="sc-dropzone__subtitle text-caption">
                  WAV · MP3 · M4A · FLAC — Up to 50MB
                </p>
              </div>
              <Waveform active={false} barCount={40} color="neutral" height={32} className="sc-dropzone__waveform" />
            </motion.div>
          )}

          {progress.status === 'uploading' && (
            <motion.div
              key="uploading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="sc-dropzone__content"
            >
              <Loader2 size={32} className="sc-spin-anim text-lime" />
              <p className="sc-dropzone__title text-h4 font-display">{progress.message}</p>
              <div className="sc-dropzone__progress-bar">
                <div className="sc-dropzone__progress-fill" style={{ width: `${progress.progress}%` }} />
              </div>
              <Waveform active barCount={40} color="lime" height={36} />
            </motion.div>
          )}

          {progress.status === 'complete' && uploadedFile && (
            <motion.div
              key="complete"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="sc-radio-player"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="sc-radio-player__top">
                <button
                  className="sc-radio-player__play-btn"
                  onClick={() => setIsPlaying(!isPlaying)}
                  aria-label={isPlaying ? 'Pause radio' : 'Play radio'}
                >
                  {isPlaying ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: 2 }} />}
                </button>

                <div className="sc-radio-player__info">
                  <div className="sc-radio-player__meta">
                    <span className="sc-radio-player__filename font-telemetry">{uploadedFile.filename}</span>
                    <span className="sc-radio-player__badge"><ShieldCheck size={11} /> 94% CONFIDENCE</span>
                  </div>

                  <div className="sc-radio-player__scrubber">
                    <div
                      className="sc-radio-player__timeline"
                      onClick={handleScrub}
                      style={{ cursor: 'pointer' }}
                    >
                      <div
                        className="sc-radio-player__progress"
                        style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }}
                      />
                    </div>
                    <div className="sc-radio-player__times font-telemetry">
                      <span>{formatTime(currentTime)}</span>
                      <span>{formatTime(duration || uploadedFile.duration_seconds || 0)}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="sc-radio-player__waveform-row">
                <Waveform active={isPlaying} barCount={48} color={isPlaying ? 'lime' : 'neutral'} height={32} />
              </div>

              <div className="sc-radio-player__footer">
                <div className="sc-radio-player__tags font-telemetry">
                  <span className="sc-dropzone__tag"><FileAudio size={12} /> {uploadedFile.format.toUpperCase()}</span>
                  <span className="sc-dropzone__tag">{(uploadedFile.file_size_bytes / 1024).toFixed(0)} KB</span>
                  <span className="sc-dropzone__tag"><Volume2 size={12} /> 44.1kHz</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={reset}
                >
                  <RefreshCw size={12} style={{ marginRight: 6 }} /> Reset Session
                </Button>
              </div>
            </motion.div>
          )}

          {progress.status === 'error' && (
            <motion.div
              key="error"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="sc-dropzone__content"
            >
              <AlertCircle size={32} style={{ color: 'var(--color-driver-stressed)' }} />
              <p className="sc-dropzone__title text-h4 font-display" style={{ color: 'var(--color-driver-stressed)' }}>
                Ingestion Failed
              </p>
              <p className="sc-dropzone__subtitle text-caption">{progress.message}</p>
              <Button
                variant="secondary"
                size="sm"
                onClick={(e) => { e.stopPropagation(); reset(); }}
              >
                Try Again
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

export default AudioUpload;
