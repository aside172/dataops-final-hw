from dataclasses import dataclass
from math import exp


@dataclass(slots=True)
class PredictionResult:
    risk_score: float
    will_default: bool
    version: str


class CreditRiskModel:
    def __init__(self, version: str, threshold: float) -> None:
        self.version = version
        self.threshold = threshold

    def predict(self, income: float, debt: float, utilization: float) -> PredictionResult:
        normalized_income = min(max(income / 10000, 0.0), 20.0)
        normalized_debt = min(max(debt / 5000, 0.0), 20.0)
        normalized_utilization = min(max(utilization, 0.0), 1.5)

        logit = -2.35 + (normalized_debt * 0.42) + (normalized_utilization * 2.15) - (normalized_income * 0.18)
        score = 1 / (1 + exp(-logit))
        return PredictionResult(
            risk_score=round(score, 6),
            will_default=score >= self.threshold,
            version=self.version,
        )
