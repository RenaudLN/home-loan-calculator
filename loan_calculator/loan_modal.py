from dash import html
import dash_mantine_components as dmc
from dash_iconify import DashIconify


def loan_param(param: str, name: str):
    return {"type": "loan-param", "id": param, "name": name}

def loan_boolean(param: str, name: str):
    return {"type": "loan-boolean", "id": param, "name": name}


class ids:
    modal = "loan_modal"
    name = lambda name: loan_param("name", name)
    property_value = lambda name: loan_param("property_value", name)
    annual_rate = lambda name: loan_param("annual_rate", name)
    borrowed_share = lambda name: loan_param("borrowed_share", name)
    loan_duration_years = lambda name: loan_param("loan_duration_years", name)
    start_capital = lambda name: loan_param("start_capital", name)
    stamp_duty_rate = lambda name: loan_param("stamp_duty_rate", name)
    monthly_income = lambda name: loan_param("monthly_income", name)
    monthly_costs = lambda name: loan_param("monthly_costs", name)
    with_offset_account = lambda name: loan_boolean("with_offset_account", name)
    start_date = lambda name: loan_param("start_date", name)
    yearly_fees = lambda name: loan_param("yearly_fees", name)
    save = lambda name: {"type": "save-loan", "name": name}


def layout(name: str = "__new__", **kwargs):
    kwargs.update(dict(
        annual_rate=3.64,
        borrowed_share=70,
        property_value=780000,
        loan_duration_years=30,
        start_capital=300000,
        stamp_duty_rate=5.5,
        monthly_income=13500,
        monthly_costs=6000,
        with_offset_account=True,
        start_date="2022-11-01",
        yearly_fees=395,
    ))
    return dmc.Modal(
        id=ids.modal,
        centered=True,
        size="xl",
        withCloseButton=True,
        title="New Loan",
        children=html.Div(
            [
                dmc.TextInput(
                    id=ids.name(name),
                    label="Name",
                    style={"display": "none" if name != "__new__" else "unset"},
                    value=name if name != "__new__" else "",
                ),
                dmc.NumberInput(
                    id=ids.property_value(name),
                    min=0,
                    step=10_000,
                    precision=2,
                    label="Property Value ($)",
                    value=kwargs.get("property_value"),
                ),
                dmc.NumberInput(
                    id=ids.annual_rate(name),
                    min=0,
                    step=1,
                    precision=3,
                    label="Annual Interest Rate (% p.a.)",
                    value=kwargs.get("annual_rate"),
                ),
                dmc.NumberInput(
                    id=ids.borrowed_share(name),
                    min=0,
                    step=1,
                    max=100,
                    precision=1,
                    label="Borrowed Share (%)",
                    value=kwargs.get("borrowed_share"),
                ),
                dmc.NumberInput(
                    id=ids.loan_duration_years(name),
                    value=kwargs.get("loan_duration_years"),
                    min=0,
                    step=1,
                    label="Loan Duration (years)",
                ),
                dmc.NumberInput(
                    id=ids.yearly_fees(name),
                    value=kwargs.get("yearly_fees"),
                    min=0,
                    precision=2,
                    label="Yearly Fees ($ p.a.)",
                ),
                dmc.NumberInput(
                    id=ids.start_capital(name),
                    value=kwargs.get("start_capital"),
                    min=0,
                    step=10_000,
                    precision=2,
                    label="Starting Capital ($)",
                    description="How much savings you currently have",
                ),
                dmc.NumberInput(
                    id=ids.stamp_duty_rate(name),
                    value=kwargs.get("stamp_duty_rate"),
                    min=0,
                    step=1,
                    precision=2,
                    label="Stamp Duty Rate (%)",
                ),
                dmc.Switch(
                    id=ids.with_offset_account(name),
                    checked=kwargs.get("with_offset_account"),
                    label="With Offset Account",
                ),
                dmc.NumberInput(
                    id=ids.monthly_income(name),
                    value=kwargs.get("monthly_income"),
                    min=0,
                    step=1,
                    precision=2,
                    label="Monthly Income ($)",
                ),
                dmc.NumberInput(
                    id=ids.monthly_costs(name),
                    value=kwargs.get("monthly_costs"),
                    min=0,
                    step=1,
                    precision=2,
                    label="Monthly Costs ($)",
                    description="This is excluding loan repayment",
                ),
                dmc.DatePicker(
                    id=ids.start_date(name),
                    value=kwargs.get("start_date"),
                    label="Loan Start Date",
                ),
                html.Div(
                    dmc.Button("Save", leftIcon=[DashIconify(icon="carbon:save", height=16)], id=ids.save(name)),
                    style={"display": "flex", "justifyContent": "end"}
                )
            ],
            style={"display": "flex", "flexDirection": "column", "gap": "1rem"},
        )
    )
