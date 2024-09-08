from copy import deepcopy
from typing import Literal

import dash_mantine_components as dmc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc
from plotly.subplots import make_subplots

COLOR_DEPOSIT = "rgb(240, 145, 23)"
COLOR_STAMP_DUTY = "rgb(240, 239, 35)"
COLOR_FEE = "rgb(240, 101, 149)"
COLOR_INTEREST = "rgb(132, 94, 247)"
COLOR_PRINCIPAL = "rgb(92, 124, 250)"
COLOR_OFFSET = "rgb(32, 201, 151)"


SERIES_CUMULATIVE = {
    "deposit": {"color": "#12b886", "label": "Deposit"},
    "stamp_duty": {"color": "#ff922b", "label": "Stamp duty"},
    "principal_payment": {"color": "#4c6ef5", "label": "Principal"},
    "interest": {"color": "#be4bdb", "label": "Interest"},
    "fee": {"color": "#e64980", "label": "Fees"},
}
SERIES_MONTHLY = {
    "principal_payment": {"color": "#4c6ef5", "label": "Principal"},
    "interest": {"color": "#be4bdb", "label": "Interest"},
    "fee": {"color": "#e64980", "label": "Fees"},
}
SERIES_OFFSET = {"color": "#fab005", "label": "Offset account"}
BASE_LAYOUT = {
    "hovermode": "x unified",
    "hoverlabel": {
        "bgcolor": "rgba(0, 0, 0, 0.8)",
        "font_color": "#fff",
        "bordercolor": "rgba(0, 0, 0, 0.8)",
        "font_size": 14,
    },
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "var(--plot-font-color)", "family": "'Inter', sans-serif"},
    "xaxis_showgrid": False,
    "yaxis_gridwidth": 2,
    "yaxis_gridcolor": "rgb(128, 128, 128)",
    "yaxis_zerolinecolor": "rgb(128, 128, 128)",
    "yaxis_griddash": "dash",
    "yaxis_ticklabelstandoff": 12,
    "xaxis_ticklabelstandoff": 8,
    "xaxis_title": None,
    "xaxis_tickfont_size": 14,
    "yaxis_tickfont_size": 14,
    "xaxis_title_font_size": 16,
    "yaxis_title_font_size": 16,
    "margin": {"b": 10, "l": 10, "r": 10, "t": 10},
    "showlegend": False,
}


class ids:
    @staticmethod
    def chart(metric, name):
        return {"type": "chart", "metric": metric, "name": name}

    @staticmethod
    def legenditem(metric, name, item):
        return {"type": "legenditem", "metric": metric, "name": name, "item": item}


def create_legend_item(label: str, color: str, metric: str, name: str, active: bool = True):
    return dmc.Group(
        [
            dmc.Box(h=12, w=12, bg=color, style={"borderRadius": "50%"}, mt="-0.25rem"),
            dmc.Text(label),
        ],
        id=ids.legenditem(metric, name, label),
        gap="0.5rem",
        align="center",
        className="legend-item" + (" active" if active else ""),
    )


def make_dmc_chart(
    data_list: list[pd.DataFrame],
    title_list: list[str] = None,
    feasible_list: list[bool] = None,
    breakpoint: Literal["mobile", "desktop"] = "desktop",
):
    cumulative_data = [
        data[list(SERIES_CUMULATIVE)].cumsum()
        .round(2)
        .rename_axis(index="date")
        .reset_index()
        for data in data_list
    ]
    cumulative_y_max = 1.1 * max(x.drop(columns="date").sum(axis=1).max() for x in cumulative_data)
    monthly_y_max = 1.05 * max(x[list(SERIES_MONTHLY)].sum(axis=1).max() for x in data_list)
    text_interval_years = 5
    text_interval_months = text_interval_years * 12

    layout = deepcopy(BASE_LAYOUT)
    if breakpoint == "mobile":
        layout["yaxis_fixedrange"] = True
        layout["xaxis_fixedrange"] = True

    return dmc.SimpleGrid(
        [
            dmc.Paper(
                radius="md",
                p="1rem",
                children=dmc.Stack(
                    [
                        dmc.Text(title, size="md", fw=600, c="yellow.6"),
                        dmc.Group(
                            [
                                create_legend_item(
                                    v["label"],
                                    v["color"],
                                    "cumulative",
                                    title,
                                    (data[k] != 0).any()
                                )
                                for k, v in SERIES_CUMULATIVE.items()
                            ]
                            + [
                                create_legend_item(
                                    SERIES_OFFSET["label"],
                                    SERIES_OFFSET["color"],
                                    "cumulative",
                                    title,
                                    (data["offset"] != 0).any(),
                                )
                            ],
                            gap="0.25rem",
                            justify="end",
                            mb="-0.5rem",
                        ),
                        dcc.Graph(
                            figure=px.area(
                                cdata.rename(columns={k: v["label"] for k, v in SERIES_CUMULATIVE.items()}),
                                x="date",
                                y=[v["label"] for v in SERIES_CUMULATIVE.values()],
                                color_discrete_map={v["label"]: v["color"] for v in SERIES_CUMULATIVE.values()},
                                height=300,
                            )
                            .update_layout(
                                layout,
                                yaxis_title_text="Cumulative ($)",
                                yaxis_autorangeoptions={"include": [0, cumulative_y_max]},
                            )
                            .add_traces(
                                px.line(data[["offset"]].where(data["interest"] > 0, None).ffill().rename_axis(index="date").reset_index(), x="date", y="offset", color_discrete_sequence=[SERIES_OFFSET["color"]])
                                .update_traces(name=SERIES_OFFSET["label"], line_width=3, visible=(data["offset"] != 0).any())
                                .data
                            )
                            .add_scatter(
                                x=cdata["date"],
                                y=cdata.drop(columns="date").sum(axis=1),
                                name="Total",
                                showlegend=False,
                                line=dict(color="rgba(0,0,0,0)"),
                            )
                            .update_traces(hovertemplate="$%{y:.3s}", line_shape="spline")
                            .update_traces(visible=(data["fee"] != 0).any(), selector={"name": "Fees"})
                            .update_traces(visible=(data["stamp_duty"] != 0).any(), selector={"name": "Stamp duty"})
                            .add_scatter(
                                x=cdata.iloc[text_interval_months - 1 :: text_interval_months]["date"],
                                y=cdata.drop(columns="date").sum(axis=1).iloc[text_interval_months - 1 :: text_interval_months],
                                texttemplate="%{y:.3s}",
                                showlegend=False,
                                mode="text",
                                textposition="top center",
                                textfont=dict(size=14, color="#888"),
                                hoverinfo="skip",
                            )
                            ,
                            responsive=True,
                            style={"height": 300},
                            config={"displayModeBar": False},
                            id=ids.chart("cumulative", title),
                            clear_on_unhover=True,
                        ),
                        dmc.Group(
                            [
                                create_legend_item(
                                    v["label"],
                                    v["color"],
                                    "monthly",
                                    title,
                                )
                                for v in SERIES_MONTHLY.values()
                            ],
                            gap="0.25rem",
                            justify="end",
                            mb="-0.5rem",
                        ),
                        dcc.Graph(
                            figure=px.area(
                                data[list(SERIES_MONTHLY)].rename_axis(index="date").reset_index().rename(columns={k: v["label"] for k, v in SERIES_MONTHLY.items()}),
                                x="date",
                                y=[v["label"] for v in SERIES_MONTHLY.values()],
                                color_discrete_map={v["label"]: v["color"] for v in SERIES_MONTHLY.values()},
                                height=300,
                            )
                            .update_layout(
                                layout,
                                yaxis_title_text="Monthly ($)",
                                yaxis_autorangeoptions={"include": [0, monthly_y_max]},
                            )
                            .add_scatter(
                                x=data.index,
                                y=data[list(SERIES_MONTHLY)].sum(axis=1),
                                name="Total",
                                showlegend=False,
                                line=dict(color="rgba(0,0,0,0)"),
                            )
                            .update_traces(hovertemplate="$%{y:.3s}")
                            ,
                            responsive=True,
                            style={"height": 300},
                            config={"displayModeBar": False},
                            id=ids.chart("monthly", title),
                            clear_on_unhover=True,
                        ),
                    ],
                    style={"flex": 1},
                    gap="xs",
                )
            )
            for data, cdata, title in zip(data_list, cumulative_data, title_list)
        ],
        cols={"base": 1, "lg": len(data_list)},
        spacing="lg",
    )
px.line

def make_comparison_figure(  # pylint: disable = too-many-locals
    data_list: list[pd.DataFrame], title_list: list[str] = None, feasible_list: list[bool] = None
) -> go.Figure:
    """Create a figure comparing several offers

    :param data_list: List of dataframes representing the timeseries of the loan, each dataframe has the columns:
        "principal_paid", "offset", "principal_payment", "interest", "fee", "repayment", "deposit", "stamp_duty"
    :param title_list: Title for each dataframe
    """
    if not isinstance(data_list, list):
        data_list = [data_list]

    # Create the subplots and set the layout
    fig = (
        make_subplots(rows=2, cols=len(data_list), shared_xaxes=True, vertical_spacing=0.1, horizontal_spacing=0.02)
        .update_layout(
            height=600,
            margin=dict(b=30, t=50, l=50, r=20, pad=8),
            yaxis_title="Cumulative ($)",
            title_x=0.5,
            title_xanchor="center",
            title_font_color="#000",
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="rgba(0, 0, 0, 0.8)",
                font_color="#fff",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="rgb(128, 128, 128)",
            legend=dict(y=-0.1, yanchor="top", orientation="h", x=1, xanchor="right"),
            **{
                f"yaxis{i}": dict(
                    title="Monthly ($)" if i == len(data_list) + 1 else None,
                    matches=f"y{'' if i <= len(data_list) else len(data_list) + 1}"
                    if i != len(data_list) + 1
                    else None,
                    showticklabels=(i == len(data_list) + 1),
                )
                for i in range(2, 2 * len(data_list) + 1)
            },
            **{
                f"xaxis{i}": dict(matches="x" if i != len(data_list) + 1 else None)
                for i in range(2, 2 * len(data_list) + 1)
            },
        )
        .update_xaxes(showgrid=False)
        .update_yaxes(showgrid=False)
    )

    text_interval_years = 5
    text_interval_months = text_interval_years * 12

    max_value_cumulative = 0
    max_value_monthly = 0
    for i, data in enumerate(data_list, 1):
        # Get the y range
        total_payments = data[["principal_payment", "interest", "fee", "deposit", "stamp_duty"]].sum(axis=1)
        total_payments2 = data[["principal_payment", "interest", "fee"]].sum(axis=1)
        data_max_cumulative = total_payments.sum()
        max_value_cumulative = max(max_value_cumulative, data_max_cumulative)
        data_max_monthly = total_payments2.max()
        max_value_monthly = max(max_value_monthly, data_max_monthly)

        # Check whether some fields are present
        has_fees = (data["fee"] != 0).any()
        has_offset = (data["offset"] != 0).any()
        has_stamp_duty = (data["stamp_duty"] != 0).any()

        # Add the cumulative payment traces
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["deposit"].cumsum(),
                name="Deposit",
                stackgroup="cumulative",
                legendgroup="deposit",
                showlegend=i == 1,
                line=dict(color=COLOR_DEPOSIT),
                hovertemplate="$%{y:.3s}",
            ),
            row=1,
            col=i,
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["stamp_duty"].cumsum() if has_stamp_duty else [np.nan] * len(data),
                name="Stamp Duty",
                stackgroup="cumulative",
                legendgroup="deposit",
                showlegend=i == 1,
                line=dict(color=COLOR_STAMP_DUTY),
                hovertemplate="$%{y:.3s}",
            ),
            row=1,
            col=i,
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["interest"].cumsum(),
                name="Interest",
                stackgroup="cumulative",
                legendgroup="interest",
                showlegend=i == 1,
                line=dict(color=COLOR_INTEREST),
                hovertemplate="$%{y:.3s}",
            ),
            row=1,
            col=i,
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["fee"].cumsum() if has_fees else [np.nan] * len(data),
                name="Fees",
                stackgroup="cumulative",
                legendgroup="fees",
                showlegend=i == 1,
                line=dict(color=COLOR_FEE),
                hovertemplate="$%{y:.3s}",
            ),
            row=1,
            col=i,
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["principal_payment"].cumsum(),
                name="Principal Payment",
                stackgroup="cumulative",
                legendgroup="principal",
                showlegend=i == 1,
                line=dict(color=COLOR_PRINCIPAL),
                hovertemplate="$%{y:.3s}",
            ),
            row=1,
            col=i,
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["offset"].where(data["interest"] > 0, None).ffill() if has_offset else [np.nan] * len(data),
                name="Offset Balance",
                legendgroup="cumulative",
                showlegend=i == 1,
                line=dict(color=COLOR_OFFSET),
                hovertemplate="$%{y:.3s}",
            ),
            row=1,
            col=i,
        )
        fig.add_trace(
            go.Scatter(
                x=data.iloc[text_interval_months - 1 :: text_interval_months].index,
                y=total_payments.cumsum().iloc[text_interval_months - 1 :: text_interval_months],
                texttemplate="%{y:.3s}",
                showlegend=False,
                mode="text",
                textposition="top center",
                textfont=dict(size=12, color="#888"),
                hoverinfo="skip",
            ),
            row=1,
            col=i,
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=total_payments.cumsum(),
                name="Total",
                showlegend=False,
                line=dict(color="rgba(0,0,0,0)"),
                hovertemplate="$%{y:.3s}",
            ),
            row=1,
            col=i,
        )

        # Add the monthly payment traces
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["interest"],
                name="Interest",
                stackgroup="monthly",
                legendgroup="interest",
                showlegend=False,
                line=dict(color=COLOR_INTEREST),
                hovertemplate="$%{y:.3s}",
            ),
            row=2,
            col=i,
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["fee"] if has_fees else [np.nan] * len(data),
                name="Fees",
                stackgroup="monthly",
                legendgroup="fees",
                showlegend=False,
                line=dict(color=COLOR_FEE),
                hovertemplate="$%{y:.3s}",
            ),
            row=2,
            col=i,
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["principal_payment"],
                name="Principal Payment",
                stackgroup="monthly",
                legendgroup="principal",
                showlegend=False,
                line=dict(color=COLOR_PRINCIPAL),
                hovertemplate="$%{y:.3s}",
            ),
            row=2,
            col=i,
        )
        fig.add_trace(
            go.Scatter(
                x=data.iloc[text_interval_months - 1 :: text_interval_months].index,
                y=total_payments2.iloc[text_interval_months - 1 :: text_interval_months],
                texttemplate="%{y:.3s}",
                showlegend=False,
                mode="text",
                textposition="top center",
                textfont=dict(size=12, color="#888"),
                hoverinfo="skip",
            ),
            row=2,
            col=i,
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=total_payments2,
                name="Total",
                showlegend=False,
                line=dict(color="rgba(0,0,0,0)"),
                hovertemplate="$%{y:.3s}",
            ),
            row=2,
            col=i,
        )

    fig.update_layout(
        yaxis_range=[0, max_value_cumulative * 1.2],
        **{f"yaxis{len(data_list) + 1}": {"range": [0, max_value_monthly * 1.2]}},
    )
    fig.update_traces(
        line_width=1,
    )

    # Add the traces titles
    title_list = title_list or []
    for i, (title, feasible) in enumerate(zip(title_list, feasible_list), 1):
        if feasible:
            text = f"<b>{title}</b>"
        else:
            text = f"<b style='color: orangered;'>{title} (⚠ missing capital)</b>"

        fig.add_annotation(
            x=(i - 0.5) / len(data_list),
            xref="paper",
            xanchor="center",
            y=1.05,
            yref="paper",
            yanchor="bottom",
            text=text,
            showarrow=False,
        )

    return fig
