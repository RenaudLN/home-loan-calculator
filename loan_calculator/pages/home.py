from typing import Any, Dict, List

import dash_mantine_components as dmc
import pandas as pd
from dash import ALL, Input, Output, State, callback, clientside_callback, ctx, dcc, html, no_update, register_page
from dash_iconify import DashIconify

from loan_calculator import analytics, delete_modal, loan_modal, plots
from loan_calculator.components import number_input, table, timeline_input_item

register_page(__name__, "/", title="Loan Calculator")


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
    # Loans
    new_loan_button = "new_loan_button"
    search = "search_loans"
    offers_wrapper = "offers_wrapper"
    edit_offer = lambda name: {"type": "edit-offer", "name": name}
    delete_offer = lambda name: {"type": "delete-offer", "name": name}
    # Comparison
    comparison_wrapper = "offer_comparison_wrapper"
    loans = "loans_store"
    trigger = "dummy_trigger_btn"
    select = "loan_selection"


def layout():
    """Layout function"""
    return html.Div(
        [
            project_sidebar(),
            dmc.ScrollArea(
                dmc.Tabs(
                    children=[
                        dmc.Tab(
                            label="My Offers",
                            children=offers_grid(),
                        ),
                        dmc.Tab(
                            label="Offer Comparison",
                            children=offers_comparison(),
                        ),
                    ],
                    style={"maxWidth": "1100px", "margin": "0 auto"},
                ),
                style={"flex": "1"},
            ),
            dcc.Store(id=ids.loans, storage_type="local"),
            dcc.Store(id=ids.rates_changes, storage_type="local"),
            html.Button(style={"display": "none"}, id=ids.trigger),
            loan_modal.layout(),
            delete_modal.layout(),
        ],
        style={"display": "flex", "gap": "0.25rem", "height": "calc(100vh - 80px)", "overflow": "hidden"},
    )


def project_sidebar():
    """Sidebar with project-level data"""
    return dmc.ScrollArea(
        [
            dmc.Text("My Project", weight="bold", style={"lineHeight": "40px"}, size="sm"),
            html.Div(
                [
                    number_input(
                        id=ids.property_value,
                        label="Property Value ($)",
                        min=0,
                        persistence=True,
                    ),
                    dmc.Space(h="sm"),
                    number_input(
                        id=ids.start_capital,
                        label="Starting Capital ($)",
                        min=0,
                        persistence=True,
                    ),
                    dmc.Space(h="sm"),
                    number_input(
                        id=ids.monthly_income,
                        label="Monthly Income ($)",
                        description="After-tax income",
                        min=0,
                        persistence=True,
                    ),
                    dmc.Space(h="sm"),
                    number_input(
                        id=ids.monthly_costs,
                        label="Monthly Costs ($)",
                        description="Excludes loan repayment",
                        min=0,
                        persistence=True,
                    ),
                    dmc.Space(h="sm"),
                    dmc.DatePicker(
                        id=ids.start_date,
                        label="Settlement Date",
                        allowFreeInput=True,
                        value="2023-01-01",
                        persistence=True,
                    ),
                    dmc.Space(h="sm"),
                    number_input(
                        id=ids.stamp_duty_rate,
                        label="Stamp Duty Rate (%)",
                        min=0,
                        persistence=True,
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
                                    ),
                                ],
                            )
                        ]
                    ),
                ]
            ),
        ],
        style={"marginLeft": "-1rem", "padding": "0 1rem", "flex": "0 0 300px"},
        offsetScrollbars=False,
    )


def offers_grid():
    """Content of first tab with a grid of cards of offers"""
    return [
        html.Div(
            [
                dmc.TextInput(
                    id=ids.search,
                    style={"flex": "1"},
                    icon=[DashIconify(icon="carbon:search")],
                ),
                dmc.Button("Add Offer", leftIcon=[DashIconify(icon="carbon:add", height=16)], id=ids.new_loan_button),
            ],
            style={"display": "flex", "alignItems": "center", "gap": "0.5rem"},
        ),
        dmc.Space(h="md"),
        html.Div(
            id=ids.offers_wrapper,
            children=dmc.Skeleton(
                height="min(400px, calc(90vh - 200px))",
                radius="md",
                style={"gridColumn": "1 / -1"},
            ),
        ),
    ]


def offers_grid_contents(loans_data: dict, search: str, property_value: float):
    """Offers cards to be displayed in the grid"""
    return [
        dmc.Paper(
            [
                html.Div(
                    [
                        dmc.Text(name or "undefined", weight="bold"),
                        dmc.Space(h=12),
                        dmc.Text(
                            f"Principal: ${(loan.get('borrowed_share') or 0) * (property_value or 0) / 100:,.0f}",
                            size="sm",
                            color="gray",
                        ),
                        dmc.Space(h=3),
                        dmc.Text(f"Annual rate: {loan.get('annual_rate', '')}% p.a.", size="sm", color="gray"),
                    ],
                    style={"flex": "1"},
                ),
                html.Div(
                    [
                        dmc.Button(
                            DashIconify(icon="carbon:edit"),
                            compact=True,
                            variant="subtle",
                            style={"padding": "0 4px"},
                            id=ids.edit_offer(name),
                        ),
                        dmc.Button(
                            DashIconify(icon="carbon:delete"),
                            compact=True,
                            variant="subtle",
                            color="red",
                            style={"padding": "0 4px"},
                            id=ids.delete_offer(name),
                        ),
                    ],
                    style={"display": "flex", "flexDirection": "column"},
                ),
            ],
            radius="md",
            p="md",
            style={"display": "flex"},
        )
        for name, loan in loans_data.items()
        if not search or search.lower() in name.lower()
    ]


def no_offers_grid_contents():
    """Message prompting the user to add offers"""
    return dmc.Paper(
        dmc.Text("Start by creating offers", color="gray"),
        style={
            "height": "min(400px, calc(90vh - 200px))",
            "display": "grid",
            "placeContent": "center",
            "gridColumn": "1 / -1",
        },
        radius="md",
    )


def offers_comparison():
    """Content of second tab with results graph"""
    return [
        dmc.MultiSelect(id=ids.select, maxSelectedValues=4, persistence=True),
        dmc.Space(h="md"),
        html.Div(
            dmc.Paper(
                dmc.Text(
                    "Create loan offers then select them above.",
                    color="gray",
                    size="xl",
                ),
                style={
                    "height": "min(400px, calc(90vh - 200px))",
                    "display": "grid",
                    "placeContent": "center",
                },
                radius="md",
            ),
            id=ids.comparison_wrapper,
        ),
    ]


clientside_callback(
    """function(n_clicks, deletes, loans) {
        const ctx = dash_clientside.callback_context
        if (ctx.triggered.length === 0 || !ctx.triggered[0].value) return dash_clientside.no_update
        const { type, name } = JSON.parse(ctx.triggered[0].prop_id.split(".")[0])
        if (type === "delete-button") {
            return Object.fromEntries(Object.entries(loans).filter(([n]) => n !== name))
        }
        const params = ctx.states_list[1].filter(s => s.id.name === name).map(s => [s.id.id, s.value])
        const booleans = ctx.states_list[2].filter(s => s.id.name === name).map(s => [s.id.id, s.value])
        const loan = Object.fromEntries(params.concat(booleans))
        if (!loans) return {[loan.name]: loan}
        return {...loans, [loan.name]: loan}
    }""",
    Output(ids.loans, "data"),
    Input(loan_modal.ids.save(ALL), "n_clicks"),
    Input(delete_modal.ids.delete_button(ALL), "n_clicks"),
    State(ids.loans, "data"),
    State(loan_modal.loan_param(ALL, ALL), "value"),
    State(loan_modal.loan_boolean(ALL, ALL), "checked"),
)


clientside_callback(
    """function(a, b, c, opened) {
        const ctx = window.dash_clientside.callback_context
        if (ctx.triggered.length === 0 || !ctx.triggered[0].value) return window.dash_clientside.no_update
        return !opened
    }""",
    Output(loan_modal.ids.modal, "opened"),
    Input(ids.new_loan_button, "n_clicks"),
    Input(ids.edit_offer(ALL), "n_clicks"),
    Input(loan_modal.ids.save(ALL), "n_clicks"),
    State(loan_modal.ids.modal, "opened"),
)


clientside_callback(
    """function(a, b, c, opened) {
        const ctx = window.dash_clientside.callback_context
        if (ctx.triggered.length === 0 || !ctx.triggered[0].value) return window.dash_clientside.no_update
        const { type } = JSON.parse(ctx.triggered[0].prop_id.split(".")[0])
        if (type === "delete-offer") return true
        return false
    }""",
    Output(delete_modal.ids.modal, "opened"),
    Input(ids.delete_offer(ALL), "n_clicks"),
    Input(delete_modal.ids.delete_button(ALL), "n_clicks"),
)


clientside_callback(
    """function(loansData, trigger, currentValue) {
        if (!loansData) return [[], []]
        const names = Object.keys(loansData).filter(k => !!k)
        return [names, currentValue ? currentValue.filter(n => names.includes(n)) : dash_clientside.no_update]
    }""",
    Output(ids.select, "data"),
    Output(ids.select, "value"),
    Input(ids.loans, "data"),
    Input(ids.trigger, "n_clicks"),
    State(ids.select, "value"),
)


@callback(
    Output(ids.offers_wrapper, "children"),
    Input(ids.loans, "data"),
    Input(ids.search, "value"),
    Input(ids.property_value, "value"),
)
def update_offers(loans_data, search, property_value):
    """Update the content of the offers grid"""
    if not loans_data:
        return no_offers_grid_contents()
    return offers_grid_contents(loans_data, search, property_value)


@callback(
    Output(ids.comparison_wrapper, "children"),
    Input(ids.select, "value"),
    Input(project_param(ALL), "value"),
    Input(ids.rates_changes, "data"),
    State(ids.loans, "data"),
)
def compute_loan(loans_names: List[str], project_params: dict, rates_change: List[Dict[str, Any]], loans_data: dict):
    """Compute the loan results"""
    if not loans_data or not loans_names:
        return dmc.Paper(
            dmc.Text(
                "Create loan offers then select them above.",
                color="gray",
                size="xl",
            ),
            style={
                "height": "min(400px, calc(90vh - 200px))",
                "display": "grid",
                "placeContent": "center",
            },
            radius="md",
        )

    project_params = {inp["id"]["id"]: value for inp, value in zip(ctx.inputs_list[1], project_params)}
    rates_change = [rc for rc in (rates_change or []) if rc.get("date") and rc.get("change") is not None]
    data_list = []
    title_list = []
    feasible_list = []
    for name in loans_names:
        loan = loans_data[name] | project_params
        data, feasible = analytics.get_loan_data(loan, rates_change)
        if data is not None:
            data_list.append(data)
            title_list.append(name)
            feasible_list.append(feasible)

    if not data_list:
        return no_update

    fig = plots.make_comparison_figure(data_list, title_list, feasible_list)

    table_data = (
        pd.DataFrame(
            [
                [
                    data[["principal_payment", "interest", "fee"]]
                    .sum(axis=1)
                    .to_frame("repayment")
                    .query("repayment > 0")
                    .mean()[0]
                    for data in data_list
                ],
                [data[["interest", "fee"]].sum(axis=1).cumsum()[10 * 12] for data in data_list],
                [
                    (data["principal_paid"].iat[10 * 12] + data["deposit"].iat[0])
                    / (data["principal_paid"].iat[-1] + data["deposit"].iat[0])
                    * 100
                    for data in data_list
                ],
                [data[["interest", "fee"]].sum(axis=1).cumsum()[-1] for data in data_list],
            ],
            columns=[title_list],
            index=[
                "Monthly Repayment",
                "Interest & Fees paid @ year 10",
                "Percent Owned @ year 10",
                "Interest & Fees paid @ loan end",
            ],
        )
        .T.apply(lambda s: s.apply(lambda x: f"{x:,.1f}%" if "Percent" in s.name else f"${x:,.0f}"))
        .T.rename_axis(" ")
        .reset_index()
    )
    return [
        dmc.Paper(table(table_data, striped=True), px="sm", pt="sm"),
        dmc.Space(h="md"),
        dcc.Graph(figure=fig, responsive=True, config={"displayModeBar": False}),
    ]


@callback(
    Output(loan_modal.ids.modal, "children"),
    Output(loan_modal.ids.modal, "title"),
    Input(ids.new_loan_button, "n_clicks"),
    Input(ids.edit_offer(ALL), "n_clicks"),
    State(ids.loans, "data"),
)
def update_offer_modal_content(new_trigger, edit_triggers, loans_data):  # pylint: disable = unused-argument
    """Update the content of the offer modal"""
    if not ctx.triggered_id:
        return [no_update] * 2

    if isinstance(ctx.triggered_id, dict):
        name = ctx.triggered_id["name"]
        loan_data = loans_data[name]
    else:
        name = "New Offer"
        loan_data = {"name": "__new__"}
    return [loan_modal.modal_content(**loan_data), name]


@callback(
    Output(delete_modal.ids.modal, "children"),
    Output(delete_modal.ids.modal, "title"),
    Input(ids.delete_offer(ALL), "n_clicks"),
)
def update_delete_modal_content(delete_trigger):  # pylint: disable = unused-argument
    """Update the content of the offer modal"""
    if not (ctx.triggered_id and ctx.triggered[0]["value"]):
        return [None] * 2

    name = ctx.triggered_id["name"]
    return [delete_modal.modal_content(name), f"Delete {name}"]


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
                value_placeholder="Change",
            )
            for i in range(2)
        ]
    else:
        items = [
            timeline_input_item(
                date_id=ids.rates_change_date_item(i),
                value_id=ids.rates_change_value_item(i),
                delete_id=ids.rates_change_delete_item(i),
                value_placeholder="Change",
                **change,
            )
            for i, change in enumerate(rates_changes)
        ] + [
            timeline_input_item(
                date_id=ids.rates_change_date_item(1),
                value_id=ids.rates_change_value_item(1),
                delete_id=ids.rates_change_delete_item(1),
                value_placeholder="Change",
            )
        ] * (
            len(rates_changes) == 1
        )

    return items


clientside_callback(
    """function(dates, values, deletes, add, current) {
        const ctx = window.dash_clientside.callback_context
        const no_update = window.dash_clientside.no_update
        if (ctx.triggered.length === 0 || ctx.triggered[0].value == null) {
            return no_update
        }
        if (ctx.triggered[0].prop_id.includes("add")) {
            return [...(current || [{date: null, change: null}]), {date: null, change: null}]
        }
        if (ctx.triggered[0].prop_id.includes("delete")) {
            const { order } = JSON.parse(ctx.triggered[0].prop_id.split(".")[0])
            return current.filter((x, i) => i !== order)
        }
        const latest = dates.map((d, i) => ({date: d, change: values[i]}))

        window.console.log(latest)
        if (JSON.stringify(current) === JSON.stringify(latest)) {
            return no_update
        }

        return latest
    }""",
    Output(ids.rates_changes, "data"),
    Input(ids.rates_change_date_item(ALL), "value"),
    Input(ids.rates_change_value_item(ALL), "value"),
    Input(ids.rates_change_delete_item(ALL), "n_clicks"),
    Input(ids.add_rates_change, "n_clicks"),
    State(ids.rates_changes, "data"),
)
