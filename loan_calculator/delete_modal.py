import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify


class ids:  # pylint: disable = invalid-name
    """Loan modal IDs"""

    modal = "delete_modal"

    @staticmethod
    def delete_button(name): return {"type": "delete-button", "name": name}


def layout():
    """Loan modal layout"""
    return dmc.Modal(
        id=ids.modal,
        centered=True,
        size="md",
        withCloseButton=True,
        title=None,
        children=modal_content(),
    )


def modal_content(name: str = None):
    """Modal content"""
    if not name:
        return None

    return html.Div(
        [
            dmc.Alert(
                "There is no going back.",
                title=f"Do you want to delete this offer: {name}?",
                color="red",
                icon=DashIconify(icon="carbon:delete"),
            ),
            html.Div(
                dmc.Button("Confirm Deletion", id=ids.delete_button(name), color="red", variant="outline"),
                style={"display": "flex", "justifyContent": "end", "width": "100%", "marginTop": 24},
            ),
        ]
    )
