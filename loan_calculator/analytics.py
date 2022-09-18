from typing import List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from numba import njit


def get_loan_data(  # pylint: disable = too-many-locals
    loan: dict, rates_change: List[dict], expenses: List[dict]
) -> Tuple[Optional[pd.DataFrame], Optional[bool]]:
    """Ensure all the required data is present then compute the loan timeseries"""
    settlement_date = loan.get("settlement_date")
    property_value = loan.get("property_value")
    annual_rate = loan.get("annual_rate")
    borrowed_share = loan.get("borrowed_share")
    loan_duration_years = loan.get("loan_duration_years")
    start_capital = loan.get("start_capital")
    stamp_duty_rate = loan.get("stamp_duty_rate")
    monthly_income = loan.get("monthly_income")
    monthly_costs = loan.get("monthly_costs")
    yearly_fees = loan.get("yearly_fees")
    with_fixed_rate = loan.get("with_fixed_rate")
    fixed_rate = loan.get("fixed_rate")
    fixed_rate_duration = loan.get("fixed_rate_duration")

    if not all(
        [
            property_value is not None,
            annual_rate is not None,
            borrowed_share is not None,
            loan_duration_years is not None,
            start_capital is not None,
            stamp_duty_rate is not None,
            monthly_income is not None,
            monthly_costs is not None,
            yearly_fees is not None,
            settlement_date is not None,
        ]
    ):
        return None, None

    if with_fixed_rate and not all([fixed_rate, fixed_rate_duration]):
        return None, None

    return compute_loan_timeseries(**loan, rates_change=rates_change, expenses=expenses)


def compute_loan_timeseries(  # pylint: disable = too-many-arguments, too-many-locals, unused-argument
    *,
    property_value: float,
    annual_rate: float,
    borrowed_share: float,
    loan_duration_years: float,
    start_capital: float,
    stamp_duty_rate: float,
    monthly_income: float,
    monthly_costs: float,
    with_offset_account: float,
    yearly_fees: float,
    settlement_date: Union[str, pd.Timestamp],
    rates_change: List[dict],
    expenses: List[dict],
    with_fixed_rate: bool = False,
    fixed_rate: float = None,
    fixed_rate_duration: int = None,
    **kwargs,
) -> Tuple[pd.DataFrame, bool]:
    """Compute the loan timeseries

    :param property_value: Property value in $
    :param annual_rate: Annual loan rate in %
    :param borrowed_share: Borrowed share in %
    :param loan_duration_years: Load duration in years
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
        settlement_date,
        f"{pd.Timestamp(settlement_date).year + loan_duration_years}-{pd.Timestamp(settlement_date).strftime('%m-%d')}",
        freq="MS",
        inclusive="left",
    )

    # Define the loan princpal
    principal = property_value * borrowed_share / 100

    # Define how much savings can be left in the offset account after deposit + stamp duty
    start_offset = (
        start_capital - property_value * (100 - borrowed_share + stamp_duty_rate) / 100
    ) * with_offset_account

    # Define the monthly loan rate and fee
    monthly_rate = get_monthly_rate_series(
        date_period=date_period,
        annual_rate=annual_rate,
        rates_change=rates_change,
        with_fixed_rate=with_fixed_rate,
        fixed_rate=fixed_rate,
        fixed_rate_duration=fixed_rate_duration,
        settlement_date=settlement_date,
    )
    monthly_fee = yearly_fees / 12

    expenses_series = get_expenses_series(date_period=date_period, expenses=expenses)

    repayments = np.c_[
        calculate_repayments(
            monthly_rate.to_numpy(),
            start_offset,
            principal,
            monthly_fee,
            monthly_income,
            monthly_costs,
            expenses_series.to_numpy(),
            with_offset_account,
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
    data.at[data.index[0], "deposit"] = property_value * (100 - borrowed_share) / 100
    data.at[data.index[0], "stamp_duty"] = property_value * (stamp_duty_rate) / 100

    feasible = start_capital >= property_value * (100 - borrowed_share + stamp_duty_rate) / 100

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

    for i in range(n_periods):
        if i == 0:
            offset = start_offset
            principal_paid = 0
        else:
            offset = offset_[i - 1]
            principal_paid = principal_paid_[i - 1]

        # Compute the amortisatino payment (i.e. the constant cashflow that will repay the loan + interests
        # over the remainnig duration)
        amortisation_payment = (
            (principal - principal_paid)
            * monthly_rate[i]
            * (1 + monthly_rate[i]) ** (n_periods - i)
            / ((1 + monthly_rate[i]) ** (n_periods - i) - 1)
        )
        # If the loan is paid don't pay anything else
        loan_payment = min(amortisation_payment, principal - principal_paid)

        # The interest depends on the amount still to pay on the loan
        interest = max(0, principal - offset - principal_paid) * monthly_rate[i]

        # Don't pay fees once the loan is fully repaid
        fee = monthly_fee if loan_payment > 0 else 0

        principal_paid_[i] = principal_paid + loan_payment - interest
        if with_offset_account:
            offset_[i] = offset + monthly_income - loan_payment - monthly_costs - fee - expenses[i]
        principal_payment_[i] = loan_payment - interest
        interest_[i] = interest
        fee_[i] = fee
        repayment_[i] = loan_payment + fee

    return principal_paid_, offset_, principal_payment_, interest_, fee_, repayment_


def get_monthly_rate_series(
    *,
    date_period: pd.DatetimeIndex,
    annual_rate: float,
    rates_change: List[dict],
    with_fixed_rate: bool = False,
    fixed_rate: float = None,
    fixed_rate_duration: int = None,
    settlement_date: Union[str, pd.Timestamp],
):
    """Create the monthly rate time series"""
    # Define the monthly loan rate and fee
    annual_rate_pct = pd.Series(annual_rate, index=date_period)
    if rates_change:
        rate_change = (
            pd.DataFrame(rates_change).assign(date=lambda df: pd.to_datetime(df["date"])).set_index("date")["value"]
        )
        annual_rate_pct += (
            rate_change.reindex(set(date_period).union(rate_change.index)).resample("MS").asfreq().ffill()
        )
    if with_fixed_rate:
        fixed_rate_end = pd.Timestamp(
            f"{pd.Timestamp(settlement_date).year + fixed_rate_duration}-"
            f"{pd.Timestamp(settlement_date).strftime('%m-%d')}"
        ) - pd.Timedelta("1D")
        annual_rate_pct.loc[:fixed_rate_end] = fixed_rate

    monthly_rate = annual_rate_pct / 12 / 100

    return monthly_rate


def get_expenses_series(*, date_period: pd.DatetimeIndex, expenses: List[dict]):
    """Create the time series of extra expenses"""
    if expenses:
        return (
            pd.DataFrame(expenses)
            .assign(date=lambda df: pd.to_datetime(df["date"]))
            .set_index("date")["value"]
            .reindex(date_period)
            .fillna(0)
        )
    return pd.Series(0, index=date_period)
