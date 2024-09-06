import dash_mantine_components as dmc
from dash import MATCH, Input, Output, clientside_callback, html
from dash_iconify import DashIconify
from dash_pydantic_form import ModelForm

from loan_calculator.data_models.offer import Offer


class ids:  # pylint: disable = invalid-name
    """Offer modal IDs"""

    modal = "loan_modal"
    save = lambda name: {"type": "save-offer", "name": name}


def layout(name: str = "__new__", **kwargs):
    """Offer modal layout"""
    return dmc.Modal(
        id=ids.modal,
        centered=True,
        size="80vw",
        withCloseButton=True,
        title="New Offer",
        children=modal_content(name, **kwargs),
    )


def modal_content(name: str, **kwargs):
    """Content of the modal, used to change the content when clicking on the edit button"""
    offer = Offer.model_construct(name=name, **kwargs)
    return html.Div(
        [
            ModelForm(
                offer, aio_id="offer", form_id="modal",
                fields_repr={
                    "name": {"n_cols": 4},
                    "fixed_rate": {"visible": ("with_fixed_rate", "==", True)},
                    "fixed_rate_duration": {"visible": ("with_fixed_rate", "==", True)},
                    "with_fixed_rate": {"n_cols": 4},
                    "with_offset_account": {"n_cols": 4},
                }
            ),
            html.Div(
                dmc.Button("Save", leftSection=DashIconify(icon="carbon:save", height=16), id=ids.save(name)),
                style={"display": "flex", "justifyContent": "end", "gridColumn": "1 / -1"},
            ),
        ],
    )
