"""Intensity selection rules (section 14.2).

Base rule: recovery < 4.5 -> low; 4.5 <= recovery < 7 -> moderate; >= 7 -> high.
Caps: pain >= 6, sleep <= 3, or stress >= 9 -> maximum intensity is low.
"""

from app.core.enums import Intensity
from app.rules.config import (
    INTENSITY_HIGH_THRESHOLD,
    INTENSITY_LOW_THRESHOLD,
    PAIN_INTENSITY_CAP,
    SLEEP_INTENSITY_CAP,
    STRESS_INTENSITY_CAP,
)

_INTENSITY_ORDER = [Intensity.LOW, Intensity.MODERATE, Intensity.HIGH]


def _cap(intensity: Intensity, cap_level: Intensity) -> Intensity:
    if _INTENSITY_ORDER.index(intensity) > _INTENSITY_ORDER.index(cap_level):
        return cap_level
    return intensity


def select_intensity(
    recovery_score: float,
    pain_score: int | None,
    sleep_score: int,
    stress_score: int,
) -> Intensity:
    if recovery_score < INTENSITY_LOW_THRESHOLD:
        intensity = Intensity.LOW
    elif recovery_score < INTENSITY_HIGH_THRESHOLD:
        intensity = Intensity.MODERATE
    else:
        intensity = Intensity.HIGH

    if (pain_score is not None and pain_score >= PAIN_INTENSITY_CAP) or (
        sleep_score <= SLEEP_INTENSITY_CAP or stress_score >= STRESS_INTENSITY_CAP
    ):
        intensity = _cap(intensity, Intensity.LOW)
    return intensity
