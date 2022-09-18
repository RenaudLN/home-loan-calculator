import itertools
from copy import deepcopy
from dataclasses import dataclass
from typing import List, Literal, Tuple, Union

import dash_mantine_components as dmc
from dash import ALL, MATCH, Input, Output, State, clientside_callback, dcc, html
from dash.development.base_component import Component
from dash_iconify import DashIconify


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


class AppshellAIO(dmc.MantineProvider):
    """Dash appshell"""

    class ids:  # pylint: disable = invalid-name
        """Appshell ids, all ids should be defined here"""

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
        if additional_themed_content is None:
            additional_themed_content = []

        has_sidebar = sidebar_bottom_slot is not None or sidebar_top_slot is not None or bool(page_links)
        has_mobile_drawer = header_slot is not None or has_sidebar

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
                            [
                                self.create_header(app_title, home_pathname, with_logo, header_slot, has_mobile_drawer),
                                html.Div(
                                    [self.create_sidebar(page_links, sidebar_top_slot, sidebar_bottom_slot)]
                                    * int(has_sidebar)
                                    + [
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
                                            style={"flex": "1 1 auto"},
                                        ),
                                        dcc.Store(id=self.ids.pages_store),
                                        dcc.Location(id=self.ids.url, refresh=False),
                                    ],
                                    className="nav-content-wrapper",
                                ),
                                html.Div(id=self.ids.pages_dummy),
                                dcc.Store(id=self.ids.primary_color_, data=primary_color),
                            ],
                            style={"display": "flex", "flexDirection": "column", "height": "100vh"},
                        ),
                    ]
                    + [self.create_mobile_drawer(page_links, header_slot, sidebar_top_slot, sidebar_bottom_slot)]
                    * int(has_mobile_drawer)
                    + (
                        additional_themed_content
                        if isinstance(additional_themed_content, List)
                        else [additional_themed_content]
                    ),
                    position="bottom-right",
                ),
            ],
        )

    def create_mobile_drawer(
        self,
        page_links: List[Union[PageLink, Component]],
        header_slot: Union[Component, List[Component]],
        sidebar_top_slot: Union[Component, List[Component]],
        sidebar_bottom_slot: Union[Component, List[Component]],
    ) -> Component:
        """Mobile drawer containing all of the sidebar and header slot on mobile formats"""
        sidebar_contents = self.make_sidebar_contents(page_links, sidebar_top_slot, sidebar_bottom_slot)
        header_contents = dmc.ScrollArea(
            offsetScrollbars=False,
            type="auto",
            children=html.Div(
                header_slot,
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "1rem",
                    "padding": "1rem 0",
                },
            ),
        )
        drawer_contents = [
            header_contents,
            html.Div(
                sidebar_contents,
                style={"flex": "1 1 auto", "display": "flex", "flexDirection": "column", "margin": "1rem -1rem 0"},
            ),
        ]

        # Synchronise the replicated items in the drawer with the originals
        # NOTE: This is only done once at the app creation so no dynamic buttons /searches here
        slot_ids = get_all_ids(drawer_contents) if drawer_contents is not None else []
        drawer_contents = make_ids_unique(drawer_contents, "header_drawer")
        drawer_ids = get_all_ids(drawer_contents) if drawer_contents is not None else []
        for (s_id, attributes), (d_id, _) in zip(slot_ids, drawer_ids):
            for attribute in attributes:
                if "type" in d_id and d_id["type"] == "navbar-link" and attribute == "className":
                    continue
                clientside_callback(
                    synchronise_function,
                    Output(s_id, attribute),
                    Input(d_id, attribute),
                )

        return dmc.Drawer(
            drawer_contents,
            id=self.ids.header_drawer,
            position="right",
            padding="md",
            class_name="menu-drawer",
        )

    def create_header(  # pylint: disable = too-many-arguments
        self,
        app_title: str,
        home_pathname: str,
        with_logo: bool,
        header_slot: Union[Component, List[Component]],
        has_mobile_drawer: bool,
    ) -> Component:
        """Create the app's header

        :param app_title: Title displayed in the header of the app
        :param with_logo: Whether to display a logo next to the title
        :param header_slot: Components to be displayed in the header (on the right)
        """

        return dmc.Header(
            height=64,
            p="md",
            style={"flex": "0 0 auto"},
            children=html.Div(
                [
                    dcc.Link(
                        [html.Div(id=self.ids.header_logo)] * int(with_logo)
                        + [dmc.Text(app_title, size="xl", color="gray")],
                        href=home_pathname,
                        style={
                            "textDecoration": "none",
                            "display": "flex",
                            "alignItems": "center",
                            "gap": "0.25rem",
                        },
                    ),
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "1rem"},
                        children=[
                            dmc.MediaQuery(
                                html.Div(header_slot, className="header-slot"),
                                smallerThan=800,
                                styles={"display": "none"},
                            )
                        ]
                        + [
                            dmc.MediaQuery(
                                dmc.Button(
                                    DashIconify(icon="eva:menu-fill", height=28),
                                    variant="subtle",
                                    style={"padding": 0, "height": 30},
                                    id=self.ids.header_overflow_menu,
                                ),
                                largerThan=800,
                                styles={"display": "none !important"},
                                class_name="header-slot",
                            ),
                        ]
                        * int(has_mobile_drawer)
                        + [dmc.ThemeSwitcher(id=self.ids.theme_toggle, style={"cursor": "pointer"})],
                    ),
                ],
                id="header_wrapper",
            ),
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

    def make_sidebar_contents(
        self,
        page_links: List[PageLink],
        sidebar_top_slot: Union[Component, List[Component]],
        sidebar_bottom_slot: Union[Component, List[Component]],
    ):
        """Sidebar contents, used in sidebar and mobile drawer"""
        page_links = page_links or []
        return (
            [dmc.ScrollArea(sidebar_top_slot, offsetScrollbars=True, class_name="sidebar-slot")]
            * int(sidebar_top_slot is not None)
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
            + [dmc.ScrollArea(sidebar_bottom_slot, offsetScrollbars=True, class_name="sidebar-slot")]
            * int(sidebar_bottom_slot is not None)
        )

    def create_sidebar(
        self,
        page_links: List[Union[PageLink, Component]],
        sidebar_top_slot: Union[Component, List[Component]] = None,
        sidebar_bottom_slot: Union[Component, List[Component]] = None,
    ) -> Component:
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
            children=self.make_sidebar_contents(page_links, sidebar_top_slot, sidebar_bottom_slot),
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
                return ["navbar-link active", "navbar-link active"]
            }
            return ["navbar-link", "navbar-link"]
        }""",
        [
            Output(ids.navbar_link(MATCH), "className"),
            Output({"prefix": "header_drawer"} | ids.navbar_link(MATCH), "className"),
        ],
        [Input(ids.url, "pathname")],
        [State(ids.navbar_link(MATCH), "id")],
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


def get_all_ids(components: Union[Component, List[Component]]) -> List[Tuple[str, str]]:
    """Retrieve the list of all ids and their synchronisable attributes"""

    def _get_ids_recursive(components: Union[Component, List[Component]]):
        ids = []
        if isinstance(components, List):
            ids += list(itertools.chain.from_iterable([_get_ids_recursive(c) for c in components]))
        elif isinstance(components, Component):
            if "id" in dir(components) and components.id:
                attributes = [
                    x
                    for x in ["data", "n_clicks", "value", "className", "class_name", "options"]
                    if x in components.available_properties
                ]
                ids.append((components.id, attributes))
            if "children" in dir(components) and components.children:
                ids += _get_ids_recursive(components.children)
        return ids

    components = deepcopy(components)
    return _get_ids_recursive(components)


def make_ids_unique(components: Union[Component, List[Component]], prefix: str) -> Union[Component, List[Component]]:
    """Give every component that has an id a new one with a prefix"""

    def _make_unique_recursive(components: Union[Component, List[Component]], prefix: str):
        if isinstance(components, List):
            return [_make_unique_recursive(c, prefix) for c in components]
        if isinstance(components, Component):
            if "id" in dir(components) and components.id:
                if isinstance(components.id, dict):
                    components.id = {"prefix": prefix} | components.id
                else:
                    components.id = {"prefix": prefix, "id": components.id}
            if "children" in dir(components) and components.children:
                components.children = _make_unique_recursive(components.children, prefix)
        return components

    components = deepcopy(components)
    return _make_unique_recursive(components, prefix)
