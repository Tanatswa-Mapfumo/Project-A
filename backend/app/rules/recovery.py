"""Recovery score rules (section 14.1).

energy_component = energy_score
sleep_component  = sleep_score
mood_component   = mood_score
stress_component = 11 - stress_score
pain_component   = 10 if pain is null else (11 - pain_score)

recovery = 0.30*energy + 0.25*sleep + 0.15*mood + 0.20*stress + 0.10*pain
"""

from app.rules.config import RECOVERY_WEIGHTS


def compute_recovery_score(
    energy_score: int,
    sleep_score: int,
    mood_score: int,
    stress_score: int,
    pain_score: int | None,
) -> float:
    components = {
        "energy": float(energy_score),
        "sleep": float(sleep_score),
        "mood": float(mood_score),
        "stress": float(11 - stress_score),
        "pain": 10.0 if pain_score is None else float(11 - pain_score),
    }
    score = sum(RECOVERY_WEIGHTS[name] * value for name, value in components.items())
    return round(score, 1)
