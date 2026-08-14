"""Transparent fusion of SER, acoustics, and transcript urgency signals."""

from __future__ import annotations

import math
import re

from backend.app.schemas.schemas import (
    AcousticAnalysis,
    AcousticFeatures,
    DriverState,
    EmotionLabel,
    EmotionProbabilities,
    TranscriptSegment,
)

STRESS_WEIGHTS = {
    "emotion": 0.45,
    "energy": 0.15,
    "pitch_variability": 0.15,
    "speech_rate": 0.10,
    "urgency": 0.15,
}

FATIGUE_WEIGHTS = {
    "emotion": 0.15,
    "low_energy": 0.25,
    "low_pitch_variability": 0.20,
    "slow_speech": 0.15,
    "pause_ratio": 0.20,
    "low_voiced_ratio": 0.05,
}

CALM_WEIGHTS = {
    "emotion": 0.55,
    "stable_energy": 0.15,
    "stable_pitch": 0.10,
    "steady_speech": 0.10,
    "low_urgency": 0.10,
}

STATE_THRESHOLD = 50.0
STATE_MARGIN = 5.0
URGENCY_TERMS = frozenset(
    {
        "box",
        "brake",
        "brakes",
        "danger",
        "help",
        "lose",
        "losing",
        "lost",
        "power",
        "problem",
        "stop",
        "tyre",
        "tyres",
        "urgent",
    }
)


def fuse_driver_states(
    emotion_states: list[DriverState],
    acoustics: AcousticAnalysis,
    transcript_segments: list[TranscriptSegment],
) -> list[DriverState]:
    """Produce application driver states from aligned per-segment evidence."""
    acoustic_by_id = {record.segment_id: record for record in acoustics.segments}
    transcript_by_id = {segment.id: segment for segment in transcript_segments}
    results: list[DriverState] = []

    for emotion in emotion_states:
        safe_emotion = emotion.model_copy(
            update={
                "probabilities": _sanitized_probabilities(emotion.probabilities),
                "raw_emotions": {
                    label: _unit(score) for label, score in emotion.raw_emotions.items()
                },
            }
        )
        segment_id = emotion.segment_id or ""
        acoustic_record = acoustic_by_id.get(segment_id)
        transcript = transcript_by_id.get(segment_id)
        features = acoustic_record.features if acoustic_record else None
        deviations = acoustic_record.session_deviations if acoustic_record else {}
        text = transcript.text if transcript else None

        signals = _signals(safe_emotion, features, deviations, text)
        stress_score = _weighted_score(
            STRESS_WEIGHTS,
            {
                "emotion": signals["emotion_stress"],
                "energy": signals["high_energy"],
                "pitch_variability": signals["high_pitch_variability"],
                "speech_rate": signals["fast_speech"],
                "urgency": signals["transcript_urgency"],
            },
        )
        fatigue_score = _weighted_score(
            FATIGUE_WEIGHTS,
            {
                "emotion": signals["emotion_fatigue"],
                "low_energy": signals["low_energy"],
                "low_pitch_variability": signals["low_pitch_variability"],
                "slow_speech": signals["slow_speech"],
                "pause_ratio": signals["pause_ratio"],
                "low_voiced_ratio": signals["low_voiced_ratio"],
            },
        )
        calm_score = _weighted_score(
            CALM_WEIGHTS,
            {
                "emotion": signals["emotion_calm"],
                "stable_energy": signals["stable_energy"],
                "stable_pitch": signals["stable_pitch"],
                "steady_speech": signals["steady_speech"],
                "low_urgency": signals["low_urgency"],
            },
        )
        state = _select_state(stress_score, fatigue_score, calm_score)
        confidence = _confidence(
            state,
            safe_emotion.confidence,
            features,
            deviations,
            (stress_score, fatigue_score, calm_score),
        )
        drivers = _explanations(state, signals)

        results.append(
            safe_emotion.model_copy(
                update={
                    "dominant_emotion": state,
                    "confidence": confidence,
                    "stress_score": stress_score,
                    "fatigue_score": fatigue_score,
                    "calm_score": calm_score,
                    "signals": signals,
                    "drivers": drivers,
                    "acoustic_features": features,
                    "rms_energy": features.rms_energy if features else None,
                    "speech_rate_wpm": features.speech_rate_wpm if features else None,
                }
            )
        )
    return results


def _signals(
    emotion: DriverState,
    features: AcousticFeatures | None,
    deviations: dict[str, float],
    text: str | None,
) -> dict[str, float]:
    energy = _deviation(deviations, "rms_energy")
    pitch = _deviation(deviations, "pitch_std_hz")
    speech_rate = _deviation(deviations, "speech_rate_wpm")
    urgency = _urgency_score(text) if text is not None else 0.0

    return {
        "emotion_stress": _unit(emotion.probabilities.stressed),
        "emotion_fatigue": _unit(emotion.probabilities.tired),
        "emotion_calm": _unit(emotion.probabilities.calm),
        "high_energy": max(energy, 0.0),
        "low_energy": max(-energy, 0.0),
        "high_pitch_variability": max(pitch, 0.0),
        "low_pitch_variability": max(-pitch, 0.0),
        "fast_speech": max(speech_rate, 0.0),
        "slow_speech": max(-speech_rate, 0.0),
        "stable_energy": _stability(deviations, "rms_energy"),
        "stable_pitch": _stability(deviations, "pitch_std_hz"),
        "steady_speech": _stability(deviations, "speech_rate_wpm"),
        "pause_ratio": _unit(features.pause_ratio if features else 0.0),
        "low_voiced_ratio": _unit(1.0 - features.voiced_ratio if features else 0.0),
        "transcript_urgency": urgency,
        "low_urgency": 1.0 - urgency if text is not None else 0.0,
    }


def _weighted_score(weights: dict[str, float], signals: dict[str, float]) -> float:
    total = sum(weights[name] * _unit(signals.get(name, 0.0)) for name in weights)
    return round(min(max(total * 100.0, 0.0), 100.0), 1)


def _select_state(stress: float, fatigue: float, calm: float) -> EmotionLabel:
    scored = [
        (EmotionLabel.STRESSED, stress),
        (EmotionLabel.TIRED, fatigue),
        (EmotionLabel.CALM, calm),
    ]
    scored.sort(key=lambda item: item[1], reverse=True)
    (best_state, best_score), (_, second_score) = scored[:2]
    if best_score >= STATE_THRESHOLD and best_score - second_score >= STATE_MARGIN:
        return best_state
    return EmotionLabel.NEUTRAL


def _confidence(
    state: EmotionLabel,
    emotion_confidence: float,
    features: AcousticFeatures | None,
    deviations: dict[str, float],
    scores: tuple[float, float, float],
) -> float:
    evidence = 0
    evidence += int("rms_energy" in deviations)
    evidence += int("pitch_std_hz" in deviations and features is not None)
    evidence += int("speech_rate_wpm" in deviations and features is not None)
    evidence += int(features is not None)
    evidence += int(features is not None and features.voiced_ratio > 0)
    completeness = evidence / 5.0

    ordered = sorted(scores, reverse=True)
    if state is EmotionLabel.NEUTRAL:
        separation = 1.0 - min(ordered[0] / STATE_THRESHOLD, 1.0)
    else:
        separation = (ordered[0] - ordered[1]) / 100.0
    confidence = 0.5 * _unit(emotion_confidence) + 0.3 * completeness + 0.2 * _unit(separation)
    return round(_unit(confidence), 2)


def _explanations(state: EmotionLabel, signals: dict[str, float]) -> list[str]:
    drivers: list[str] = []
    if state is EmotionLabel.STRESSED:
        if signals["emotion_stress"] >= 0.5:
            drivers.append("elevated speech-emotion stress probability")
        if signals["high_energy"] >= 0.35:
            drivers.append("higher-than-session-median vocal energy")
        if signals["high_pitch_variability"] >= 0.35:
            drivers.append("higher-than-session-median pitch variability")
        if signals["fast_speech"] >= 0.35:
            drivers.append("faster-than-session-median speech rate")
        if signals["transcript_urgency"] >= 0.35:
            drivers.append("urgent language in the radio transcript")
    elif state is EmotionLabel.TIRED:
        if signals["emotion_fatigue"] >= 0.3:
            drivers.append("fatigue-related speech-emotion model evidence")
        if signals["low_energy"] >= 0.35:
            drivers.append("lower-than-session-median vocal energy")
        if signals["low_pitch_variability"] >= 0.35:
            drivers.append("lower-than-session-median pitch variability")
        if signals["slow_speech"] >= 0.35:
            drivers.append("slower-than-session-median speech rate")
        if signals["pause_ratio"] >= 0.4:
            drivers.append("higher pause proportion in the speech segment")
    elif state is EmotionLabel.CALM:
        if signals["emotion_calm"] >= 0.5:
            drivers.append("elevated calm speech-emotion probability")
        if signals["stable_energy"] >= 0.7:
            drivers.append("vocal energy close to the session median")
        if signals["low_urgency"] >= 0.8:
            drivers.append("low transcript urgency signal")
    else:
        drivers.append(
            f"no fused state score crossed the {STATE_THRESHOLD:.0f}-point decision threshold"
        )
    return drivers or ["available evidence was mixed across state signals"]


def _urgency_score(text: str) -> float:
    words = set(re.findall(r"\b[\w']+\b", text.lower()))
    keyword_score = min(len(words.intersection(URGENCY_TERMS)) / 3.0, 1.0)
    punctuation_score = min(text.count("!") * 0.1, 0.2)
    return _unit(keyword_score + punctuation_score)


def _deviation(deviations: dict[str, float], key: str) -> float:
    value = deviations.get(key, 0.0)
    if not math.isfinite(float(value)):
        return 0.0
    return min(max(float(value), -1.0), 1.0)


def _stability(deviations: dict[str, float], key: str) -> float:
    if key not in deviations:
        return 0.0
    return 1.0 - abs(_deviation(deviations, key))


def _unit(value: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(number):
        return 0.0
    return min(max(number, 0.0), 1.0)


def _sanitized_probabilities(probabilities: EmotionProbabilities) -> EmotionProbabilities:
    values = {
        "calm": _unit(probabilities.calm),
        "stressed": _unit(probabilities.stressed),
        "neutral": _unit(probabilities.neutral),
        "tired": _unit(probabilities.tired),
    }
    total = sum(values.values())
    if total <= 0:
        values["neutral"] = 1.0
        total = 1.0
    return EmotionProbabilities(**{key: value / total for key, value in values.items()})
