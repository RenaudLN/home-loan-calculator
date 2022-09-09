import dash_mantine_components as dmc
from dash import register_page

register_page(__name__)


def layout():
    """Layout function"""
    return [
        dmc.Title("404 - page not found", order=1),
    ]
