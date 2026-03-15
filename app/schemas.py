from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    income: float = Field(gt=0, description="Monthly income in USD")
    debt: float = Field(ge=0, description="Outstanding debt in USD")
    utilization: float = Field(ge=0, le=1, description="Credit utilization ratio")


class PredictResponse(BaseModel):
    risk_score: float
    will_default: bool
    model_version: str
    duration_ms: float
