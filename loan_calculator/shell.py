import dash_mantine_components as dmc
from dash import ALL, MATCH, Input, Output, State, callback, clientside_callback, dcc, html, page_container
from dash_iconify import DashIconify
from dash_pydantic_form import ModelForm, fields

from loan_calculator.data_models import FutureExpenses, Project, RatesForecast

PRIMARY_COLOR = "teal"

class ids:  # pylint: disable = invalid-name
    """Home IDs"""

    # Project
    theme_provider = "theme-provider"
    theme_toggle = "theme-toggle"
    theme_store = "theme-store"
    project_wrapper = "project-wrapper"
    url = "main-url"
    trigger = "dummy_trigger_btn"

    @staticmethod
    def data_store(name): return {"type": "data-store", "aio_id": name}


def create_header():
    return dmc.AppShellHeader(
        px=25,
        children=[
            dmc.Group(
                justify="space-between",
                align="center",
                h="100%",
                children=[
                    dmc.Group(
                        [
                            dmc.ActionIcon(
                                DashIconify(
                                    icon="radix-icons:hamburger-menu",
                                    width=25,
                                ),
                                id="drawer-hamburger-button",
                                variant="transparent",
                                size="lg",
                                hiddenFrom="lg",
                            ),
                            dmc.Anchor(
                                [
                                    dmc.Image(src="/assets/logo-light-theme.png", w=32, h=32, darkHidden=True, mt=-2),
                                    dmc.Image(src="/assets/logo-dark-theme.png", w=32, h=32, lightHidden=True, mt=-2),
                                    "Loan Calculator",
                                ],
                                size="xl",
                                href="/",
                                underline=False,
                                style={"display": "flex", "alignItems": "center", "gap": "0.75rem"},
                            ),
                        ],
                        gap="md",
                    ),
                    dmc.Group(
                        justify="flex-end",
                        h=31,
                        gap="md",
                        children=[
                            dmc.ActionIcon(
                                [
                                    DashIconify(
                                        icon="radix-icons:sun",
                                        width=25,
                                        id="light-theme-icon",
                                    ),
                                    DashIconify(
                                        icon="radix-icons:moon",
                                        width=25,
                                        id="dark-theme-icon",
                                    ),
                                ],
                                variant="transparent",
                                color="yellow",
                                id=ids.theme_toggle,
                                size="lg",
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def create_navbar():
    return dmc.AppShellNavbar(
        dmc.ScrollArea(
            offsetScrollbars=True,
            type="scroll",
            style={"height": "100%"},
            children=dmc.Stack(
                gap=0,
                children=[
                    dmc.Text("My Project", style={"lineHeight": "40px"}, size="sm", fw=600),
                    html.Div(
                        dmc.Skeleton(),
                        id=ids.project_wrapper,
                    ),
                ],
                p="2rem 1rem 0.5rem 1.5rem",
            ),
        )
    )


def create_navbar_drawer():
    return dmc.Drawer(
        id="components-navbar-drawer",
        overlayProps={"opacity": 0.55, "blur": 3},
        zIndex=1500,
        offset=10,
        radius="md",
        withCloseButton=False,
        size="75vw",
        children=dmc.Skeleton(),
        trapFocus=False,
    )


appshell = dmc.MantineProvider(
    id=ids.theme_provider,
    defaultColorScheme="auto",
    theme={
        "primaryColor": PRIMARY_COLOR,
        "fontFamily": "'Inter', sans-serif",
        "colors": {
            "dark": [
                "#f4f4f5",
                "#e4e4e7",
                "#d4d4d8",
                "#a1a1aa",
                "#71717a",
                "#52525b",
                "#3f3f46",
                "#27272a",
                "#18181b",
                "#09090b",
            ],
        },
    },
    children=[
        dcc.Store(id=ids.theme_store, storage_type="local"),
        dcc.Location(id=ids.url, refresh="callback-nav"),
        dmc.NotificationProvider(zIndex=2000),
        html.Div(style={"display": "none"}, id=ids.trigger),
        dmc.AppShell(
            [
                create_header(),
                create_navbar(),
                create_navbar_drawer(),
                dmc.AppShellMain(children=page_container),
            ],
            header={"height": 56},
            padding="xl",
            zIndex=20,
            navbar={
                "width": 350,
                "breakpoint": "lg",
                "collapsed": {"mobile": True},
            },
        ),
        *[
            dcc.Store(id=ids.data_store(name), storage_type="local")
            for name in ["project", "rates", "expenses"]
        ]
    ],
)


clientside_callback(
    """
    function(data) {
        return data
    }
    """,
    Output(ids.theme_provider, "forceColorScheme"),
    Input(ids.theme_store, "data"),
)

clientside_callback(
    """
    function(n_clicks, data) {
        return data === "dark" ? "light" : "dark";
    }
    """,
    Output(ids.theme_store, "data"),
    Input(ids.theme_toggle, "n_clicks"),
    State(ids.theme_store, "data"),
    prevent_initial_call=True,
)

@callback(
    Output(ids.project_wrapper, "children"),
    Input(ids.project_wrapper, "id"),
    State(ids.data_store(ALL), "data"),
)
def update_project_wrapper(_, data_stores):
    project_data, rates_data, expenses_data = data_stores
    project = Project.model_construct(**(project_data or {}))
    rates_forecast = RatesForecast.model_construct(**(rates_data or {}))
    expenses = FutureExpenses.model_construct(**(expenses_data or {}))

    return [
        ModelForm(project, aio_id="project", form_id="sidebar", debounce_inputs=500),
        dmc.Space(h="md"),
        dmc.Accordion(
            [
                dmc.AccordionItem(
                    value="rates",
                    children=[
                        dmc.AccordionControl("Interest rates projection", px="0.5rem"),
                        dmc.AccordionPanel(
                            ModelForm(
                                rates_forecast,
                                aio_id="rates",
                                form_id="sidebar",
                                debounce_inputs=500,
                                fields_repr={"changes": fields.Table(table_height=200, title=" ")},
                            ),
                            px="0.5rem",
                            pt="0.25rem",
                        ),
                    ],
                ),
                dmc.AccordionItem(
                    value="expenses",
                    children=[
                        dmc.AccordionControl("Future expenses", px="0.5rem"),
                        dmc.AccordionPanel(
                            ModelForm(
                                expenses,
                                aio_id="expenses",
                                form_id="sidebar",
                                debounce_inputs=500,
                                fields_repr={"expenses": fields.Table(table_height=200, title=" ")},
                            ),
                            px="0.5rem",
                            pt="0.25rem",
                        ),
                    ],
                ),
            ],
            mx="-0.5rem",
        ),
    ]

clientside_callback(
    """(val) => val""",
    Output(ids.data_store(MATCH), "data"),
    Input(ModelForm.ids.main(MATCH, "sidebar"), "data"),
)
