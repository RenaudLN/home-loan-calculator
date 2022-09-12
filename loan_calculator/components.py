import dash_mantine_components as dmc
from dash import dcc, html


def number_input(
    *,
    id: str,  # pylint: disable = redefined-builtin
    label: str,
    description: str = None,
    **kwargs,
):
    """Re-build dmc NumberInput but with possible persistence"""
    return html.Div(
        [dmc.Text(label, style={"marginBottom": 4, "fontSize": "0.875rem"})]
        + [dmc.Text(description, style={"marginBottom": 4, "marginTop": -4, "fontSize": "0.75rem"}, color="gray")]
        * bool(description)
        + [
            dcc.Input(type="number", id=id, **kwargs),
        ],
    )
