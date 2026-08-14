"""
Insights generator module.
Produces automated race-engineering observations from correlated data.
"""

from __future__ import annotations

from backend.app.schemas.schemas import (
    AlignedLapEmotion,
    InsightItem,
    InsightSeverity,
    EmotionLabel,
)
from backend.app.analytics.correlation import (
    compute_stress_pace_correlation,
    compute_fatigue_pace_correlation,
    detect_performance_anomalies,
    compute_stint_fatigue_trend,
)


def generate_insights(
    aligned_laps: list[AlignedLapEmotion],
) -> list[InsightItem]:
    """
    Analyze aligned lap/emotion data and produce a list of actionable
    race-engineering insights.
    """
    insights: list[InsightItem] = []

    if not aligned_laps:
        insights.append(
            InsightItem(
                severity=InsightSeverity.INFO,
                category="Data",
                message="No lap data available for analysis. Upload lap timing to enable insights.",
            )
        )
        return insights

    # ── 1. Stress-Pace Correlation ────────────────────────────────────────
    stress_corr = compute_stress_pace_correlation(aligned_laps)
    if stress_corr > 0.5:
        insights.append(
            InsightItem(
                severity=InsightSeverity.WARNING,
                category="Stress-Performance",
                message=(
                    f"Strong positive correlation ({stress_corr:.2f}) between driver stress "
                    f"and lap time degradation. Consider radio encouragement or strategy change."
                ),
                data={"correlation": stress_corr},
            )
        )
    elif stress_corr > 0.25:
        insights.append(
            InsightItem(
                severity=InsightSeverity.INFO,
                category="Stress-Performance",
                message=(
                    f"Moderate stress-pace correlation ({stress_corr:.2f}) detected. "
                    f"Driver performance slightly impacted under stress."
                ),
                data={"correlation": stress_corr},
            )
        )

    # ── 2. Fatigue-Pace Correlation ───────────────────────────────────────
    fatigue_corr = compute_fatigue_pace_correlation(aligned_laps)
    if fatigue_corr > 0.5:
        insights.append(
            InsightItem(
                severity=InsightSeverity.CRITICAL,
                category="Fatigue-Performance",
                message=(
                    f"High fatigue-pace correlation ({fatigue_corr:.2f}). "
                    f"Driver tiredness is significantly impacting lap times. "
                    f"Recommend pit stop or safety car period to recover."
                ),
                data={"correlation": fatigue_corr},
            )
        )
    elif fatigue_corr > 0.25:
        insights.append(
            InsightItem(
                severity=InsightSeverity.WARNING,
                category="Fatigue-Performance",
                message=(
                    f"Moderate fatigue-pace correlation ({fatigue_corr:.2f}). "
                    f"Monitor driver tiredness closely."
                ),
                data={"correlation": fatigue_corr},
            )
        )

    # ── 3. Performance Anomalies ──────────────────────────────────────────
    anomalies = detect_performance_anomalies(aligned_laps, delta_threshold=1.0)
    for anomaly in anomalies:
        sev = (
            InsightSeverity.CRITICAL
            if anomaly["severity"] == "critical"
            else InsightSeverity.WARNING
        )
        insights.append(
            InsightItem(
                severity=sev,
                category="Pace Anomaly",
                message=(
                    f"Lap {anomaly['lap_number']}: +{anomaly['delta_to_best']:.3f}s off best pace. "
                    f"Driver was {anomaly['dominant_emotion']} "
                    f"(stress={anomaly['stress_level']:.0%}, fatigue={anomaly['fatigue_level']:.0%})."
                ),
                lap_number=anomaly["lap_number"],
                data=anomaly,
            )
        )

    # ── 4. Stint Fatigue Trend ────────────────────────────────────────────
    trends = compute_stint_fatigue_trend(aligned_laps, window=3)
    increasing_trends = [t for t in trends if t["trend"] == "increasing"]
    if increasing_trends:
        last_trend = increasing_trends[-1]
        insights.append(
            InsightItem(
                severity=InsightSeverity.WARNING,
                category="Fatigue Trend",
                message=(
                    f"Rising fatigue trend detected from Lap {last_trend['lap_start']} "
                    f"to Lap {last_trend['lap_end']} "
                    f"(avg fatigue: {last_trend['avg_fatigue']:.0%}). "
                    f"Pace degrading by +{last_trend['avg_delta']:.3f}s average."
                ),
                lap_number=last_trend["lap_end"],
                data=last_trend,
            )
        )

    # ── 5. Best Lap Emotion ───────────────────────────────────────────────
    best_lap = min(aligned_laps, key=lambda l: l.lap_time_seconds)
    insights.append(
        InsightItem(
            severity=InsightSeverity.INFO,
            category="Peak Performance",
            message=(
                f"Best lap ({best_lap.lap_number}): {best_lap.lap_time_seconds:.3f}s. "
                f"Driver was {best_lap.dominant_emotion.value} "
                f"(stress={best_lap.stress_level:.0%})."
            ),
            lap_number=best_lap.lap_number,
        )
    )

    # ── 6. Overall stress summary ─────────────────────────────────────────
    avg_stress = sum(l.stress_level for l in aligned_laps) / len(aligned_laps)
    avg_fatigue = sum(l.fatigue_level for l in aligned_laps) / len(aligned_laps)

    if avg_stress > 0.5:
        insights.append(
            InsightItem(
                severity=InsightSeverity.WARNING,
                category="Session Summary",
                message=(
                    f"High average stress ({avg_stress:.0%}) across {len(aligned_laps)} laps. "
                    f"Review track conditions and driver comfort."
                ),
            )
        )
    
    if avg_fatigue > 0.3:
        insights.append(
            InsightItem(
                severity=InsightSeverity.WARNING,
                category="Session Summary",
                message=(
                    f"Elevated average fatigue ({avg_fatigue:.0%}). "
                    f"Consider shorter stints in future sessions."
                ),
            )
        )

    return insights
