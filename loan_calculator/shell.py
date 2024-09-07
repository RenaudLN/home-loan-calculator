import dash_mantine_components as dmc
from dash import ALL, MATCH, Input, Output, State, callback, clientside_callback, dcc, html, page_container
from dash_iconify import DashIconify
from dash_pydantic_form import ModelForm, fields
from dash_breakpoints import WindowBreakpoints

from loan_calculator.data_models import FutureExpenses, Project, RatesForecast

PRIMARY_COLOR = "yellow"

class ids:  # pylint: disable = invalid-name
    """Home IDs"""

    # Project
    theme_provider = "theme-provider"
    theme_store = "theme-store"
    appshell = "app-shell"
    drawer_button = "drawer-button"
    menu_drawer = "menu-drawer"
    wrapper_sidebar = "project-wrapper-sidebar"
    wrapper_drawer = "project-wrapper-drawer"
    url = "main-url"
    trigger = "dummy_trigger_btn"
    breakpoints = "breakpoints"

    @staticmethod
    def data_store(name): return {"type": "data-store", "aio_id": name}

    @staticmethod
    def theme_toggle(name): return {"type": "theme-toggle", "name": name}


def create_title():
    return dmc.Anchor(
        [
            dmc.Image(src="/assets/logo-light-theme.png", w=28, h=28, darkHidden=True, mt=-2),
            dmc.Image(src="/assets/logo-dark-theme.png", w=28, h=28, lightHidden=True, mt=-2),
            dmc.Text("Loan Calculator"),
        ],
        size="lg",
        href="/",
        underline=False,
        style={"display": "flex", "alignItems": "center", "gap": "0.75rem"},
        c="inherit",
    )


def create_theme_switcher(name: str):
    return dmc.ActionIcon(
        [
            DashIconify(icon="radix-icons:sun", width=25),
            DashIconify(icon="radix-icons:moon", width=25),
        ],
        variant="transparent",
        color="yellow",
        id=ids.theme_toggle(name),
        size="lg",
    )


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
                                id=ids.drawer_button,
                                variant="transparent",
                                size="lg",
                                hiddenFrom="lg",
                            ),
                            create_title(),
                        ],
                        gap="md",
                    ),
                    dmc.Group(
                        justify="flex-end",
                        h=31,
                        gap="md",
                        children=create_theme_switcher("header"),
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
                    dmc.Group(
                        [
                            create_title(),
                            create_theme_switcher("sidebar"),
                        ],
                        justify="space-between",
                    ),
                    dmc.Space(h="md"),
                    dmc.Text("My Project", style={"lineHeight": "40px"}, size="sm", fw=600),
                    html.Div([], id=ids.wrapper_sidebar),
                ],
                p="1rem 1rem 1rem 1.5rem",
            ),
        )
    )


def create_navbar_drawer():
    return dmc.Drawer(
        id=ids.menu_drawer,
        overlayProps={"opacity": 0.55, "blur": 3},
        zIndex=1500,
        offset=10,
        radius="md",
        withCloseButton=False,
        size="75vw",
        children=dmc.Stack(
            gap=0,
            children=[
                dmc.Text("My Project", style={"lineHeight": "40px"}, size="sm", fw=600),
                html.Div([], id=ids.wrapper_drawer),
            ],
        ),
        trapFocus=False,
    )


def create_appshell():
    return dmc.MantineProvider(
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
            WindowBreakpoints(
                id=ids.breakpoints,
                widthBreakpointThresholdsPx=[1200],
                widthBreakpointNames=["mobile", "dekstop"],
            ),
            dmc.AppShell(
                [
                    create_header(),
                    create_navbar(),
                    create_navbar_drawer(),
                    dmc.AppShellMain(children=page_container),
                ],
                header={
                    "height": 56,
                    "collapsed": True,
                },
                padding="xl",
                zIndex=20,
                navbar={
                    "width": 350,
                    "breakpoint": "lg",
                    "collapsed": {"mobile": True},
                },
                id=ids.appshell,
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
    function(trigger, data) {
        if (!trigger.some(x => !!x)) return dash_clientside.no_update
        return data === "dark" ? "light" : "dark";
    }
    """,
    Output(ids.theme_store, "data"),
    Input(ids.theme_toggle(ALL), "n_clicks"),
    State(ids.theme_store, "data"),
    prevent_initial_call=True,
)

@callback(
    Output(ids.wrapper_sidebar, "children"),
    Output(ids.wrapper_drawer, "children"),
    Input(ids.wrapper_sidebar, "id"),
    State(ids.data_store(ALL), "data"),
    State(ids.breakpoints, "widthBreakpoint"),
)
def update_project_wrapper(_, data_stores, breakpoint):
    project_data, rates_data, expenses_data = data_stores
    project = Project.model_construct(**(project_data or {}))
    rates_forecast = RatesForecast.model_construct(**(rates_data or {}))
    expenses = FutureExpenses.model_construct(**(expenses_data or {}))

    children = [
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

    if breakpoint == "mobile":
        return [[], children]

    return [children, []]

clientside_callback(
    """(val) => val""",
    Output(ids.data_store(MATCH), "data"),
    Input(ModelForm.ids.main(MATCH, "sidebar"), "data"),
)

clientside_callback(
    """(n) => !!n""",
    Output(ids.menu_drawer, "opened"),
    Input(ids.drawer_button, "n_clicks"),
)

clientside_callback(
    """(bkpt, cSidebar, cDrawer) => {
        const children = Array.isArray(cSidebar) && cSidebar.length === 0 ? cDrawer : cSidebar
        if (bkpt === "dekstop") {
            return [{height: 56, collapsed: true}, children, []]
        } else {
            return [{height: 56, collapsed: false}, [], children]
        }
    }""",
    Output(ids.appshell, "header"),
    Output(ids.wrapper_sidebar, "children", allow_duplicate=True),
    Output(ids.wrapper_drawer, "children", allow_duplicate=True),
    Input(ids.breakpoints, "widthBreakpoint"),
    State(ids.wrapper_sidebar, "children"),
    State(ids.wrapper_drawer, "children"),
    prevent_initial_call=True,
)
