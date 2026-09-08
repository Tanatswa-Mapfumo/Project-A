"""Unit tests for soreness analysis (section 14.3, Appendix B)."""

from app.rules.soreness import analyze_soreness


def test_exclusion_band():
    analysis = analyze_soreness({"quads": 9, "chest": 2})
    assert analysis.excluded_regions == ["quads"]
    assert analysis.excluded_muscles == {"quadriceps"}
    assert analysis.deprioritized_regions == []


def test_deprioritize_band():
    analysis = analyze_soreness({"hamstrings": 5, "chest": 4})
    assert analysis.deprioritized_regions == ["chest", "hamstrings"]
    assert analysis.deprioritized_muscles == {"hamstrings", "chest"}


def test_normal_band_ignored():
    analysis = analyze_soreness({"chest": 3})
    assert analysis.excluded_muscles == set()
    assert analysis.deprioritized_muscles == set()


def test_shoulder_region_maps_to_delts():
    analysis = analyze_soreness({"shoulders": 8})
    assert analysis.excluded_muscles == {"front_delts", "side_delts", "rear_delts"}


def test_joint_regions_are_conservative():
    knees = analyze_soreness({"knees": 8})
    assert knees.excluded_muscles == {"quadriceps", "hamstrings", "calves"}
    ankles = analyze_soreness({"ankles": 7})
    assert ankles.excluded_muscles == {"calves"}


def test_empty_map():
    analysis = analyze_soreness({})
    assert analysis.has_exclusions is False
