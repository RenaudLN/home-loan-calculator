import dash_mantine_components as dmc
from dash import ALL, Input, Output, State, callback, clientside_callback, dcc, html

from loan_calculator.aio_appshell import AppshellAIO
from loan_calculator.components import number_input, timeline_input_item


def project_param(name: str):
    """Project parameters"""
    return {"type": "project-param", "id": name}


class ids:  # pylint: disable = invalid-name
    """Home IDs"""

    # Project
    property_value = project_param("property_value")
    start_capital = project_param("start_capital")
    monthly_income = project_param("monthly_income")
    monthly_costs = project_param("monthly_costs")
    start_date = project_param("settlement_date")
    stamp_duty_rate = project_param("stamp_duty_rate")
    add_rates_change = "add_rates_change"
    rates_timeline = "rates_timeline"
    rates_changes = "rates_changes"
    rates_change_date_item = lambda i: {"type": "rate-change-date-item", "order": i}
    rates_change_value_item = lambda i: {"type": "rate-change-value-item", "order": i}
    rates_change_delete_item = lambda i: {"type": "rate-change-delete-item", "order": i}
    expenses_timeline = "expenses_timeline"
    add_expense = "add_expense"
    expenses = "expenses"
    expense_date_item = lambda i: {"type": "expense-date-item", "order": i}
    expense_value_item = lambda i: {"type": "expense-value-item", "order": i}
    expense_delete_item = lambda i: {"type": "expense-delete-item", "order": i}
    trigger = "dummy_trigger_btn"


appshell = AppshellAIO(
    "Loan Calculator",
    primary_color="teal",
    sidebar_top_slot=[
        dmc.Text("My Project", weight="bold", style={"lineHeight": "40px"}, size="sm"),
        html.Div(
            [
                number_input(
                    id=ids.property_value,
                    label="Property Value ($)",
                    min=0,
                    persistence=True,
                    debounce=True,
                ),
                dmc.Space(h="sm"),
                number_input(
                    id=ids.start_capital,
                    label="Initial Capital ($)",
                    description="Amount of available capital for this purchase",
                    min=0,
                    persistence=True,
                    debounce=True,
                ),
                dmc.Space(h="sm"),
                number_input(
                    id=ids.monthly_income,
                    label="Monthly Income ($)",
                    description="After-tax income",
                    min=0,
                    persistence=True,
                    debounce=True,
                ),
                dmc.Space(h="sm"),
                number_input(
                    id=ids.monthly_costs,
                    label="Monthly Costs ($)",
                    description="Excludes loan repayment",
                    min=0,
                    persistence=True,
                    debounce=True,
                ),
                dmc.Space(h="sm"),
                dmc.DatePicker(
                    id=ids.start_date,
                    label="Settlement Date",
                    allowFreeInput=True,
                    persistence=True,
                ),
                dmc.Space(h="sm"),
                number_input(
                    id=ids.stamp_duty_rate,
                    label="Stamp Duty Rate (%)",
                    min=0,
                    persistence=True,
                    debounce=True,
                ),
                dmc.Space(h="sm"),
                dmc.Accordion(
                    [
                        dmc.AccordionItem(
                            label="Interest rates projection",
                            children=[
                                dmc.Text(
                                    "Note: The rate changes should be relative to the current value.",
                                    size="sm",
                                    color="gray",
                                ),
                                dmc.Space(h="sm"),
                                dmc.Timeline(id=ids.rates_timeline),
                                dmc.Space(h="sm"),
                                dmc.Button(
                                    "Add rate change",
                                    compact=True,
                                    id=ids.add_rates_change,
                                    style={"marginLeft": "2.25rem"},
                                ),
                            ],
                        ),
                        dmc.AccordionItem(
                            label="Future expenses",
                            children=[
                                dmc.Text(
                                    "Additional expenses not considered in the monthly costs, "
                                    "e.g. a car or a wedding. Impacts the offset account balance.",
                                    size="sm",
                                    color="gray",
                                ),
                                dmc.Space(h="sm"),
                                dmc.Timeline(id=ids.expenses_timeline),
                                dmc.Space(h="md"),
                                dmc.Button(
                                    "Add expense",
                                    compact=True,
                                    id=ids.add_expense,
                                    style={"marginLeft": "2.25rem"},
                                ),
                            ],
                        ),
                    ],
                ),
            ]
        ),
    ],
    additional_themed_content=[
        dcc.Store(id=ids.rates_changes, storage_type="local"),
        dcc.Store(id=ids.expenses, storage_type="local"),
        html.Button(style={"display": "none"}, id=ids.trigger),
    ],
)


@callback(
    Output(ids.rates_timeline, "children"),
    Input(ids.rates_changes, "data"),
    Input(ids.trigger, "n_clicks"),
)
def update_rates_timeline(rates_changes, trigger):  # pylint: disable = unused-argument
    """Update the rates change timeline"""
    if not rates_changes:
        items = [
            timeline_input_item(
                date_id=ids.rates_change_date_item(i),
                value_id=ids.rates_change_value_item(i),
                delete_id=ids.rates_change_delete_item(i),
                value_placeholder="Change (% p.a.)",
                with_trend_bullet=True,
            )
            for i in range(2)
        ]
    else:
        items = [
            timeline_input_item(
                date_id=ids.rates_change_date_item(i),
                value_id=ids.rates_change_value_item(i),
                delete_id=ids.rates_change_delete_item(i),
                value_placeholder="Change (% p.a.)",
                with_trend_bullet=True,
                **change,
            )
            for i, change in enumerate(rates_changes)
        ] + [
            timeline_input_item(
                date_id=ids.rates_change_date_item(1),
                value_id=ids.rates_change_value_item(1),
                delete_id=ids.rates_change_delete_item(1),
                value_placeholder="Change (% p.a.)",
                with_trend_bullet=True,
            )
        ] * (
            len(rates_changes) == 1
        )

    return items


@callback(
    Output(ids.expenses_timeline, "children"),
    Input(ids.expenses, "data"),
    Input(ids.trigger, "n_clicks"),
)
def update_expenses_timeline(expenses, trigger):  # pylint: disable = unused-argument
    """Update the rates change timeline"""
    if not expenses:
        items = [
            timeline_input_item(
                date_id=ids.expense_date_item(i),
                value_id=ids.expense_value_item(i),
                delete_id=ids.expense_delete_item(i),
                value_placeholder="Cost ($)",
            )
            for i in range(2)
        ]
    else:
        items = [
            timeline_input_item(
                date_id=ids.expense_date_item(i),
                value_id=ids.expense_value_item(i),
                delete_id=ids.expense_delete_item(i),
                value_placeholder="Cost ($)",
                **change,
            )
            for i, change in enumerate(expenses)
        ] + [
            timeline_input_item(
                date_id=ids.expense_date_item(1),
                value_id=ids.expense_value_item(1),
                delete_id=ids.expense_delete_item(1),
                value_placeholder="Cost ($)",
            )
        ] * (
            len(expenses) == 1
        )

    return items


save_timeline_values = """function(dates, values, deletes, add, current) {
    const ctx = window.dash_clientside.callback_context
    const no_update = window.dash_clientside.no_update
    if (ctx.triggered.length !== 1) {
        return no_update
    }
    if (ctx.triggered[0].prop_id.includes("add") && ctx.triggered[0].value != null) {
        return [...(current || [{date: null, value: null}]), {date: null, value: null}]
    }
    if (ctx.triggered[0].prop_id.includes("delete") && ctx.triggered[0].value != null) {
        const { order } = JSON.parse(ctx.triggered[0].prop_id.split(".")[0])
        return current.filter((x, i) => i !== order)
    }

    const latest = dates.map((d, i) => ({date: d, value: values[i]}))
    if (JSON.stringify(current) === JSON.stringify(latest)) {
        return no_update
    }

    return latest
}"""


clientside_callback(
    save_timeline_values,
    Output(ids.rates_changes, "data"),
    Input(ids.rates_change_date_item(ALL), "value"),
    Input(ids.rates_change_value_item(ALL), "value"),
    Input(ids.rates_change_delete_item(ALL), "n_clicks"),
    Input(ids.add_rates_change, "n_clicks"),
    State(ids.rates_changes, "data"),
)


clientside_callback(
    save_timeline_values,
    Output(ids.expenses, "data"),
    Input(ids.expense_date_item(ALL), "value"),
    Input(ids.expense_value_item(ALL), "value"),
    Input(ids.expense_delete_item(ALL), "n_clicks"),
    Input(ids.add_expense, "n_clicks"),
    State(ids.expenses, "data"),
)
