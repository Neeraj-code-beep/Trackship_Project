"""Deterministic, evidence-backed race-engineering insight rules."""

from __future__ import annotations

from statistics import median
from typing import Any

from backend.app.analytics.correlation import (
    compute_fatigue_pace_correlation,
    compute_stint_fatigue_trend,
    compute_stress_pace_correlation,
)
from backend.app.schemas.schemas import (
    AlignedLapEmotion,
    EmotionLabel,
    InsightItem,
    InsightPriority,
    InsightSeverity,
)

PACE_DEGRADATION_THRESHOLD_SECONDS = 1.0
ELEVATED_STATE_SCORE = 60.0


def generate_insights(aligned_laps: list[AlignedLapEmotion]) -> list[InsightItem]:
    """Evaluate cautious rules, order by priority, and assign stable IDs."""
    candidates: list[dict[str, Any]] = []
    if not aligned_laps:
        candidates.append(
            _candidate(
                priority=InsightPriority.LOW,
                insight_type="no_lap_data",
                title="Lap context unavailable",
                category="Data",
                message="No lap timing was available for state-performance analysis.",
                evidence={"usable_laps": 0},
            )
        )
        return _finalize(candidates)

    stress_correlation = compute_stress_pace_correlation(aligned_laps)
    fatigue_correlation = compute_fatigue_pace_correlation(aligned_laps)
    fatigue_trend = compute_stint_fatigue_trend(aligned_laps)

    if stress_correlation.pearson_r is not None and stress_correlation.pearson_r >= 0.4:
        priority = (
            InsightPriority.HIGH if stress_correlation.pearson_r >= 0.7 else InsightPriority.MEDIUM
        )
        candidates.append(
            _candidate(
                priority=priority,
                insight_type="stress_pace_association",
                title="Stress signal rose with pace loss",
                category="Stress-Performance",
                message=(
                    "Stress-related vocal scores were positively associated with "
                    "slower-than-baseline laps. Review concurrent radio and handling context; "
                    "the association does not establish causation."
                ),
                evidence={
                    "pearson_r": stress_correlation.pearson_r,
                    "sample_size": stress_correlation.sample_size,
                    "strength": stress_correlation.strength,
                },
            )
        )

    if fatigue_trend.trend == "rising":
        evidence: dict[str, Any] = {
            "fatigue_change": fatigue_trend.change,
            "early_average": fatigue_trend.early_average,
            "late_average": fatigue_trend.late_average,
            "sample_size": fatigue_trend.sample_size,
        }
        if fatigue_correlation.pearson_r is not None:
            evidence["pace_correlation_r"] = fatigue_correlation.pearson_r
        candidates.append(
            _candidate(
                priority=InsightPriority.MEDIUM,
                insight_type="rising_fatigue_signal",
                title="Estimated fatigue-related signal increased",
                category="Fatigue Trend",
                message=(
                    "Estimated fatigue-related vocal scores were higher in the late-session "
                    "sample than the early-session sample. This is a heuristic vocal pattern, "
                    "not a medical assessment."
                ),
                evidence=evidence,
            )
        )

    usable_with_state = [
        lap for lap in aligned_laps if lap.segment_ids and not lap.is_timing_outlier
    ]
    if usable_with_state:
        best_lap = min(usable_with_state, key=lambda lap: lap.lap_time_seconds)
        median_stress = float(median(lap.stress_score for lap in usable_with_state))
        if (
            best_lap.dominant_emotion is EmotionLabel.CALM
            and best_lap.calm_score >= 50.0
            and best_lap.stress_score <= median_stress
        ):
            candidates.append(
                _candidate(
                    priority=InsightPriority.LOW,
                    insight_type="calm_best_lap",
                    title="Fastest analyzed lap aligned with a calm state",
                    category="Peak Performance",
                    message=(
                        "The fastest lap with radio evidence occurred during a comparatively "
                        "calm fused driver-state estimate."
                    ),
                    evidence={
                        "lap_number": best_lap.lap_number,
                        "lap_time_seconds": best_lap.lap_time_seconds,
                        "calm_score": best_lap.calm_score,
                        "stress_score": best_lap.stress_score,
                        "session_median_stress_score": round(median_stress, 1),
                    },
                    lap_number=best_lap.lap_number,
                )
            )

    anomalies = sorted(
        (
            lap
            for lap in aligned_laps
            if not lap.is_timing_outlier
            and lap.segment_ids
            and lap.lap_delta >= PACE_DEGRADATION_THRESHOLD_SECONDS
            and max(lap.stress_score, lap.fatigue_score) >= ELEVATED_STATE_SCORE
        ),
        key=lambda lap: lap.lap_delta,
        reverse=True,
    )[:2]
    for lap in anomalies:
        signal = "stress" if lap.stress_score >= lap.fatigue_score else "estimated fatigue"
        state_score = max(lap.stress_score, lap.fatigue_score)
        priority = (
            InsightPriority.HIGH
            if lap.lap_delta >= 2.0 and state_score >= 70.0
            else InsightPriority.MEDIUM
        )
        candidates.append(
            _candidate(
                priority=priority,
                insight_type="state_pace_degradation",
                title=f"Lap {lap.lap_number} combined elevated state and pace loss",
                category="Pace Anomaly",
                message=(
                    f"Lap {lap.lap_number} was slower than the session median while the "
                    f"{signal} vocal score was elevated. Investigate concurrent race context."
                ),
                evidence={
                    "lap_number": lap.lap_number,
                    "lap_delta_seconds": lap.lap_delta,
                    "stress_score": lap.stress_score,
                    "fatigue_score": lap.fatigue_score,
                },
                lap_number=lap.lap_number,
            )
        )

    if not candidates:
        candidates.append(
            _candidate(
                priority=InsightPriority.LOW,
                insight_type="insufficient_evidence",
                title="No material state-performance pattern detected",
                category="Data",
                message=(
                    "Available lap and radio evidence did not cross the configured insight "
                    "thresholds."
                ),
                evidence={
                    "laps_with_state": len(usable_with_state),
                    "stress_correlation_reason": stress_correlation.reason,
                    "fatigue_correlation_reason": fatigue_correlation.reason,
                    "fatigue_trend": fatigue_trend.trend,
                },
            )
        )
    return _finalize(candidates)


def _candidate(
    *,
    priority: InsightPriority,
    insight_type: str,
    title: str,
    category: str,
    message: str,
    evidence: dict[str, Any],
    lap_number: int | None = None,
) -> dict[str, Any]:
    return {
        "priority": priority,
        "type": insight_type,
        "title": title,
        "category": category,
        "message": message,
        "evidence": evidence,
        "lap_number": lap_number,
    }


def _finalize(candidates: list[dict[str, Any]]) -> list[InsightItem]:
    rank = {
        InsightPriority.HIGH: 0,
        InsightPriority.MEDIUM: 1,
        InsightPriority.LOW: 2,
    }
    ordered = sorted(
        candidates,
        key=lambda item: (
            rank[item["priority"]],
            item["type"],
            item["lap_number"] or 0,
        ),
    )
    insights: list[InsightItem] = []
    for index, item in enumerate(ordered, start=1):
        priority = item["priority"]
        severity = (
            InsightSeverity.INFO if priority is InsightPriority.LOW else InsightSeverity.WARNING
        )
        insights.append(
            InsightItem(
                id=f"insight_{index:03d}",
                severity=severity,
                priority=priority,
                type=item["type"],
                title=item["title"],
                category=item["category"],
                message=item["message"],
                evidence=item["evidence"],
                data=item["evidence"],
                lap_number=item["lap_number"],
            )
        )
    return insights
