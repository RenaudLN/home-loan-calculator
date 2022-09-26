from dataclasses import dataclass
from typing import List, Literal, Union

import dash_mantine_components as dmc
from dash import ALL, MATCH, Input, Output, State, callback, clientside_callback, dcc, html
from dash.development.base_component import Component
from dash_breakpoints import WindowBreakpoints
from dash_iconify import DashIconify

SMALL_THRESHOLD = 800


@dataclass
class PageLink:
    """Page link

    NOTE: icons can be found at https://icon-sets.iconify.design/
    """

    label: str
    href: str
    icon: str


synchronise_function = """function(...inputs) {
    if (
        !window.dash_clientside.callback_context.triggered
        || window.dash_clientside.callback_context.triggered.length < 1
        || !window.dash_clientside.callback_context.triggered.some(x => x.value != undefined)
    ) {
        return window.dash_clientside.no_update
    }
    return window.dash_clientside.callback_context.triggered.filter(x => x.value != undefined)[0].value
}"""

synchronise_boolean_function = """function(...inputs) {
    if (
        !window.dash_clientside.callback_context.triggered
        || window.dash_clientside.callback_context.triggered.length < 1
        || !window.dash_clientside.callback_context.triggered.some(x => x.value != undefined)
    ) {
        return window.dash_clientside.no_update
    }
    return Boolean(window.dash_clientside.callback_context.triggered.filter(x => x.value != undefined)[0].value)
}"""


class AppshellAIO(dmc.MantineProvider):  # pylint: disable = too-many-instance-attributes
    """Dash appshell"""

    class ids:  # pylint: disable = invalid-name
        """Appshell ids, all ids should be defined here"""

        breakpoints = "window-breakpoints"
        breakpoints_layout = "breakpoints-layout-wrapper"
        navbar_link = lambda href: {"type": "navbar-link", "id": href}
        header_logo = "header-logo"
        theme_provider = "theme-provider"
        theme_toggle = "theme-toggle"
        navbar = "navbar"
        pages_content = "_pages_content"
        pages_dummy = "_pages_dummy"
        pages_store = "_pages_store"
        url = "_pages_location"
        redirect = lambda name: {"type": "redirect", "id": name}
        primary_color_ = "__primary-color"
        sidebar_drawer = "sidebar-drawer"
        sidebar_overflow_menu = "sidebar-overflow-menu"
        header_drawer = "header-drawer"
        header_overflow_menu = "header-overflow-menu"

    # Make the ids class a public class
    ids = ids

    def __init__(  # pylint: disable = too-many-arguments, too-many-locals
        self,
        app_title: str = "App Title",
        home_pathname: str = "/",
        page_links: List[Union[PageLink, Component]] = None,
        with_logo: bool = True,
        primary_color: str = "indigo",
        header_slot: Union[Component, List[Component]] = None,
        sidebar_top_slot: Union[Component, List[Component]] = None,
        sidebar_bottom_slot: Union[Component, List[Component]] = None,
        theme: Literal["light", "dark"] = "light",
        additional_themed_content: Union[Component, List[Component]] = None,
    ):
        """
        :param app_title: Title displayed in the header of the app
        :param home_pathname: Pathname to be taken to when clicking on the app logo/title
        :param page_links: Links to be displayed in the sidebar
        :param with_logo: Whether to display a logo next to the title
        :param logos: Overwrite the name of the logos with one or 2 logo names
        :param header_slot: Components to be displayed in the header (on the right)
        :param sidebar_top_slot: Components to be displayed at the top of the sidebar
        :param sidebar_bottom_slot: Components to be displayed at the bottom of the sidebar
        """
        self.app_title = app_title
        self.home_pathname = home_pathname
        self.page_links = page_links
        self.with_logo = with_logo
        self.primary_color = primary_color
        self.header_slot = header_slot
        self.sidebar_top_slot = sidebar_top_slot
        self.sidebar_bottom_slot = sidebar_bottom_slot

        if additional_themed_content is None:
            additional_themed_content = []

        callback(
            Output(self.ids.breakpoints_layout, "children"),
            Input(self.ids.breakpoints, "widthBreakpoint"),
        )(self.change_breakpoint_layout)

        # Define the appshell layout
        super().__init__(
            id=self.ids.theme_provider,
            theme={
                "colorScheme": theme,
                "fontFamily": "'Inter', sans-serif",
                "primaryColor": primary_color,
            },
            styles={
                "Button": {"root": {"fontWeight": 400}},
                "Alert": {"title": {"fontWeight": 500}},
                "AvatarsGroup": {"truncated": {"fontWeight": 500}},
            },
            withGlobalStyles=True,
            withNormalizeCSS=True,
            children=[
                dmc.NotificationsProvider(
                    [
                        html.Div(
                            style={"display": "flex", "flexDirection": "column", "height": "100vh"},
                            id=self.ids.breakpoints_layout,
                        ),
                        dmc.ScrollArea(
                            offsetScrollbars=False,
                            type="auto",
                            children=html.Div(
                                [
                                    html.Div(id=self.ids.pages_content),
                                    html.Div(html.Div(), className="overlay-loader"),
                                ],
                                className="content-wrapper",
                            ),
                            class_name="content-scroll" + " with-sidebar" * self.has_sidebar,
                        ),
                        html.Div(html.Div(), className="overlay-loader"),
                        WindowBreakpoints(
                            id=self.ids.breakpoints,
                            widthBreakpointThresholdsPx=[SMALL_THRESHOLD],
                            widthBreakpointNames=["small", "large"],
                        ),
                        html.Div(id=self.ids.pages_dummy),
                        dcc.Store(id=self.ids.primary_color_, data=primary_color),
                        dcc.Store(id=self.ids.pages_store),
                        dcc.Location(id=self.ids.url, refresh=False),
                    ]
                    + (
                        additional_themed_content
                        if isinstance(additional_themed_content, List)
                        else [additional_themed_content]
                    ),
                    position="bottom-right",
                ),
            ],
        )

    @property
    def has_sidebar(self):
        """Wether a sidebar should be displayed"""
        return self.sidebar_bottom_slot is not None or self.sidebar_top_slot is not None or bool(self.page_links)

    def change_breakpoint_layout(
        self,
        breakpoint_value: Literal["small", "large"],
    ) -> List[Component]:
        """Create the contents/topbar/sidebar depending on the breakpoint_value"""
        if breakpoint_value == "large":
            return [
                self.create_header(breakpoint_value),
                html.Div(
                    [self.create_sidebar()] * self.has_sidebar,
                    className="nav-content-wrapper",
                ),
            ]

        return [
            self.create_header(breakpoint_value),
            self.create_mobile_drawer(),
        ]

    def create_mobile_drawer(self) -> Component:
        """Mobile drawer containing all of the sidebar and header slot on mobile formats"""
        sidebar_contents = self.make_sidebar_contents()
        header_contents = dmc.ScrollArea(
            offsetScrollbars=False,
            type="auto",
            children=html.Div(
                self.header_slot,
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "1rem",
                    "padding": "1rem 0",
                },
            ),
        )
        drawer_contents = [header_contents] * bool(self.header_slot) + [
            html.Div(
                sidebar_contents,
                style={
                    "flex": "1 1 auto",
                    "display": "flex",
                    "flexDirection": "column",
                    "margin": f"{'1rem' if self.header_slot else 0} -1rem 0",
                    "overflow": "hidden",
                },
            ),
        ]

        return dmc.Drawer(
            drawer_contents,
            id=self.ids.header_drawer,
            position="right",
            padding="md",
            class_name="menu-drawer",
        )

    def create_header(self, breakpoint_value: Literal["small", "large"]) -> Component:
        """Create the app's header

        :param app_title: Title displayed in the header of the app
        :param with_logo: Whether to display a logo next to the title
        :param header_slot: Components to be displayed in the header (on the right)
        """

        return dmc.Header(
            height="var(--topbar-height)",
            p="md",
            style={"flex": "0 0 auto"},
            children=[
                dcc.Link(
                    [html.Div(id=self.ids.header_logo)] * self.with_logo
                    + [dmc.Text(self.app_title, size="xl", color="gray")],
                    href=self.home_pathname,
                    style={
                        "textDecoration": "none",
                        "display": "flex",
                        "alignItems": "center",
                        "gap": "0.25rem",
                    },
                ),
                html.Div(
                    style={"display": "flex", "alignItems": "center", "gap": "1rem"},
                    children=(
                        [html.Div(self.header_slot, className="header-slot")]
                        if breakpoint_value == "large"
                        else [
                            dmc.Button(
                                DashIconify(icon="gg:menu-right", height=28),
                                variant="subtle",
                                color="dark",
                                style={"padding": 0, "height": 30},
                                id=self.ids.header_overflow_menu,
                            )
                        ]
                    )
                    + [dmc.ThemeSwitcher(id=self.ids.theme_toggle, style={"cursor": "pointer"})],
                ),
            ],
        )

    def navbar_link(self, page_link: PageLink) -> Component:
        """Styled sidebar link

        :param page_link: Link with a label, a href, and an icon
        """
        return dcc.Link(
            dmc.Text(
                [DashIconify(icon=page_link.icon, height=20), html.Span(page_link.label)], size="md", color="gray"
            ),
            href=page_link.href,
            className="navbar-link",
            id=self.ids.navbar_link(page_link.href),
        )

    def make_sidebar_contents(self):
        """Sidebar contents, used in sidebar and mobile drawer"""
        page_links = self.page_links or []
        return (
            [dmc.ScrollArea(self.sidebar_top_slot, offsetScrollbars=True, class_name="sidebar-slot")]
            * (self.sidebar_top_slot is not None)
            + [
                dmc.ScrollArea(
                    offsetScrollbars=True,
                    type="auto",
                    class_name="nav-links-scroller",
                    children=html.Div(
                        className="nav-links-wrapper",
                        children=[
                            self.navbar_link(page_link) if isinstance(page_link, PageLink) else page_link
                            for page_link in page_links
                        ],
                    ),
                ),
            ]
            * bool(page_links)
            + [dmc.ScrollArea(self.sidebar_bottom_slot, offsetScrollbars=True, class_name="sidebar-slot")]
            * (self.sidebar_bottom_slot is not None)
        )

    def create_sidebar(self) -> Component:
        """Create the app's sidebar

        :param page_links: Links to be displayed in the sidebar
        :param sidebar_top_slot: Components to be displayed at the top of the sidebar
        :param sidebar_bottom_slot: Components to be displayed at the bottom of the sidebar
        """

        return dmc.Navbar(
            id=self.ids.navbar,
            fixed=False,
            class_name="sidebar",
            py="lg",
            children=self.make_sidebar_contents(),
        )

    # Clientside callback to update the Mantine Theme
    # It updates the value in the ThemeProvider and adds a "theme" data attribute to the document body
    clientside_callback(
        """function(colorScheme, primaryColor) {
            if (!colorScheme) return dash_clientside.no_update
            const body = document.body
            body.dataset.theme = colorScheme
            return {
                colorScheme,
                fontFamily: "'Inter', sans-serif",
                primaryColor,
            }
        }""",
        Output(ids.theme_provider, "theme"),
        Input(ids.theme_toggle, "value"),
        State(ids.primary_color_, "data"),
        prevent_initial_callback=True,
    )

    # Sets an active class on navbar-links if the url matches
    clientside_callback(
        """function(pathname, id) {
            const href = id["id"]
            const decodedPathname = decodeURI(pathname)
            if (href === decodedPathname || decodedPathname.startsWith(`${href}/`)) {
                return "navbar-link active"
            }
            return "navbar-link"
        }""",
        Output(ids.navbar_link(MATCH), "className"),
        Input(ids.url, "pathname"),
        State(ids.navbar_link(MATCH), "id"),
    )

    # Create a multiplexer for the url component, allowing multiple callbacks to update the url
    # See Readme for usage
    clientside_callback(
        synchronise_function,
        Output(ids.url, "pathname"),
        Input(ids.redirect(ALL), "data"),
    )

    # Open the drawer on overflow menu click
    clientside_callback(
        synchronise_boolean_function,
        Output(ids.sidebar_drawer, "opened"),
        Input(ids.sidebar_overflow_menu, "n_clicks"),
    )

    clientside_callback(
        synchronise_boolean_function,
        Output(ids.header_drawer, "opened"),
        Input(ids.header_overflow_menu, "n_clicks"),
    )
