import dash_mantine_components as dmc
from dash import MATCH, Input, Output, clientside_callback, html
from dash_iconify import DashIconify


def loan_param(param: str, name: str):
    """Parameters represented with a "value" attribute"""
    return {"type": "loan-param", "id": param, "name": name}


def loan_boolean(param: str, name: str):
    """Parameters represented with a "checked" attribute"""
    return {"type": "loan-boolean", "id": param, "name": name}


class ids:  # pylint: disable = invalid-name
    """Offer modal IDs"""

    modal = "loan_modal"
    name = lambda name: loan_param("name", name)
    annual_rate = lambda name: loan_param("annual_rate", name)
    borrowed_share = lambda name: loan_param("borrowed_share", name)
    loan_duration_years = lambda name: loan_param("loan_duration_years", name)
    with_offset_account = lambda name: loan_boolean("with_offset_account", name)
    with_fixed_rate = lambda name: loan_boolean("with_fixed_rate", name)
    start_date = lambda name: loan_param("start_date", name)
    yearly_fees = lambda name: loan_param("yearly_fees", name)
    fixed_rate = lambda name: loan_param("fixed_rate", name)
    fixed_rate_duration = lambda name: loan_param("fixed_rate_duration", name)
    save = lambda name: {"type": "save-offer", "name": name}


def layout(name: str = "__new__", **kwargs):
    """Offer modal layout"""
    return dmc.Modal(
        id=ids.modal,
        centered=True,
        size="xl",
        withCloseButton=True,
        title="New Offer",
        children=modal_content(name, **kwargs),
    )


def modal_content(name: str, **kwargs):
    """Content of the modal, used to change the content when clicking on the edit button"""
    return html.Div(
        [
            dmc.TextInput(
                id=ids.name(name),
                label="Name",
                style={"display": "none" if name != "__new__" else "unset"},
                value=name if name != "__new__" else "",
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
                value=kwargs.get("yearly_fees", 0),
                min=0,
                precision=2,
                label="Yearly Fees ($ p.a.)",
            ),
            html.Div(
                dmc.Switch(
                    id=ids.with_fixed_rate(name),
                    checked=kwargs.get("with_fixed_rate", False),
                    label="With Fixed Rate",
                    style={"marginTop": "0.5rem"},
                ),
                style={"gridColumn": "1 / -1"},
            ),
            dmc.NumberInput(
                id=ids.fixed_rate(name),
                value=kwargs.get("fixed_rate"),
                min=0,
                precision=3,
                label="Fixed Rate (% p.a.)",
                style={"display": "none" if not kwargs.get("with_fixed_rate") else "block"},
            ),
            dmc.NumberInput(
                id=ids.fixed_rate_duration(name),
                value=kwargs.get("fixed_rate_duration"),
                min=0,
                precision=0,
                label="Fixed Rate Duration (years)",
                style={"display": "none" if not kwargs.get("with_fixed_rate") else "block"},
            ),
            html.Div(
                dmc.Switch(
                    id=ids.with_offset_account(name),
                    checked=kwargs.get("with_offset_account", False),
                    label="With Offset Account",
                    style={"marginTop": "0.5rem"},
                ),
                style={"gridColumn": "1 / -1"},
            ),
            html.Div(
                dmc.Button("Save", leftIcon=[DashIconify(icon="carbon:save", height=16)], id=ids.save(name)),
                style={"display": "flex", "justifyContent": "end", "gridColumn": "1 / -1"},
            ),
        ],
        style={"gap": "0.5rem", "display": "grid", "gridTemplateColumns": "1fr 1fr"},
    )


clientside_callback(
    """function(withFixedRate) {
        if (withFixedRate) {
            return [
                {display: "block"},
                {display: "block"},
            ]
        }
        return [
            {display: "none"},
            {display: "none"},
        ]
    }""",
    Output(ids.fixed_rate(MATCH), "style"),
    Output(ids.fixed_rate_duration(MATCH), "style"),
    Input(ids.with_fixed_rate(MATCH), "checked"),
)
