"""
Insights generator module.
Produces automated race-engineering observations from correlated data.
"""

from __future__ import annotations

from backend.app.analytics.correlation import (
    compute_fatigue_pace_correlation,
    compute_stint_fatigue_trend,
    compute_stress_pace_correlation,
    detect_performance_anomalies,
)
from backend.app.schemas.schemas import (
    AlignedLapEmotion,
    InsightItem,
    InsightSeverity,
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
    stress_result = compute_stress_pace_correlation(aligned_laps)
    stress_corr = stress_result.pearson_r
    if stress_corr is not None and stress_corr > 0.5:
        insights.append(
            InsightItem(
                severity=InsightSeverity.WARNING,
                category="Stress-Performance",
                message=(
                    f"Strong positive correlation ({stress_corr:.2f}) between driver stress "
                    f"and lap time degradation; this is an association, not causation."
                ),
                data=stress_result.model_dump(),
            )
        )
    elif stress_corr is not None and stress_corr > 0.25:
        insights.append(
            InsightItem(
                severity=InsightSeverity.INFO,
                category="Stress-Performance",
                message=(
                    f"Moderate stress-pace correlation ({stress_corr:.2f}) detected. "
                    f"Review the concurrent signals without assuming causation."
                ),
                data=stress_result.model_dump(),
            )
        )

    # ── 2. Fatigue-Pace Correlation ───────────────────────────────────────
    fatigue_result = compute_fatigue_pace_correlation(aligned_laps)
    fatigue_corr = fatigue_result.pearson_r
    if fatigue_corr is not None and fatigue_corr > 0.5:
        insights.append(
            InsightItem(
                severity=InsightSeverity.CRITICAL,
                category="Fatigue-Performance",
                message=(
                    f"High fatigue-pace correlation ({fatigue_corr:.2f}). "
                    f"Estimated fatigue-related vocal signals and slower laps moved together. "
                    f"Review the concurrent stint data."
                ),
                data=fatigue_result.model_dump(),
            )
        )
    elif fatigue_corr is not None and fatigue_corr > 0.25:
        insights.append(
            InsightItem(
                severity=InsightSeverity.WARNING,
                category="Fatigue-Performance",
                message=(
                    f"Moderate fatigue-pace correlation ({fatigue_corr:.2f}). "
                    f"Monitor the estimated vocal pattern alongside pace."
                ),
                data=fatigue_result.model_dump(),
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
                    f"(stress={anomaly['stress_level']:.0%}, "
                    f"fatigue={anomaly['fatigue_level']:.0%})."
                ),
                lap_number=anomaly["lap_number"],
                data=anomaly,
            )
        )

    # ── 4. Stint Fatigue Trend ────────────────────────────────────────────
    fatigue_trend = compute_stint_fatigue_trend(aligned_laps)
    if fatigue_trend.trend == "rising":
        insights.append(
            InsightItem(
                severity=InsightSeverity.WARNING,
                category="Fatigue Trend",
                message=(
                    "Estimated fatigue-related vocal signals increased from the early "
                    f"to late session sample by {fatigue_trend.change:.1f} points."
                ),
                data=fatigue_trend.model_dump(),
            )
        )

    # ── 5. Best Lap Emotion ───────────────────────────────────────────────
    best_lap = min(aligned_laps, key=lambda lap: lap.lap_time_seconds)
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
    avg_stress = sum(lap.stress_level for lap in aligned_laps) / len(aligned_laps)
    avg_fatigue = sum(lap.fatigue_level for lap in aligned_laps) / len(aligned_laps)

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
