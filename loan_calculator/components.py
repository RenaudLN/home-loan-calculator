import dash_mantine_components as dmc
import pandas as pd
from dash import dcc


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
        dmc.TableTr([dmc.TableTh(col, style={"textAlign": "left" if i == 0 else "right"}) for i, col in enumerate(columns)])
    ]
    rows = [
        dmc.TableTr(
            [
                dmc.TableTd(
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
    table_children = [dmc.TableThead(header), dmc.TableTbody(rows)]
    return dmc.ScrollArea(
        dmc.Table(table_children, **kwargs), style={"paddingBottom": 12}, type="auto", offsetScrollbars=False
    )


class LoadingOverlay(dcc.Loading):
    """A loading overlay component."""

    def __init__(self, children, **kwargs):
        super().__init__(
            children,
            custom_spinner=dmc.Loader(),
            delay_show=500,
            **kwargs,
        )
