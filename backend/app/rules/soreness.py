"""Soreness analysis rules (section 14.3).

1-3 -> normal
4-6 -> deprioritize
7-10 -> exclude exercises whose primary muscle groups strongly load that region
"""

from dataclasses import dataclass, field

from app.rules.config import (
    BODY_REGION_TO_MUSCLES,
    SORENESS_DEPRIORITIZE_MIN,
    SORENESS_EXCLUDE_MIN,
)


@dataclass
class SorenessAnalysis:
    excluded_regions: list[str] = field(default_factory=list)
    deprioritized_regions: list[str] = field(default_factory=list)
    excluded_muscles: set[str] = field(default_factory=set)
    deprioritized_muscles: set[str] = field(default_factory=set)

    @property
    def has_exclusions(self) -> bool:
        return bool(self.excluded_muscles)


def analyze_soreness(soreness_map: dict[str, int]) -> SorenessAnalysis:
    analysis = SorenessAnalysis()
    for region, score in sorted(soreness_map.items()):
        muscles = BODY_REGION_TO_MUSCLES.get(region, [])
        if score >= SORENESS_EXCLUDE_MIN:
            analysis.excluded_regions.append(region)
            analysis.excluded_muscles.update(muscles)
        elif score >= SORENESS_DEPRIORITIZE_MIN:
            analysis.deprioritized_regions.append(region)
            analysis.deprioritized_muscles.update(muscles)
    return analysis
