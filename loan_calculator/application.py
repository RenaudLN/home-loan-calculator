import dash_mantine_components as dmc
from dash import Dash, _dash_renderer

from loan_calculator.shell import create_appshell

_dash_renderer._set_react_version("18.2.0")

app = Dash(
    __name__,
    meta_tags=[
        {"charset": "utf-8"},
        {"name": "viewport", "content": "width=device-width, initial-scale=1, shrink-to-fit=no"},
    ],
    use_pages=True,
    external_stylesheets=dmc.styles.ALL,
)
app.config.suppress_callback_exceptions = True
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
server = app.server


app.layout = create_appshell()


if __name__ == "__main__":
    app.run_server(debug=True)
