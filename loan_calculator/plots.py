from typing import List

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

COLOR_DEPOSIT = "rgb(240, 145, 23)"
COLOR_STAMP_DUTY = "rgb(240, 239, 35)"
COLOR_FEE = "rgb(240, 101, 149)"
COLOR_INTEREST = "rgb(132, 94, 247)"
COLOR_PRINCIPAL = "rgb(92, 124, 250)"
COLOR_OFFSET = "rgb(32, 201, 151)"


def make_comparison_figure(  # pylint: disable = too-many-locals
    data_list: List[pd.DataFrame], title_list: List[str] = None, feasible_list: List[bool] = None
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
