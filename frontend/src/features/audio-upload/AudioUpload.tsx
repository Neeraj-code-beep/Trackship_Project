import React, { useCallback, useState, useRef } from 'react';
import { Upload, FileAudio, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { uploadAudio } from '../../services/api';
import type { AudioUploadResponse, UploadProgress } from '../../types';
import './AudioUpload.css';

const ALLOWED_TYPES = ['.wav', '.mp3', '.m4a', '.flac'];
const MAX_SIZE_MB = 50;

interface AudioUploadProps {
  onUploadComplete: (response: AudioUploadResponse) => void;
}

export const AudioUpload: React.FC<AudioUploadProps> = ({ onUploadComplete }) => {
  const [dragActive, setDragActive] = useState(false);
  const [progress, setProgress] = useState<UploadProgress>({
    status: 'idle',
    progress: 0,
    message: 'Drop audio file or click to browse',
  });
  const [uploadedFile, setUploadedFile] = useState<AudioUploadResponse | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_TYPES.includes(ext)) {
      return `Unsupported format. Allowed: ${ALLOWED_TYPES.join(', ')}`;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File too large (${(file.size / (1024 * 1024)).toFixed(1)}MB). Max: ${MAX_SIZE_MB}MB`;
    }
    return null;
  };

  const handleUpload = useCallback(async (file: File) => {
    const error = validateFile(file);
    if (error) {
      setProgress({ status: 'error', progress: 0, message: error });
      return;
    }

    setProgress({ status: 'uploading', progress: 0, message: 'Uploading...' });

    try {
      const response = await uploadAudio(file, (pct) => {
        setProgress({ status: 'uploading', progress: pct, message: `Uploading... ${pct}%` });
      });

      setUploadedFile(response);
      setProgress({
        status: 'complete',
        progress: 100,
        message: `✓ ${response.filename} uploaded successfully`,
      });
      onUploadComplete(response);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Upload failed';
      setProgress({ status: 'error', progress: 0, message: msg });
    }
  }, [onUploadComplete]);

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

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      handleUpload(e.target.files[0]);
    }
  }, [handleUpload]);

  const reset = () => {
    setProgress({ status: 'idle', progress: 0, message: 'Drop audio file or click to browse' });
    setUploadedFile(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="audio-upload-container">
      <div
        className={`dropzone ${dragActive ? 'dropzone--active' : ''} ${progress.status === 'error' ? 'dropzone--error' : ''} ${progress.status === 'complete' ? 'dropzone--success' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => progress.status !== 'uploading' && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ALLOWED_TYPES.join(',')}
          onChange={handleChange}
          className="dropzone__input"
        />

        <div className="dropzone__content">
          {progress.status === 'idle' && (
            <>
              <Upload className="dropzone__icon" size={42} />
              <p className="dropzone__title">Upload Driver Radio</p>
              <p className="dropzone__subtitle">.wav, .mp3, .m4a, .flac — up to 50MB</p>
            </>
          )}

          {progress.status === 'uploading' && (
            <>
              <Loader2 className="dropzone__icon dropzone__icon--spin" size={42} />
              <p className="dropzone__title">{progress.message}</p>
              <div className="progress-bar">
                <div className="progress-bar__fill" style={{ width: `${progress.progress}%` }} />
              </div>
            </>
          )}

          {progress.status === 'complete' && uploadedFile && (
            <>
              <CheckCircle className="dropzone__icon dropzone__icon--success" size={42} />
              <p className="dropzone__title">{uploadedFile.filename}</p>
              <div className="upload-meta">
                <span><FileAudio size={14} /> {uploadedFile.format.toUpperCase()}</span>
                <span>{(uploadedFile.file_size_bytes / 1024).toFixed(0)} KB</span>
                {uploadedFile.duration_seconds && (
                  <span>{uploadedFile.duration_seconds.toFixed(1)}s</span>
                )}
              </div>
              <button className="btn-reset" onClick={(e) => { e.stopPropagation(); reset(); }}>
                Upload Another
              </button>
            </>
          )}

          {progress.status === 'error' && (
            <>
              <AlertCircle className="dropzone__icon dropzone__icon--error" size={42} />
              <p className="dropzone__title">Upload Failed</p>
              <p className="dropzone__subtitle">{progress.message}</p>
              <button className="btn-reset" onClick={(e) => { e.stopPropagation(); reset(); }}>
                Try Again
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AudioUpload;
