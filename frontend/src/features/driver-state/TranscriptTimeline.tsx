import React from 'react';
import { MessageSquare, Clock } from 'lucide-react';
import type { TranscriptSegment } from '../../types';
import './TranscriptTimeline.css';

interface TranscriptTimelineProps {
  segments: TranscriptSegment[];
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function getConfidenceClass(confidence: number): string {
  if (confidence >= 0.9) return 'confidence--high';
  if (confidence >= 0.75) return 'confidence--medium';
  return 'confidence--low';
}

export const TranscriptTimeline: React.FC<TranscriptTimelineProps> = ({ segments }) => {
  if (!segments.length) {
    return (
      <div className="transcript-timeline transcript-timeline--empty">
        <MessageSquare size={32} className="transcript-timeline__empty-icon" />
        <p>No transcript data available. Upload and analyze audio to see the timeline.</p>
      </div>
    );
  }

  return (
    <div className="transcript-timeline">
      <div className="transcript-timeline__header">
        <MessageSquare size={18} />
        <h3>Radio Transcript</h3>
        <span className="transcript-timeline__count">{segments.length} segments</span>
      </div>

      <div className="transcript-timeline__list">
        {segments.map((seg, i) => (
          <div className="transcript-segment" key={i}>
            <div className="transcript-segment__timeline">
              <div className="transcript-segment__dot" />
              {i < segments.length - 1 && <div className="transcript-segment__line" />}
            </div>

            <div className="transcript-segment__content">
              <div className="transcript-segment__meta">
                <span className="transcript-segment__time">
                  <Clock size={12} />
                  {formatTime(seg.start_time)} — {formatTime(seg.end_time)}
                </span>
                {seg.speaker && (
                  <span className="transcript-segment__speaker">{seg.speaker}</span>
                )}
                <span className={`transcript-segment__confidence ${getConfidenceClass(seg.confidence)}`}>
                  {(seg.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <p className="transcript-segment__text">{seg.text}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TranscriptTimeline;
