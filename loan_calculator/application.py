import os

import dash_mantine_components as dmc
from dash import Dash, clientside_callback, Input, Output
from dash_iconify import DashIconify
from loan_calculator.aio_appshell import AppshellAIO, PageLink, synchronise_boolean_function
from loan_calculator import loan_modal


app = Dash(
    __name__,
    meta_tags=[
        {"charset": "utf-8"},
        {"name": "viewport", "content": "width=device-width, initial-scale=1, shrink-to-fit=no"},
    ],
    use_pages=True,
)
app.config.suppress_callback_exceptions = True
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
server = app.server


class ids:
    new_loan_button = "new_loan_button"


appshell = AppshellAIO(
    "Loan Calculator",
    header_slot=[dmc.Button("Add Loan", leftIcon=[DashIconify(icon="carbon:add")], id=ids.new_loan_button)],
    additional_themed_content=[
        loan_modal.layout()
    ]
)

clientside_callback(
    synchronise_boolean_function,
    Output(loan_modal.ids.modal, "opened"),
    Input(ids.new_loan_button, "n_clicks")
)

app.layout = appshell


if __name__ == "__main__":
    app.run_server(debug=True)
