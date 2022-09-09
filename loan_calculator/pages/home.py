import pandas as pd
from dash import register_page, html, dcc, callback, clientside_callback, Input, State, Output, ALL, no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from loan_calculator import loan_modal

register_page(__name__, "/")

class ids:
    wrapper = "results_wrapper"
    loans = "loans_store"
    trigger = "dummy_trigger_btn"
    select = "loan_selection"


def layout():
    """Layout function"""
    return [
        dmc.MultiSelect(id=ids.select, maxSelectedValues=3, persistence=True),
        dmc.Space(h="md"),
        html.Div(
            dmc.Paper(
                dmc.Text(
                    "Start by adding a loan",
                    color="gray",
                    size="xl",
                ),
                style={
                    "height": "min(400px, calc(90vh - 200px))",
                    "display": "grid",
                    "placeContent": "center",
                },
                radius="md",
            ),
            id=ids.wrapper,
        ),
        dcc.Store(id=ids.loans, storage_type="local"),
        html.Button(style={"display": "none"}, id=ids.trigger),
    ]


clientside_callback(
    """function(n_clicks, loans) {
        const ctx = dash_clientside.callback_context
        if (ctx.triggered.length === 0) return dash_clientside.no_update
        const { name } = JSON.parse(ctx.triggered[0].prop_id.split(".")[0])
        const params = ctx.states_list[1].filter(s => s.id.name === name).map(s => [s.id.id, s.value])
        const booleans = ctx.states_list[2].filter(s => s.id.name === name).map(s => [s.id.id, s.value])
        const loan = Object.fromEntries(params.concat(booleans))
        console.log(loan)
        if (!loans) return {[loan.name]: loan}
        return {...loans, [loan.name]: loan}
    }""",
    Output(ids.loans, "data"),
    Input(loan_modal.ids.save(ALL), "n_clicks"),
    State(ids.loans, "data"),
    State(loan_modal.loan_param(ALL, ALL), "value"),
    State(loan_modal.loan_boolean(ALL, ALL), "checked"),
)


@callback(
    Output(ids.select, "data"),
    Input(ids.loans, "data"),
    Input(ids.trigger, "n_clicks"),
)
def compute_loan(loans_data, trigger):
    return [n for n in loans_data if n]


@callback(
    Output(ids.wrapper, "children"),
    Input(ids.select, "value"),
    State(ids.loans, "data"),
)
def compute_loan(loans_names, loans_data):
    if not loans_data or not loans_names:
        return no_update

    data_list = []
    title_list = []
    for name in loans_names:
        loan = loans_data[name]
        data = get_loan_data(loan)
        if data is not None:
            data_list.append(data)
            title_list.append(name)

    if not data_list:
        return no_update

    fig = make_figure(data_list, title_list)
    return dcc.Graph(
        figure=fig,
        responsive=True,
        config={"displayModeBar": False}
    )


def get_loan_data(loan):
    start_date = loan.get("start_date")
    property_value = loan.get("property_value")
    annual_rate = loan.get("annual_rate")
    borrowed_share = loan.get("borrowed_share")
    loan_duration_years = loan.get("loan_duration_years")
    start_capital = loan.get("start_capital")
    stamp_duty_rate = loan.get("stamp_duty_rate")
    monthly_income = loan.get("monthly_income")
    monthly_costs = loan.get("monthly_costs")
    with_offset_account = loan.get("with_offset_account")
    yearly_fees = loan.get("yearly_fees")

    if not all([
        property_value is not None,
        annual_rate is not None,
        borrowed_share is not None,
        loan_duration_years is not None,
        start_capital is not None,
        stamp_duty_rate is not None,
        monthly_income is not None,
        monthly_costs is not None,
        with_offset_account is not None,
        yearly_fees is not None,
    ]):
        return None

    date_period = pd.date_range(
        start_date,
        f"{pd.Timestamp(start_date).year + loan_duration_years}-{pd.Timestamp(start_date).strftime('%m-%d')}",
        freq="MS",
        inclusive="left",
    )
    principal = property_value * borrowed_share / 100
    start_offset = (start_capital - property_value * (100 - borrowed_share + stamp_duty_rate) / 100) * with_offset_account
    monthly_rate = annual_rate / 100 / 12
    monthly_fee = yearly_fees / 12

    data = pd.DataFrame(
        index=date_period,
        columns=["principal_paid", "offset", "principal_payment", "interest", "fee", "repayment"]
    ).rename_axis(index="date")

    for i, date in enumerate(date_period):
        if i == 0:
            offset = start_offset
            principal_paid = 0
        else:
            offset = data["offset"].iat[i - 1]
            principal_paid = data["principal_paid"].iat[i - 1]

        coef = (1 + monthly_rate) ** (loan_duration_years * 12)
        loan_payment = min(
            principal * monthly_rate * coef / (coef - 1),
            principal - principal_paid
        )

        if principal - offset - principal_paid <= 0:
            interest = 0
        else:
            interest = (principal - offset - principal_paid) * monthly_rate

        fee = monthly_fee if loan_payment > 0 else 0

        data.iloc[i] = [
            principal_paid + loan_payment - interest,
            offset + monthly_income - loan_payment - monthly_costs - fee
            if with_offset_account else 0,
            loan_payment - interest,
            interest,
            fee,
            loan_payment + fee,
        ]

    return data


def make_figure(data_list, title_list=None):
    if not isinstance(data_list, list):
        data_list = [data_list]

    fig = make_subplots(rows=2, cols=len(data_list), shared_xaxes=True, vertical_spacing=0.1, horizontal_spacing=0.02).update_layout(
        height=600,
        margin=dict(b=30, t=50, l=50, r=20, pad=8),
        yaxis_title="Cumulative Payments ($)",
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
        legend=dict(y=-0.05, yanchor="top", orientation="h", x=1, xanchor="right"),
        **{
            f"yaxis{i}": dict(
                title="Monthly Payments ($)" if i == len(data_list) + 1 else None,
                matches=f"y{'' if i <= len(data_list) else len(data_list) + 1}" if i != len(data_list) + 1 else None,
                showticklabels=True if i == len(data_list) + 1 else False,
            )
            for i in range(2, 2 * len(data_list) + 1)
        }
    ).update_xaxes(showgrid=False).update_yaxes(showgrid=False)
    color_fee = "orangered"
    color_interest = "pink"
    color_principal = "darkcyan"
    color_offset = "forestgreen"

    text_interval_years = 4
    text_interval_months = text_interval_years * 12

    max_value_cumulative = 0
    max_value_monthly = 0
    for i, data in enumerate(data_list, 1):
        total_payments = data[["principal_payment", "interest", "fee"]].sum(axis=1)
        data_max_cumulative = total_payments.sum()
        max_value_cumulative = max(max_value_cumulative, data_max_cumulative)
        data_max_monthly = total_payments.max()
        max_value_monthly = max(max_value_monthly, data_max_monthly)
        has_fees = (data["fee"] != 0).any()
        has_offset = (data["offset"] != 0).any()
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["interest"].cumsum(),
                name="Interest",
                stackgroup="cumulative",
                legendgroup="interest",
                showlegend=i == 1,
                line=dict(color=color_interest),
                hovertemplate="$%{y:.3s}",
            ),
            row=1,
            col=i
        )
        if has_fees:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["fee"].cumsum(),
                    name="Fees",
                    stackgroup="cumulative",
                    legendgroup="fees",
                    showlegend=i == 1,
                    line=dict(color=color_fee),
                    hovertemplate="$%{y:.3s}",
                ),
                row=1,
                col=i
            )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["principal_payment"].cumsum(),
                name="Principal Payment",
                stackgroup="cumulative",
                legendgroup="principal",
                showlegend=i == 1,
                line=dict(color=color_principal),
                hovertemplate="$%{y:.3s}",
            ),
            row=1,
            col=i
        )
        if has_offset:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["offset"].where(data["interest"] > 0, None).ffill(),
                    name="Offset Balance",
                    legendgroup="cumulative",
                    showlegend=i == 1,
                    line=dict(color=color_offset),
                    hovertemplate="$%{y:.3s}",
                ),
                row=1,
                col=i
            )
        fig.add_trace(
            go.Scatter(
                x=data.iloc[text_interval_months - 1::text_interval_months].index,
                y=total_payments.cumsum().iloc[text_interval_months - 1::text_interval_months],
                texttemplate="%{y:.3s}",
                showlegend=False,
                mode="text",
                textposition="top center",
                textfont=dict(size=12, color="#888"),
                hoverinfo="skip",
            ),
            row=1,
            col=i
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["interest"],
                name="Interest",
                stackgroup="monthly",
                legendgroup="interest",
                showlegend=False,
                line=dict(color=color_interest),
                hovertemplate="$%{y:.3s}",
            ),
            row=2,
            col=i
        )
        if has_fees:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["fee"],
                    name="Fees",
                    stackgroup="monthly",
                    legendgroup="fees",
                    showlegend=False,
                    line=dict(color=color_fee),
                    hovertemplate="$%{y:.3s}",
                ),
                row=2,
                col=i
            )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["principal_payment"],
                name="Principal Payment",
                stackgroup="monthly",
                legendgroup="principal",
                showlegend=False,
                line=dict(color=color_principal),
                hovertemplate="$%{y:.3s}",
            ),
            row=2,
            col=i
        )
        fig.add_trace(
            go.Scatter(
                x=data.iloc[text_interval_months - 1::text_interval_months].index,
                y=total_payments.iloc[text_interval_months - 1::text_interval_months],
                texttemplate="%{y:.3s}",
                showlegend=False,
                mode="text",
                textposition="top center",
                textfont=dict(size=12, color="#888"),
                hoverinfo="skip",
            ),
            row=2,
            col=i
        )

    fig.update_layout(
        yaxis_range=[0, max_value_cumulative * 1.2],
        **{f"yaxis{len(data_list) + 1}": {"range": [0, max_value_monthly * 1.2]}},
    )

    title_list = title_list or []
    for i, title in enumerate(title_list, 1):
        fig.add_annotation(
            x=(i - 0.5) / len(data_list),
            xref="paper",
            xanchor="center",
            y=1.05,
            yref="paper",
            yanchor="bottom",
            text=f"<b>{title}</b>",
            showarrow=False,
        )

    return fig