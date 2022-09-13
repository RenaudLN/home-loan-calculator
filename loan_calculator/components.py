import dash_mantine_components as dmc
import pandas as pd
from dash import dcc, html
from dash_iconify import DashIconify


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


def table(df: pd.DataFrame, truncate: int = None, **kwargs) -> dmc.Table:
    """DMC table based on a pandas dataframe"""
    if truncate:
        df = pd.concat(
            [
                df.head(truncate if df.shape[0] > truncate + 1 else truncate + 1),
                pd.DataFrame([["..."] * df.shape[1]], columns=df.columns) if df.shape[0] > truncate + 1 else None,
            ]
        )
    columns, values = df.columns, df.values
    header = [
        html.Tr([html.Th(col, style={"textAlign": "left" if i == 0 else "right"}) for i, col in enumerate(columns)])
    ]
    rows = [
        html.Tr(
            [
                html.Td(
                    cell,
                    style={
                        "textAlign": "left" if i == 0 else "right",
                        "whiteSpace": "nowrap",
                        "width": "1%" if i == 0 else "auto",
                    },
                )
                for i, cell in enumerate(row)
            ]
        )
        for row in values
    ]
    table_children = [html.Thead(header), html.Tbody(rows)]
    return dmc.ScrollArea(
        dmc.Table(table_children, **kwargs), style={"paddingBottom": 12}, type="auto", offsetScrollbars=False
    )


def timeline_input_item(  # pylint: disable = too-many-arguments
    date_id: dict,
    value_id: dict,
    delete_id: dict,
    date: str = None,
    change: float = None,
    value_placeholder: str = None,
):
    """Timeline item with inputs for date and value"""
    bullet = None
    if change is not None:
        if change > 0:
            bullet = [DashIconify(icon="carbon:caret-up", color="red", height=20)]
        elif change < 0:
            bullet = [DashIconify(icon="carbon:caret-down", color="lime", height=20)]
        else:
            bullet = [DashIconify(icon="carbon:subtract", color="blue", height=20)]

    return dmc.TimelineItem(
        html.Div(
            [
                html.Div(
                    [
                        dmc.DatePicker(
                            placeholder="Date",
                            value=date,
                            id=date_id,
                            inputFormat="YYYY-MM",
                            size="xs",
                            allowFreeInput=True,
                            clearable=False,
                        ),
                        dmc.Space(h="xs"),
                        dcc.Input(
                            type="number",
                            placeholder=value_placeholder,
                            # debounce=True,
                            value=change,
                            id=value_id,
                            className="xs",
                        ),
                    ],
                    style={"flex": "1"},
                ),
                html.Div(
                    dmc.Button(
                        DashIconify(icon="carbon:close"),
                        compact=True,
                        variant="subtle",
                        color="red",
                        style={"padding": "0 4px"},
                        id=delete_id,
                    ),
                ),
            ],
            style={"display": "flex", "alignItems": "center", "gap": "0.25rem"},
        ),
        bullet=bullet,
    )
