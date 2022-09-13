from dash import Dash

from loan_calculator.aio_appshell import AppshellAIO

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


appshell = AppshellAIO("Loan Calculator", primary_color="teal")

app.layout = appshell


if __name__ == "__main__":
    app.run_server(debug=True)
