import dash_mantine_components as dmc
from dash import ALL, Input, Output, State, callback, clientside_callback, ctx, dcc, html, no_update, register_page
from dash_iconify import DashIconify

from loan_calculator import analytics, loan_modal, plots
from loan_calculator.aio_appshell import synchronise_boolean_function

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
                style={"flex": "1"},
            ),
            dcc.Store(id=ids.loans, storage_type="local"),
            html.Button(style={"display": "none"}, id=ids.trigger),
        ],
        style={"display": "flex", "gap": "0.25rem"},
    )


def project_sidebar():
    """Sidebar with project-level data"""
    return html.Div(
        [
            dmc.Text("My Project", weight="bold", style={"lineHeight": "40px"}),
            html.Div(
                [
                    dmc.NumberInput(
                        label="Property Value ($)",
                        min=0,
                        step=10_000,
                        precision=2,
                        id=ids.property_value,
                        value=600_000,
                    ),
                    dmc.Space(h="sm"),
                    dmc.NumberInput(
                        label="Starting Capital ($)",
                        min=0,
                        step=10_000,
                        precision=2,
                        id=ids.start_capital,
                        value=150_000,
                    ),
                    dmc.Space(h="sm"),
                    dmc.NumberInput(
                        label="Monthly income ($)",
                        description="After-tax income",
                        min=0,
                        step=500,
                        precision=2,
                        id=ids.monthly_income,
                        value=9_000,
                    ),
                    dmc.Space(h="sm"),
                    dmc.NumberInput(
                        label="Monthly Costs ($)",
                        description="Excludes loan repayment",
                        min=0,
                        step=500,
                        precision=2,
                        id=ids.monthly_costs,
                        value=4_000,
                    ),
                    dmc.Space(h="sm"),
                    dmc.DatePicker(
                        id=ids.start_date,
                        label="Settlement Date",
                        allowFreeInput=True,
                        value="2023-01-01",
                    ),
                    dmc.Space(h="sm"),
                    dmc.NumberInput(
                        id=ids.stamp_duty_rate,
                        min=0,
                        step=1,
                        precision=2,
                        label="Stamp Duty Rate (%)",
                        value=5.5,
                    ),
                ]
            ),
        ],
        style={"marginLeft": "-1rem", "minWidth": 300, "padding": "0 1rem"},
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
                dmc.Button("New Offers", leftIcon=[DashIconify(icon="carbon:add", height=16)], id=ids.new_loan_button),
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


def offers_grid_contents(loans_data: dict, search: str):
    """Offers cards to be displayed in the grid"""
    return [
        dmc.Paper(
            [
                html.Div(
                    [
                        dmc.Text(name or "undefined", weight="bold"),
                        dmc.Text(f"Annual rate: {loan.get('annual_rate', '')} % p.a.", size="sm", color="gray"),
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
        dmc.MultiSelect(id=ids.select, maxSelectedValues=3, persistence=True),
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
        console.log(ctx.triggered)
        if (ctx.triggered.length === 0 || !ctx.triggered[0].value) return dash_clientside.no_update
        const { type, name } = JSON.parse(ctx.triggered[0].prop_id.split(".")[0])
        if (type === "delete-offer") {
            return Object.fromEntries(Object.entries(loans).filter(([n]) => n !== name))
        }
        const params = ctx.states_list[1].filter(s => s.id.name === name).map(s => [s.id.id, s.value])
        const booleans = ctx.states_list[2].filter(s => s.id.name === name).map(s => [s.id.id, s.value])
        const loan = Object.fromEntries(params.concat(booleans))
        console.log(loan)
        if (!loans) return {[loan.name]: loan}
        return {...loans, [loan.name]: loan}
    }""",
    Output(ids.loans, "data"),
    Input(loan_modal.ids.save(ALL), "n_clicks"),
    Input(ids.delete_offer(ALL), "n_clicks"),
    State(ids.loans, "data"),
    State(loan_modal.loan_param(ALL, ALL), "value"),
    State(loan_modal.loan_boolean(ALL, ALL), "checked"),
)

clientside_callback(
    synchronise_boolean_function,
    Output(loan_modal.ids.modal, "opened"),
    Input(ids.new_loan_button, "n_clicks"),
    Input(ids.edit_offer(ALL), "n_clicks"),
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
)
def update_offers(loans_data, search):
    """Update the content of the offers grid"""
    if not loans_data:
        return no_offers_grid_contents()
    return offers_grid_contents(loans_data, search)


@callback(
    Output(ids.comparison_wrapper, "children"),
    Input(ids.select, "value"),
    Input(project_param(ALL), "value"),
    State(ids.loans, "data"),
)
def compute_loan(loans_names, project_params, loans_data):
    """Compute the loan results"""
    if not loans_data or not loans_names:
        return no_update

    project_params = {inp["id"]["id"]: value for inp, value in zip(ctx.inputs_list[1], project_params)}
    data_list = []
    title_list = []
    for name in loans_names:
        loan = loans_data[name] | project_params
        data = analytics.get_loan_data(loan)
        if data is not None:
            data_list.append(data)
            title_list.append(name)

    if not data_list:
        return no_update

    fig = plots.make_comparison_figure(data_list, title_list)
    return dcc.Graph(figure=fig, responsive=True, config={"displayModeBar": False})


@callback(
    Output(loan_modal.ids.modal, "children"),
    Output(loan_modal.ids.modal, "title"),
    Input(ids.new_loan_button, "n_clicks"),
    Input(ids.edit_offer(ALL), "n_clicks"),
    State(ids.loans, "data"),
)
def update_modal_content(new_trigger, edit_triggers, loans_data):  # pylint: disable = unused-argument
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
