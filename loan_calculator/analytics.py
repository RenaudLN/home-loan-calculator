from typing import List, Optional, Tuple, Union

import numpy as np
import pandas as pd


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

    expenses = get_expenses_series(date_period=date_period, expenses=expenses)

    # Initialise the timeseries dataframe
    data = pd.DataFrame(
        index=date_period,
        columns=[
            "principal_paid",
            "offset",
            "principal_payment",
            "interest",
            "fee",
            "repayment",
            "deposit",
            "stamp_duty",
        ],
    ).rename_axis(index="date")

    # Compute the value month after month
    for i, date in enumerate(date_period):
        if i == 0:
            offset = start_offset
            principal_paid = 0
        else:
            offset = data["offset"].iat[i - 1]
            principal_paid = data["principal_paid"].iat[i - 1]

        # Compute the amortisatino payment (i.e. the constant cashflow that will repay the loan + interests
        # over the remainnig duration)
        amortisation_payment = compute_amortisation_payment(
            principal - principal_paid,
            monthly_rate.at[date],
            loan_duration_years * 12 - i,
        )
        # If the loan is paid don't pay anything else
        loan_payment = min(amortisation_payment, principal - principal_paid)

        # The interest depends on the amount still to pay on the loan
        interest = max(0, principal - offset - principal_paid) * monthly_rate.at[date]

        # Don't pay fees once the loan is fully repaid
        fee = monthly_fee if loan_payment > 0 else 0

        data.iloc[i] = [
            principal_paid + loan_payment - interest,
            offset + monthly_income - loan_payment - monthly_costs - fee - expenses.at[date]
            if with_offset_account
            else 0,
            loan_payment - interest,
            interest,
            fee,
            loan_payment + fee,
            property_value * (100 - borrowed_share) / 100 if i == 0 else 0,
            property_value * (stamp_duty_rate) / 100 if i == 0 else 0,
        ]

    feasible = start_capital >= property_value * (100 - borrowed_share + stamp_duty_rate) / 100

    return data, feasible


def compute_amortisation_payment(
    principal: float, rate: Union[float, np.ndarray], n_periods: int
) -> Union[float, np.ndarray]:
    """Compute the amortisation payment

    :param principal: Loan principal
    :param rate: Loan rate (for the given period, e.g. monthly for a period of a month)
    :param n_periods: Number of periods to amortise the loan
    :return: Amortisation payment
    """
    return principal * rate * (1 + rate) ** n_periods / ((1 + rate) ** n_periods - 1)


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
