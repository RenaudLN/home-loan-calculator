import dash_mantine_components as dmc
import pandas as pd
from dash import ALL, Input, Output, State, callback, clientside_callback, ctx, dcc, html, no_update, register_page
from dash_iconify import DashIconify
from dash_pydantic_form import ModelForm
from pydantic import ValidationError

from loan_calculator import analytics, delete_modal, loan_modal, plots
from loan_calculator.components import LoadingOverlay, table
from loan_calculator.data_models import FutureExpenses, Offer, Project, RatesForecast
from loan_calculator.shell import ids as shell_ids

register_page(__name__, "/", title="Loan Calculator")


class ids:  # pylint: disable = invalid-name
    """Home IDs"""

    # Loans
    new_offer_button = "new_offer_button"
    search = "search_loans"
    offers_wrapper = "offers_wrapper"
    # Comparison
    comparison_wrapper = "offer_comparison_wrapper"
    loans = "loans_store"
    select = "loan_selection"
    #
    first_10 = "first_10"

    @staticmethod
    def edit_offer(name): return {"type": "edit-offer", "name": name}

    @staticmethod
    def delete_offer(name): return {"type": "delete-offer", "name": name}

    @staticmethod
    def create_offer(name): return {"type": "create-offer", "name": name}


def layout():
    """Layout function"""
    return html.Div(
        [
            dmc.Tabs(
                children=[
                    dmc.TabsList(
                        [
                            dmc.TabsTab("My offers", value="my_offers"),
                            dmc.TabsTab("Offer comparison", value="comparison"),
                        ],
                        className="bg-sticky",
                    ),
                    dmc.TabsPanel(offers_grid(), value="my_offers"),
                    dmc.TabsPanel(offers_comparison(), value="comparison"),
                ],
                style={"maxWidth": "1200px", "margin": "0 auto"},
                value="comparison",
            ),
            dcc.Store(id=ids.loans, storage_type="local"),
            loan_modal.layout(),
            delete_modal.layout(),
        ],
    )


def offers_grid():
    """Content of first tab with a grid of cards of offers"""
    return [
        html.Div(
            [
                dmc.TextInput(
                    id=ids.search,
                    style={"flex": "1"},
                    leftSection=DashIconify(icon="carbon:search"),
                ),
                dmc.Button("Add Offer", leftSection=DashIconify(icon="carbon:add", height=16), id=ids.new_offer_button),
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
                        dmc.Text(name or "undefined", fw="bold"),
                        dmc.Space(h=12),
                        dmc.Text(
                            f"Principal: ${(loan.get('borrowed_share') or 0) * (property_value or 0) / 100:,.0f}",
                            size="sm",
                            c="gray",
                        ),
                        dmc.Space(h=3),
                        dmc.Text(f"Annual rate: {loan.get('rate', '')}% p.a.", size="sm", c="gray"),
                    ],
                    style={"flex": "1"},
                ),
                html.Div(
                    [
                        dmc.Button(
                            DashIconify(icon="carbon:edit"),
                            size="compact-md",
                            variant="subtle",
                            style={"padding": "0 4px"},
                            id=ids.edit_offer(name),
                        ),
                        dmc.Button(
                            DashIconify(icon="carbon:trash-can"),
                            size="compact-md",
                            variant="subtle",
                            color="red",
                            style={"padding": "0 4px"},
                            id=ids.delete_offer(name),
                        ),
                    ],
                    style={"display": "flex", "flexDirection": "column"},
                    className="hover-visible",
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
        html.Div(
            dmc.Text("Start by creating offers", c="gray"),
            style={
                "height": "min(400px, calc(90vh - 200px))",
                "display": "grid",
                "placeContent": "center",
                "cursor": "pointer",
            },
            id=ids.create_offer("first"),
        ),
        style={"gridColumn": "1 / -1"},
        radius="md",
    )


def offers_comparison():
    """Content of second tab with results graph"""
    return [
        dmc.Group(
            [
                dmc.MultiSelect(id=ids.select, persistence=True, maxValues=2, value=[], data=[], style={"flex": 1}),
                dmc.Switch("Show first 10 years", id=ids.first_10),
            ],
            pos="sticky",
            top="3.25rem",
            style={"zIndex": 10},
            p="1rem 0",
            className="bg-sticky",
        ),
        LoadingOverlay(offers_comparison_empty_content(), id=ids.comparison_wrapper),
    ]


def offers_comparison_empty_content():
    """Content of comparison tab when no offer is selected"""
    return dmc.Paper(
        html.Div(
            dmc.Text("Create loan offers then select them above.", c="gray"),
            style={
                "height": "min(400px, calc(90vh - 200px))",
                "display": "grid",
                "placeContent": "center",
                "cursor": "pointer",
            },
            id=ids.create_offer("comparison"),
        ),
        radius="md",
    )


clientside_callback(
    """function(n_clicks, deletes, loans, new_loan) {
        const ctx = dash_clientside.callback_context
        if (!ctx.triggered || ctx.triggered.length === 0 || !ctx.triggered[0].value) return dash_clientside.no_update
        const { type, name } = JSON.parse(ctx.triggered[0].prop_id.split(".")[0])
        if (type === "delete-button") {
            return Object.fromEntries(Object.entries(loans).filter(([n]) => n !== name))
        }
        if (!loans) return {[new_loan.name]: new_loan}
        return {...loans, [new_loan.name]: new_loan}
    }""",
    Output(ids.loans, "data"),
    Input(loan_modal.ids.save(ALL), "n_clicks"),
    Input(delete_modal.ids.delete_button(ALL), "n_clicks"),
    State(ids.loans, "data"),
    State(ModelForm.ids.main("offer", "modal"), "data"),
)


clientside_callback(
    """function(a, b, c, d, opened) {
        const ctx = window.dash_clientside.callback_context
        if (ctx.triggered.length === 0 || !ctx.triggered[0].value) return window.dash_clientside.no_update
        return !opened
    }""",
    Output(loan_modal.ids.modal, "opened"),
    Input(ids.new_offer_button, "n_clicks"),
    Input(ids.create_offer(ALL), "n_clicks"),
    Input(ids.edit_offer(ALL), "n_clicks"),
    Input(loan_modal.ids.save(ALL), "n_clicks"),
    State(loan_modal.ids.modal, "opened"),
)


clientside_callback(
    """function(a, b, c, opened) {
        const ctx = window.dash_clientside.callback_context
        if (!ctx.triggered || ctx.triggered.length === 0 || !ctx.triggered[0].value) return window.dash_clientside.no_update
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
    Input(shell_ids.trigger, "n_clicks"),
    State(ids.select, "value"),
)


@callback(
    Output(ids.offers_wrapper, "children"),
    Input(ids.loans, "data"),
    Input(ids.search, "value"),
    Input(ModelForm.ids.main("project", "sidebar"), "data"),
)
def update_offers(loans_data, search, project_data):
    """Update the content of the offers grid"""
    if not loans_data:
        return no_offers_grid_contents()
    return offers_grid_contents(loans_data, search, project_data["property_value"])


@callback(
    Output(ids.comparison_wrapper, "children"),
    Input(ids.select, "value"),
    Input(ids.first_10, "checked"),
    Input(ModelForm.ids.main("project", "sidebar"), "data"),
    Input(ModelForm.ids.main("rates", "sidebar"), "data"),
    Input(ModelForm.ids.main("expenses", "sidebar"), "data"),
    State(ids.loans, "data"),
    State(shell_ids.breakpoints, "widthBreakpoint"),
)
def compute_loan(
    loans_names: list[str],
    first_10: bool,
    project_data: dict,
    rates_change: dict,
    expenses: dict,
    loans_data: dict,
    breakpoint: str,
):
    """Compute the loan results"""
    if not loans_data or not loans_names:
        return offers_comparison_empty_content()

    try:
        project = Project(**project_data)
    except ValidationError:
        return no_update

    rates_change = RatesForecast(**rates_change)
    expenses = FutureExpenses(**expenses)

    data_list = []
    title_list = []
    feasible_list = []
    for name in loans_names:
        try:
            offer = Offer(**loans_data[name])
        except ValidationError:
            continue
        data, feasible = analytics.compute_loan_timeseries(
            project=project,
            offer=offer,
            rates_change=rates_change,
            expenses=expenses,
        )
        if data is not None:
            data_list.append(data)
            title_list.append(name)
            feasible_list.append(feasible)

    if not data_list:
        return no_update

    fig = plots.make_dmc_chart(
        [d.iloc[:10 * 12] if first_10 else d for d in data_list],
        title_list,
        feasible_list,
        breakpoint,
    )

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
        dmc.Space(h="lg"),
        fig,
    ]


@callback(
    Output(loan_modal.ids.modal, "children"),
    Output(loan_modal.ids.modal, "title"),
    Input(ids.new_offer_button, "n_clicks"),
    Input(ids.create_offer(ALL), "n_clicks"),
    Input(ids.edit_offer(ALL), "n_clicks"),
    State(ids.loans, "data"),
)
def update_offer_modal_content(  # pylint: disable = unused-argument
    new_trigger, create_triggers, edit_triggers, loans_data
):
    """Update the content of the offer modal"""
    if not ctx.triggered_id:
        return [no_update] * 2

    if isinstance(ctx.triggered_id, dict) and ctx.triggered_id["type"] == "edit-offer":
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
