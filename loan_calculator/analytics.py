from datetime import date
from functools import lru_cache

import numpy as np
import pandas as pd
from numba import njit

from loan_calculator.data_models import FutureExpenses, Offer, Project, RatesForecast


def compute_loan_timeseries(  # pylint: disable = too-many-arguments, too-many-locals, unused-argument
    *,
    project: Project,
    offer: Offer,
    rates_change: RatesForecast,
    expenses: FutureExpenses,
    **kwargs,
) -> tuple[pd.DataFrame, bool]:
    """Compute the loan timeseries

    :param property_value: Property value in $
    :param rate: Annual loan rate in %
    :param borrowed_share: Borrowed share in %
    :param loan_duration: Load duration in years
    :param start_capital: Starting capital in $
    :param stamp_duty_rate: Stamp duty rate in %
    :param monthly_income: After-tax monthly income in $
    :param monthly_costs: Monthly costs before repayment in $
    :param with_offset_account: Whether the loan includes an offset account
    :param yearly_fees: Yearly loan management fees in $
    :param settlement_date: Settlement date
    :return: Loan data timeseries
    """

    # Define the loan period
    date_period = pd.date_range(
        project.settlement_date,
        project.settlement_date + pd.Timedelta(days=offer.loan_duration * 365),
        freq="MS",
        inclusive="left",
    )

    # Define the loan princpal
    principal = project.property_value * offer.borrowed_share / 100

    # Define how much savings can be left in the offset account after deposit + stamp duty
    start_offset = (
        project.start_capital - project.property_value * (100 - offer.borrowed_share + project.stamp_duty_rate) / 100
    ) * offer.with_offset_account

    # Define the monthly loan rate and fee
    monthly_rate = get_monthly_rate_series(
        date_period=date_period,
        rate=offer.rate,
        rates_change=rates_change,
        with_fixed_rate=offer.with_fixed_rate,
        fixed_rate=offer.fixed_rate,
        fixed_rate_duration=offer.fixed_rate_duration,
        settlement_date=project.settlement_date,
    )
    monthly_fee = offer.yearly_fees / 12

    expenses_series = get_expenses_series(date_period=date_period, expenses=expenses)

    repayments = np.c_[
        calculate_repayments(
            monthly_rate.to_numpy(),
            start_offset,
            principal,
            monthly_fee,
            project.monthly_income,
            project.monthly_costs,
            expenses_series.to_numpy(),
            offer.with_offset_account,
        )
    ]
    data = pd.DataFrame(
        repayments,
        columns=[
            "principal_paid",
            "offset",
            "principal_payment",
            "interest",
            "fee",
            "repayment",
        ],
        index=date_period,
    ).assign(deposit=0, stamp_duty=0)
    data.at[data.index[0], "deposit"] = project.property_value * (100 - offer.borrowed_share) / 100
    data.at[data.index[0], "stamp_duty"] = project.property_value * (project.stamp_duty_rate) / 100

    feasible = project.start_capital >= project.property_value * (100 - offer.borrowed_share + project.stamp_duty_rate) / 100

    return data, feasible


@njit(fastmath=True)
def calculate_repayments(  # pylint: disable = too-many-arguments, too-many-locals
    monthly_rate: np.ndarray,
    start_offset: float,
    principal: float,
    monthly_fee: float,
    monthly_income: float,
    monthly_costs: float,
    expenses: np.ndarray,
    with_offset_account: bool,
) -> np.ndarray:
    """Calculate the repayments data with numba"""
    n_periods = monthly_rate.shape[0]
    principal_paid_ = np.zeros(n_periods)
    offset_ = np.zeros(n_periods)
    principal_payment_ = np.zeros(n_periods)
    interest_ = np.zeros(n_periods)
    fee_ = np.zeros(n_periods)
    repayment_ = np.zeros(n_periods)
    principal_paid_no_offset_ = np.zeros(n_periods)

    for i in range(n_periods):
        if i == 0:
            offset = start_offset
            principal_paid = 0
            principal_paid_no_offset = 0
        else:
            offset = offset_[i - 1]
            principal_paid = principal_paid_[i - 1]
            principal_paid_no_offset = principal_paid_no_offset_[i - 1]

        # Compute the amortisatino payment (i.e. the constant cashflow that will repay the loan + interests
        # over the remainnig duration)
        amortisation_payment = (
            (principal - principal_paid_no_offset)
            * monthly_rate[i]
            * (1 + monthly_rate[i]) ** (n_periods - i)
            / ((1 + monthly_rate[i]) ** (n_periods - i) - 1)
        )
        # If the loan is paid don't pay anything else
        loan_payment = min(amortisation_payment, principal - principal_paid)

        # The interest depends on the amount still to pay on the loan
        interest = max(0, principal - offset - principal_paid) * monthly_rate[i]
        interest_no_offset = max(0, principal - principal_paid_no_offset) * monthly_rate[i]

        # Don't pay fees once the loan is fully repaid
        fee = monthly_fee if loan_payment > 0 else 0

        principal_paid_[i] = principal_paid + loan_payment - interest
        principal_paid_no_offset_[i] = principal_paid_no_offset + loan_payment - interest_no_offset
        if with_offset_account:
            offset_[i] = offset + monthly_income - loan_payment - monthly_costs - fee - expenses[i]
        principal_payment_[i] = loan_payment - interest
        interest_[i] = interest
        fee_[i] = fee
        repayment_[i] = loan_payment + fee

    return principal_paid_, offset_, principal_payment_, interest_, fee_, repayment_


@lru_cache
def read_historical_rates() -> pd.DataFrame:
    """Read the historical rates"""
    try:
        return pd.read_html("https://www.rba.gov.au/statistics/cash-rate#datatable")[0]
    except Exception:
        return pd.read_csv("loan_calculator/assets/historical_rates.csv")

def get_monthly_rate_series(
    *,
    date_period: pd.DatetimeIndex,
    rate: float,
    rates_change: RatesForecast,
    with_fixed_rate: bool = False,
    fixed_rate: float = None,
    fixed_rate_duration: int = None,
    settlement_date: str | date | pd.Timestamp,
):
    """Create the monthly rate time series"""
    # Define the monthly loan rate and fee
    if settlement_date < date.today():
        histo = read_historical_rates()
        past_changes = (
            histo.rename(columns={"Effective Date": "date", "Change%\xa0points": "value"})
            .assign(
                date=lambda df: pd.to_datetime(df["date"], format="%d %b %Y", errors="coerce")
                + pd.offsets.MonthEnd()
                + pd.Timedelta(days=1),
                value=lambda df: pd.to_numeric(df["value"], errors="coerce"),
            )
            [["date", "value"]]
            .dropna(subset=["value"])
            .query("value != 0")
            .groupby("date")[["value"]].sum()
            .assign(value=lambda df: df["value"].cumsum() - df["value"].cumsum().loc[settlement_date:].iat[0])
            .reset_index()
            .to_dict("records")
        )
        rates_change = RatesForecast(changes=past_changes + rates_change.changes)

    rate_pct = pd.Series(rate, index=date_period)
    if rates_change.changes:
        rate_change = (
            pd.DataFrame(rates_change.model_dump()["changes"])
            .dropna()
            .assign(date=lambda df: pd.to_datetime(df["date"])).set_index("date")["value"]
        )
        rate_pct += (
            rate_change.reindex(set(date_period).union(rate_change.index)).resample("MS").asfreq().ffill().fillna(0)
        )
    if with_fixed_rate:
        fixed_rate_end = pd.Timestamp(
            f"{pd.Timestamp(settlement_date).year + fixed_rate_duration}-"
            f"{pd.Timestamp(settlement_date).strftime('%m-%d')}"
        ) - pd.Timedelta("1D")
        rate_pct.loc[:fixed_rate_end] = fixed_rate

    monthly_rate = rate_pct / 12 / 100

    return monthly_rate


def get_expenses_series(*, date_period: pd.DatetimeIndex, expenses: FutureExpenses):
    """Create the time series of extra expenses"""
    if expenses.expenses:
        return (
            pd.DataFrame(expenses.model_dump()["expenses"])
            .dropna()
            .assign(date=lambda df: pd.to_datetime(df["date"]) + pd.offsets.MonthBegin())
            .set_index("date")["value"]
            .reindex(date_period)
            .fillna(0)
        )
    return pd.Series(0, index=date_period)
