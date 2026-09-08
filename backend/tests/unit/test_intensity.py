"""Unit tests for intensity selection (section 14.2)."""

from app.core.enums import Intensity
from app.rules.intensity import select_intensity


def test_low_recovery_selects_low():
    assert select_intensity(3.0, None, 7, 3) == Intensity.LOW


def test_moderate_recovery_selects_moderate():
    assert select_intensity(6.0, None, 7, 4) == Intensity.MODERATE


def test_high_recovery_selects_high():
    assert select_intensity(8.0, None, 8, 3) == Intensity.HIGH


def test_boundaries():
    assert select_intensity(4.5, None, 7, 4) == Intensity.MODERATE
    assert select_intensity(7.0, None, 7, 4) == Intensity.HIGH


def test_pain_caps_intensity_to_low():
    assert select_intensity(9.0, 6, 9, 2) == Intensity.LOW
    assert select_intensity(9.0, 5, 9, 2) == Intensity.HIGH


def test_sleep_caps_intensity_to_low():
    assert select_intensity(9.0, None, 3, 2) == Intensity.LOW
    assert select_intensity(9.0, None, 4, 2) == Intensity.HIGH


def test_stress_caps_intensity_to_low():
    assert select_intensity(9.0, None, 9, 9) == Intensity.LOW
    assert select_intensity(9.0, None, 9, 8) == Intensity.HIGH
