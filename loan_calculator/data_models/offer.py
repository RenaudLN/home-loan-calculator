from pydantic import BaseModel, Field, model_validator


class Offer(BaseModel):
    """Loan offer."""

    name: str = Field(title="Name")
    rate: float = Field(title="Annual interest rate (%)", default=3, ge=0, le=100)
    borrowed_share: float = Field(title="Borrowed share (%)", default=80, ge=0, le=100)
    loan_duration: float = Field(title="Loan duration (years)", default=25, ge=1)
    yearly_fees: float = Field(title="Yearly fees ($)", default=0, ge=0)
    with_fixed_rate: bool = Field(title="With fixed rate", default=False)
    fixed_rate: float | None = Field(title="Fixed rate (%)", default=None)
    fixed_rate_duration: int | None = Field(title="Fixed rate duration (years)", default=None)
    with_offset_account: bool = Field(title="With offset account", default=False)

    @model_validator(mode="after")
    def validate_fixed_rate(self):
        if self.with_fixed_rate and (self.fixed_rate is None or self.fixed_rate_duration is None):
            raise ValueError("fixed_rate and fixed_rate_duration are required when with_fixed_rate is True")
        return self
