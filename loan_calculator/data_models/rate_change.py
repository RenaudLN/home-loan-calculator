from datetime import date as date_
from pydantic import BaseModel, Field


class RateDelta(BaseModel):
    """Rate change."""

    date: date_ = Field(title="Date")
    value: float = Field(title="Value (%)")


class RatesForecast(BaseModel):
    """Rate forecast."""

    changes: list[RateDelta] = Field(
        title="Interest rates projection",
        description="Note: The rate changes should be relative to the current value.",
        default_factory=list,
    )
