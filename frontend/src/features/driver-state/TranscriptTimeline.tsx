import React, { useEffect, useRef } from 'react';
import { MessageSquare, Clock, ShieldCheck, Zap } from 'lucide-react';
import type { DriverState, TranscriptSegment } from '../../types';
import { EmptyState } from '../../components/ui/State';
import './TranscriptTimeline.css';

interface TranscriptTimelineProps {
  segments: TranscriptSegment[];
  states: DriverState[];
  currentTime: number;
  onSegmentClick?: (time: number) => void;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = (seconds % 60).toFixed(1);
  return `${m.toString().padStart(2, '0')}:${s.padStart(4, '0')}`;
}

export const TranscriptTimeline: React.FC<TranscriptTimelineProps> = ({
  segments = [],
  states = [],
  currentTime,
  onSegmentClick,
}) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const activeItemRef = useRef<HTMLDivElement>(null);

  // Find active segment index
  const activeIdx = segments.findIndex(
    (seg) => currentTime >= seg.start_time && currentTime <= seg.end_time
  );
  const statesBySegmentId = new Map(
    states
      .filter((state) => state.segment_id)
      .map((state) => [state.segment_id as string, state])
  );

  // Scroll active segment into view
  useEffect(() => {
    if (activeItemRef.current && scrollContainerRef.current) {
      const container = scrollContainerRef.current;
      const element = activeItemRef.current;

      const elementTop = element.offsetTop;
      const elementHeight = element.offsetHeight;
      const containerScrollTop = container.scrollTop;
      const containerHeight = container.clientHeight;

      if (
        elementTop < containerScrollTop ||
        elementTop + elementHeight > containerScrollTop + containerHeight
      ) {
        container.scrollTo({
          top: elementTop - containerHeight / 2 + elementHeight / 2,
          behavior: 'smooth',
        });
      }
    }
  }, [activeIdx, segments.length]);

  if (!segments.length) {
    return (
      <div className="sc-transcript-card">
        <EmptyState
          icon={<MessageSquare size={32} />}
          title="Transcript will appear after analysis"
          description="No transcript is available yet. Upload real audio and start analysis to reveal speech segments."
        />
      </div>
    );
  }

  return (
    <div className="sc-transcript-card">
      <div className="sc-transcript-card__header">
        <div className="sc-transcript-card__title-group">
          <div className="sc-transcript-card__icon-badge">
            <MessageSquare size={16} className="text-lime" />
          </div>
          <div>
            <h3 className="text-h4 font-display" style={{ margin: 0 }}>Driver Radio Console Timeline</h3>
            <span className="text-micro font-telemetry">WHISPER ASR + ACOUSTIC ALIGNMENT</span>
          </div>
        </div>
        <span className="sc-transcript-card__count font-telemetry text-micro">
          {segments.length} Speech Segments
        </span>
      </div>

      <div ref={scrollContainerRef} className="sc-transcript-timeline">
        {segments.map((seg, i) => {
          const isActive = i === activeIdx;
          const driverState = statesBySegmentId.get(seg.id);
          const isStressFlagged = driverState?.dominant_emotion === 'stressed';

          return (
            <div
              key={seg.id}
              ref={isActive ? activeItemRef : null}
              className={`sc-transcript-item ${isStressFlagged ? 'sc-transcript-item--flagged' : ''} ${isActive ? 'sc-transcript-item--active' : ''}`}
              onClick={() => onSegmentClick && onSegmentClick(seg.start_time)}
              onKeyDown={(e) => {
                if ((e.key === 'Enter' || e.key === ' ') && onSegmentClick) {
                  e.preventDefault();
                  onSegmentClick(seg.start_time);
                }
              }}
              role={onSegmentClick ? 'button' : undefined}
              tabIndex={onSegmentClick ? 0 : undefined}
              aria-label={onSegmentClick ? `Seek audio to ${formatTime(seg.start_time)}: ${seg.text}` : undefined}
            >
              <div className="sc-transcript-item__left">
                <span className="sc-transcript-item__time font-telemetry">
                  <Clock size={10} />
                  {formatTime(seg.start_time)}
                </span>
                <div className={`sc-transcript-item__dot ${isStressFlagged ? 'sc-transcript-item__dot--alert' : ''} ${isActive ? 'sc-transcript-item__dot--active' : ''}`} />
                {i < segments.length - 1 && <div className="sc-transcript-item__line" />}
              </div>

              <div className="sc-transcript-item__body">
                <div className="sc-transcript-item__meta">
                  <span className={`sc-transcript-item__speaker font-telemetry ${(seg.speaker || '').toLowerCase().includes('engineer') ? 'sc-transcript-item__speaker--engineer' : ''}`}>
                    {seg.speaker || 'SPEAKER UNKNOWN'}
                  </span>

                  <span className="sc-transcript-item__conf font-telemetry text-micro">
                    <ShieldCheck size={11} />
                    {seg.confidence !== null && seg.confidence !== undefined
                      ? `${(seg.confidence * 100).toFixed(0)}% ASR`
                      : 'ASR N/A'}
                  </span>

                  {isStressFlagged && (
                    <span className="sc-transcript-item__flag font-telemetry text-micro">
                      <Zap size={10} />
                      STRESS ELEVATED · {(driverState.confidence * 100).toFixed(0)}% SER
                    </span>
                  )}
                </div>

                <p className="sc-transcript-item__text text-body">{seg.text}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TranscriptTimeline;
