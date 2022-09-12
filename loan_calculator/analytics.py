from typing import Optional, Union

import numpy as np
import pandas as pd


def get_loan_data(loan: dict) -> Optional[pd.DataFrame]:
    """Ensure all the required data is present then compute the loan timeseries"""
    start_date = loan.get("settlement_date")
    property_value = loan.get("property_value")
    annual_rate = loan.get("annual_rate")
    borrowed_share = loan.get("borrowed_share")
    loan_duration_years = loan.get("loan_duration_years")
    start_capital = loan.get("start_capital")
    stamp_duty_rate = loan.get("stamp_duty_rate")
    monthly_income = loan.get("monthly_income")
    monthly_costs = loan.get("monthly_costs")
    with_offset_account = loan.get("with_offset_account")
    yearly_fees = loan.get("yearly_fees")

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
            with_offset_account is not None,
            yearly_fees is not None,
            start_date is not None,
        ]
    ):
        return None

    return compute_loan_timeseries(**loan)


def compute_loan_timeseries(  # pylint: disable = too-many-arguments, too-many-locals, unused-argument
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
    **kwargs,
):
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
    monthly_rate = annual_rate / 100 / 12
    monthly_fee = yearly_fees / 12

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

    amortisation_payment = compute_amortisation_payment(principal, monthly_rate, loan_duration_years * 12)

    # Compute the value month after month
    for i in range(len(date_period)):
        if i == 0:
            offset = start_offset
            principal_paid = 0
        else:
            offset = data["offset"].iat[i - 1]
            principal_paid = data["principal_paid"].iat[i - 1]

        # If the loan is paid don't pay anything else
        loan_payment = min(amortisation_payment, principal - principal_paid)

        # The interest depends on the amount still to pay on the loan
        interest = max(0, principal - offset - principal_paid) * monthly_rate

        # Don't pay fees once the loan is fully repaid
        fee = monthly_fee if loan_payment > 0 else 0

        data.iloc[i] = [
            principal_paid + loan_payment - interest,
            offset + monthly_income - loan_payment - monthly_costs - fee if with_offset_account else 0,
            loan_payment - interest,
            interest,
            fee,
            loan_payment + fee,
            property_value * (100 - borrowed_share) / 100 if i == 0 else 0,
            property_value * (stamp_duty_rate) / 100 if i == 0 else 0,
        ]

    return data


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
