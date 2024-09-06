from datetime import date
from pydantic import BaseModel, Field


class Project(BaseModel):
    """Home load project."""

    property_value: float = Field(title="Property value ($)")
    start_capital: float = Field(title="Starting capital ($)", description="Amount of available capital for this purchase")
    monthly_income: float = Field(title="Monthly income ($)", description="After-tax income")
    monthly_costs: float = Field(title="Monthly costs ($)", description="Expected costs before repayment")
    settlement_date: date = Field(title="Settlement date", default_factory=lambda : date.today())
    stamp_duty_rate: float = Field(title="Stamp duty rate (%)", ge=0, le=100, default=0)
