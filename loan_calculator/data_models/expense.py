from datetime import date as date_
from pydantic import BaseModel, Field


class Expense(BaseModel):
    """Rate change."""

    date: date_ = Field(title="Date")
    value: float = Field(title="Expense ($)")


class FutureExpenses(BaseModel):
    """Rate forecast."""

    expenses: list[Expense] = Field(
        title="Future expenses",
        description="Additional expenses not considered in the monthly costs, "
        "e.g. a car or a wedding. Impacts the offset account balance.",
        default_factory=list,
    )
