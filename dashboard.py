from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ai_analysis import get_ai_analysis
from backtesting import run_backtest
from indicators import add_indicators
from market import get_market_data
from news import get_company_news
from portfolio_risk import calculate_portfolio_risk
from portfolio_manager import generate_rebalance_plan
import inspect
import paper_trading as paper_trading_module

calculate_position_metrics = paper_trading_module.calculate_position_metrics
load_portfolio = paper_trading_module.load_portfolio
reset_portfolio = paper_trading_module.reset_portfolio


def buy_asset(
    ticker,
    quantity,
    price,
    **trade_metadata,
):
    """Call old or new paper-trading modules safely."""

    actual_function = paper_trading_module.buy_asset

    try:
        supported_parameters = inspect.signature(
            actual_function
        ).parameters

        accepted_metadata = {
            key: value
            for key, value in trade_metadata.items()
            if key in supported_parameters
        }

        return actual_function(
            ticker=ticker,
            quantity=quantity,
            price=price,
            **accepted_metadata,
        )

    except (TypeError, ValueError):
        return actual_function(
            ticker=ticker,
            quantity=quantity,
            price=price,
        )


def sell_asset(
    ticker,
    quantity,
    price,
    **trade_metadata,
):
    """Call old or new paper-trading modules safely."""

    actual_function = paper_trading_module.sell_asset

    try:
        supported_parameters = inspect.signature(
            actual_function
        ).parameters

        accepted_metadata = {
            key: value
            for key, value in trade_metadata.items()
            if key in supported_parameters
        }

        return actual_function(
            ticker=ticker,
            quantity=quantity,
            price=price,
            **accepted_metadata,
        )

    except (TypeError, ValueError):
        return actual_function(
            ticker=ticker,
            quantity=quantity,
            price=price,
        )
from scanner import scan_market
from strategy import generate_signal
from strategy_lab import StrategyParameters, compare_strategies
from strategy_optimizer import optimise_strategy
from watchlist import add_ticker, load_watchlist, remove_ticker, reset_watchlist
from price_alerts import (
    check_alerts,
    create_alert,
    delete_alert,
    load_alerts,
    set_alert_active,
)
from support_resistance import calculate_support_resistance
from trade_advisor import generate_trade_advice
from execution_risk_manager import (
    calculate_daily_realised_pnl,
    evaluate_buy_order,
)
from ui_theme import (
    apply_plotly_theme,
    inject_global_css,
    render_app_heading,
    render_sidebar_brand,
    render_sidebar_section,
    render_status_bar,
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="TAM Tradex",
    page_icon="📈",
    layout="wide",
)

apply_plotly_theme()
inject_global_css()


# ==================================================
# CONSTANTS
# ==================================================

STARTING_CASH = 10_000.00

ASSET_OPTIONS = {
    "Apple": "AAPL",
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
}

SCANNER_TICKERS = list(ASSET_OPTIONS.values())

if "current_page" not in st.session_state:
    st.session_state.current_page = "home"


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def safe_float(value) -> float:
    """
    Convert a pandas or Python numeric value into a float.
    """

    try:
        if hasattr(value, "item"):
            return float(value.item())

        return float(value)

    except (TypeError, ValueError):
        return 0.0


def format_currency(value: float) -> str:
    """
    Format a number using British pound currency.
    """

    return f"£{value:,.2f}"


def load_asset_data(ticker: str):
    """
    Download market data and add technical indicators.
    """

    data = get_market_data(ticker)

    if data is None or data.empty:
        return None

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.loc[:, ~data.columns.duplicated()]

    data = add_indicators(data)

    return data


def get_latest_price(data) -> float:
    """
    Extract the latest closing price.
    """

    return safe_float(
        data["Close"].iloc[-1]
    )


def display_signal(signal: str) -> None:
    """
    Display a colour-coded trading signal.
    """

    if signal == "BUY":
        st.success(f"Signal: {signal}")

    elif signal == "SELL":
        st.error(f"Signal: {signal}")

    else:
        st.warning(f"Signal: {signal}")


# ==================================================
# MAIN HEADER
# ==================================================

# render_app_heading()


# ==================================================
# SIDEBAR
# ==================================================

#render_sidebar_brand()
render_sidebar_section("Market Workspace")

asset_names = list(ASSET_OPTIONS.keys())

selected_asset_override = st.session_state.pop(
    "selected_asset_override",
    None,
)

if selected_asset_override in asset_names:
    selected_asset_index = asset_names.index(
        selected_asset_override
    )
else:
    selected_asset_index = 0

selected_asset = st.sidebar.selectbox(
    "Active market",
    options=asset_names,
    index=selected_asset_index,
)

ticker = ASSET_OPTIONS[selected_asset]

render_sidebar_section("Navigation")

navigation_items = [
    ("🏠  Dashboard", "home"),
    ("📈  Asset Analysis", "analysis"),
    ("🔎  Market Scanner", "scanner"),
    ("💼  Portfolio", "portfolio"),
    ("📊  Portfolio Analytics", "portfolio_analytics"),
    ("🧠  AI Portfolio Manager", "portfolio_manager"),
    ("⭐  Watchlist & Alerts", "watchlist"),
    ("📓  Trading Journal", "journal"),
    ("🧪  Strategy Lab", "strategy_lab"),
    ("⏱️  Backtesting", "backtest"),
]

for navigation_label, navigation_page in navigation_items:

    if st.sidebar.button(
        navigation_label,
        use_container_width=True,
        key=f"sidebar_navigation_{navigation_page}",
    ):
        st.session_state.current_page = navigation_page
        st.rerun()

render_sidebar_section("Account Snapshot")

portfolio_sidebar = load_portfolio()

sidebar_cash = safe_float(
    portfolio_sidebar.get("cash", 0.0)
)

sidebar_realised_pnl = safe_float(
    portfolio_sidebar.get(
        "realised_pnl",
        0.0,
    )
)

st.sidebar.metric(
    "Available Cash",
    format_currency(sidebar_cash),
)

st.sidebar.metric(
    "Realised P/L",
    format_currency(sidebar_realised_pnl),
)

st.sidebar.caption(
    "Educational research and simulated execution only. "
    "No live brokerage orders are submitted."
)


# ==================================================
# MARKET SCANNER SCREEN
# ==================================================

if st.session_state.current_page == "scanner":

    st.header("Market Scanner")

    st.write(
        "Compare prices, moving averages, RSI and technical signals "
        "across the TAM Tradex watchlist."
    )

    with st.spinner("Scanning the market..."):

        try:
            scanner_results = scan_market(
                SCANNER_TICKERS
            )

        except Exception as error:
            scanner_results = []

            st.error(
                f"Market scanner error: {error}"
            )

    if scanner_results:

        scanner_dataframe = pd.DataFrame(
            scanner_results
        )

        st.dataframe(
            scanner_dataframe,
            use_container_width=True,
            hide_index=True,
        )

        if "Signal" in scanner_dataframe.columns:

            buy_count = int(
                (
                    scanner_dataframe["Signal"]
                    == "BUY"
                ).sum()
            )

            sell_count = int(
                (
                    scanner_dataframe["Signal"]
                    == "SELL"
                ).sum()
            )

            hold_count = int(
                (
                    scanner_dataframe["Signal"]
                    == "HOLD"
                ).sum()
            )

            metric1, metric2, metric3 = st.columns(3)

            metric1.metric(
                "Buy Signals",
                buy_count,
            )

            metric2.metric(
                "Sell Signals",
                sell_count,
            )

            metric3.metric(
                "Hold Signals",
                hold_count,
            )

    else:

        st.warning(
            "No scanner results were returned. "
            "Check your internet connection and market-data module."
        )


# ==================================================
# PORTFOLIO SCREEN
# ==================================================

elif st.session_state.current_page == "portfolio":

    st.header("Paper-Trading Portfolio")

    portfolio = load_portfolio()

    positions = portfolio.get(
        "positions",
        {},
    )

    total_market_value = 0.0
    total_unrealised_pnl = 0.0

    position_rows = []

    if positions:

        with st.spinner(
            "Updating live portfolio prices..."
        ):

            for (
                position_ticker,
                position,
            ) in positions.items():

                try:
                    position_data = load_asset_data(
                        position_ticker
                    )

                    if (
                        position_data is None
                        or position_data.empty
                    ):
                        st.warning(
                            f"No market data was returned "
                            f"for {position_ticker}."
                        )
                        continue

                    current_price = get_latest_price(
                        position_data
                    )

                    quantity = safe_float(
                        position.get(
                            "quantity",
                            0.0,
                        )
                    )

                    average_price = safe_float(
                        position.get(
                            "average_price",
                            0.0,
                        )
                    )

                    market_value = (
                        quantity
                        * current_price
                    )

                    cost_basis = (
                        quantity
                        * average_price
                    )

                    unrealised_pnl = (
                        market_value
                        - cost_basis
                    )

                    if cost_basis > 0:

                        return_percentage = (
                            unrealised_pnl
                            / cost_basis
                        ) * 100

                    else:

                        return_percentage = 0.0

                    total_market_value += (
                        market_value
                    )

                    total_unrealised_pnl += (
                        unrealised_pnl
                    )

                    position_rows.append(
                        {
                            "Ticker": position_ticker,
                            "Quantity": round(
                                quantity,
                                4,
                            ),
                            "Average Entry": round(
                                average_price,
                                2,
                            ),
                            "Current Price": round(
                                current_price,
                                2,
                            ),
                            "Cost Basis": round(
                                cost_basis,
                                2,
                            ),
                            "Market Value": round(
                                market_value,
                                2,
                            ),
                            "Unrealised P/L": round(
                                unrealised_pnl,
                                2,
                            ),
                            "Return %": round(
                                return_percentage,
                                2,
                            ),
                        }
                    )

                except Exception as error:

                    st.warning(
                        f"Could not update "
                        f"{position_ticker}: {error}"
                    )

    cash = safe_float(
        portfolio.get(
            "cash",
            0.0,
        )
    )

    realised_pnl = safe_float(
        portfolio.get(
            "realised_pnl",
            0.0,
        )
    )

    total_account_value = (
        cash
        + total_market_value
    )

    total_return_value = (
        total_account_value
        - STARTING_CASH
    )

    total_return_percentage = (
        (
            total_return_value
            / STARTING_CASH
        )
        * 100
        if STARTING_CASH > 0
        else 0.0
    )

    (
        metric1,
        metric2,
        metric3,
        metric4,
        metric5,
    ) = st.columns(5)

    metric1.metric(
        "Account Value",
        format_currency(
            total_account_value
        ),
    )

    metric2.metric(
        "Available Cash",
        format_currency(cash),
    )

    metric3.metric(
        "Market Value",
        format_currency(
            total_market_value
        ),
    )

    metric4.metric(
        "Unrealised P/L",
        format_currency(
            total_unrealised_pnl
        ),
    )

    metric5.metric(
        "Total Return",
        f"{total_return_percentage:.2f}%",
        delta=format_currency(
            total_return_value
        ),
    )

    st.divider()

    st.subheader("Open Positions")

    if position_rows:

        positions_dataframe = pd.DataFrame(
            position_rows
        )

        st.dataframe(
            positions_dataframe,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Your paper-trading portfolio "
            "does not contain any open positions."
        )

    st.subheader("Trade History")

    trade_history = portfolio.get(
        "trade_history",
        [],
    )

    if trade_history:

        trade_history_dataframe = pd.DataFrame(
            trade_history
        )

        trade_history_dataframe = (
            trade_history_dataframe.iloc[::-1]
        )

        st.dataframe(
            trade_history_dataframe,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No paper trades have been recorded yet."
        )

    st.divider()

    with st.expander(
        "Reset Paper-Trading Account"
    ):

        st.warning(
            "This will delete all simulated positions, "
            "trade history and performance data. "
            "The account will return to £10,000 cash."
        )

        confirm_reset = st.checkbox(
            "I understand that this action cannot be undone.",
            key="confirm_portfolio_reset",
        )

        reset_button = st.button(
            "Reset Account",
            type="primary",
            disabled=not confirm_reset,
            use_container_width=True,
        )

        if reset_button:

            reset_portfolio()

            st.success(
                "The paper-trading account "
                "was reset successfully."
            )

            st.rerun()




# ==================================================
# PORTFOLIO ANALYTICS SCREEN
# ==================================================

elif st.session_state.current_page == "portfolio_analytics":

    st.header("Portfolio Analytics")

    st.write(
        "Evaluate capital allocation, concentration, open-position returns "
        "and current paper-portfolio risk."
    )

    analytics_portfolio = load_portfolio()
    analytics_positions = analytics_portfolio.get("positions", {})
    analytics_cash = safe_float(analytics_portfolio.get("cash", 0.0))
    analytics_realised_pnl = safe_float(
        analytics_portfolio.get("realised_pnl", 0.0)
    )

    analytics_rows = []
    analytics_market_value = 0.0
    analytics_cost_basis = 0.0
    analytics_unrealised_pnl = 0.0

    if analytics_positions:

        with st.spinner("Updating portfolio analytics with current prices..."):

            for analytics_ticker, analytics_position in analytics_positions.items():

                try:
                    analytics_data = load_asset_data(analytics_ticker)

                    if analytics_data is None or analytics_data.empty:
                        st.warning(
                            f"No current market data was returned for "
                            f"{analytics_ticker}."
                        )
                        continue

                    analytics_current_price = get_latest_price(analytics_data)
                    analytics_quantity = safe_float(
                        analytics_position.get("quantity", 0.0)
                    )
                    analytics_average_price = safe_float(
                        analytics_position.get("average_price", 0.0)
                    )

                    position_market_value = (
                        analytics_quantity * analytics_current_price
                    )
                    position_cost_basis = (
                        analytics_quantity * analytics_average_price
                    )
                    position_unrealised_pnl = (
                        position_market_value - position_cost_basis
                    )
                    position_return_percentage = (
                        position_unrealised_pnl / position_cost_basis * 100
                        if position_cost_basis > 0
                        else 0.0
                    )

                    analytics_market_value += position_market_value
                    analytics_cost_basis += position_cost_basis
                    analytics_unrealised_pnl += position_unrealised_pnl

                    analytics_rows.append(
                        {
                            "Ticker": analytics_ticker,
                            "Quantity": analytics_quantity,
                            "Average Entry": analytics_average_price,
                            "Current Price": analytics_current_price,
                            "Cost Basis": position_cost_basis,
                            "Market Value": position_market_value,
                            "Unrealised P/L": position_unrealised_pnl,
                            "Return %": position_return_percentage,
                        }
                    )

                except Exception as error:
                    st.warning(
                        f"Could not calculate analytics for "
                        f"{analytics_ticker}: {error}"
                    )

    analytics_account_value = analytics_cash + analytics_market_value
    analytics_total_pnl = (
        analytics_account_value - STARTING_CASH
    )
    analytics_total_return = (
        analytics_total_pnl / STARTING_CASH * 100
        if STARTING_CASH > 0
        else 0.0
    )
    analytics_invested_percentage = (
        analytics_market_value / analytics_account_value * 100
        if analytics_account_value > 0
        else 0.0
    )
    analytics_cash_percentage = (
        analytics_cash / analytics_account_value * 100
        if analytics_account_value > 0
        else 0.0
    )

    if analytics_rows:
        analytics_dataframe = pd.DataFrame(analytics_rows)
        analytics_dataframe["Allocation %"] = (
            analytics_dataframe["Market Value"]
            / analytics_market_value
            * 100
            if analytics_market_value > 0
            else 0.0
        )
        largest_position_percentage = safe_float(
            analytics_dataframe["Allocation %"].max()
        )
        winning_positions = int(
            (analytics_dataframe["Unrealised P/L"] > 0).sum()
        )
        losing_positions = int(
            (analytics_dataframe["Unrealised P/L"] < 0).sum()
        )
    else:
        analytics_dataframe = pd.DataFrame()
        largest_position_percentage = 0.0
        winning_positions = 0
        losing_positions = 0

    portfolio_risk_result = calculate_portfolio_risk(
        analytics_dataframe,
        cash_percentage=analytics_cash_percentage,
    )

    metric_row1 = st.columns(5)

    metric_row1[0].metric(
        "Account Value",
        format_currency(analytics_account_value),
        delta=format_currency(analytics_total_pnl),
    )
    metric_row1[1].metric(
        "Total Return",
        f"{analytics_total_return:.2f}%",
    )
    metric_row1[2].metric(
        "Invested Capital",
        format_currency(analytics_market_value),
        delta=f"{analytics_invested_percentage:.1f}% deployed",
    )
    metric_row1[3].metric(
        "Available Cash",
        format_currency(analytics_cash),
        delta=f"{analytics_cash_percentage:.1f}% cash",
    )
    metric_row1[4].metric(
        "Open Positions",
        len(analytics_rows),
    )

    metric_row2 = st.columns(5)

    metric_row2[0].metric(
        "Unrealised P/L",
        format_currency(analytics_unrealised_pnl),
    )
    metric_row2[1].metric(
        "Realised P/L",
        format_currency(analytics_realised_pnl),
    )
    metric_row2[2].metric(
        "Winning Positions",
        winning_positions,
    )
    metric_row2[3].metric(
        "Losing Positions",
        losing_positions,
    )
    metric_row2[4].metric(
        "Largest Allocation",
        f"{largest_position_percentage:.1f}%",
    )

    st.divider()

    if analytics_dataframe.empty:

        st.info(
            "No open positions are available for portfolio analysis. "
            "Place a simulated buy order first."
        )

    else:

        chart_column1, chart_column2 = st.columns(2)

        with chart_column1:

            st.subheader("Capital Allocation")

            allocation_chart = go.Figure(
                data=[
                    go.Pie(
                        labels=analytics_dataframe["Ticker"],
                        values=analytics_dataframe["Market Value"],
                        hole=0.55,
                        textinfo="label+percent",
                        hovertemplate=(
                            "%{label}<br>"
                            "Market value: £%{value:,.2f}<br>"
                            "Allocation: %{percent}"
                            "<extra></extra>"
                        ),
                    )
                ]
            )

            allocation_chart.update_layout(
                height=470,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=True,
            )

            st.plotly_chart(
                allocation_chart,
                use_container_width=True,
            )

        with chart_column2:

            st.subheader("Unrealised Profit and Loss")

            pnl_chart_data = analytics_dataframe.sort_values(
                "Unrealised P/L",
                ascending=True,
            )

            pnl_chart = go.Figure()

            pnl_chart.add_trace(
                go.Bar(
                    x=pnl_chart_data["Unrealised P/L"],
                    y=pnl_chart_data["Ticker"],
                    orientation="h",
                    text=pnl_chart_data["Unrealised P/L"].map(
                        lambda value: f"£{value:,.2f}"
                    ),
                    textposition="auto",
                    hovertemplate=(
                        "%{y}<br>"
                        "Unrealised P/L: £%{x:,.2f}"
                        "<extra></extra>"
                    ),
                )
            )

            pnl_chart.update_layout(
                height=470,
                xaxis_title="Unrealised P/L (£)",
                yaxis_title="",
                margin=dict(l=20, r=20, t=20, b=20),
            )

            st.plotly_chart(
                pnl_chart,
                use_container_width=True,
            )

        st.subheader("Position Return Comparison")

        return_chart_data = analytics_dataframe.sort_values(
            "Return %",
            ascending=False,
        )

        return_chart = go.Figure()

        return_chart.add_trace(
            go.Bar(
                x=return_chart_data["Ticker"],
                y=return_chart_data["Return %"],
                text=return_chart_data["Return %"].map(
                    lambda value: f"{value:.2f}%"
                ),
                textposition="auto",
                hovertemplate=(
                    "%{x}<br>"
                    "Position return: %{y:.2f}%"
                    "<extra></extra>"
                ),
            )
        )

        return_chart.update_layout(
            height=420,
            xaxis_title="Ticker",
            yaxis_title="Return (%)",
            margin=dict(l=20, r=20, t=20, b=20),
        )

        st.plotly_chart(
            return_chart,
            use_container_width=True,
        )

        st.subheader("Portfolio Risk Score")

        risk_score = safe_float(
            portfolio_risk_result.get("risk_score", 0.0)
        )
        portfolio_health_score = safe_float(
            portfolio_risk_result.get(
                "portfolio_health_score",
                0.0,
            )
        )
        diversification_score = safe_float(
            portfolio_risk_result.get(
                "diversification_score",
                0.0,
            )
        )
        concentration_score = safe_float(
            portfolio_risk_result.get(
                "concentration_score",
                0.0,
            )
        )
        effective_positions = safe_float(
            portfolio_risk_result.get(
                "effective_positions",
                0.0,
            )
        )
        top_three_percentage = safe_float(
            portfolio_risk_result.get(
                "top_three_percentage",
                0.0,
            )
        )
        risk_level = portfolio_risk_result.get(
            "risk_level",
            "Unavailable",
        )

        risk_metric_columns = st.columns(5)

        risk_metric_columns[0].metric(
            "Portfolio Risk",
            f"{risk_score:.1f}/100",
            delta=risk_level,
            delta_color="inverse",
        )

        risk_metric_columns[1].metric(
            "Portfolio Health",
            f"{portfolio_health_score:.1f}/100",
        )

        risk_metric_columns[2].metric(
            "Diversification",
            f"{diversification_score:.1f}/100",
        )

        risk_metric_columns[3].metric(
            "Effective Positions",
            f"{effective_positions:.2f}",
        )

        risk_metric_columns[4].metric(
            "Top 3 Allocation",
            f"{top_three_percentage:.1f}%",
        )

        risk_gauge_column, diversification_gauge_column = st.columns(2)

        with risk_gauge_column:

            risk_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=risk_score,
                    number={"suffix": "/100"},
                    title={"text": f"Risk Level: {risk_level}"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"thickness": 0.28},
                        "steps": [
                            {"range": [0, 25]},
                            {"range": [25, 45]},
                            {"range": [45, 70]},
                            {"range": [70, 100]},
                        ],
                        "threshold": {
                            "line": {"width": 4},
                            "thickness": 0.8,
                            "value": risk_score,
                        },
                    },
                )
            )

            risk_gauge.update_layout(
                height=320,
                margin=dict(l=20, r=20, t=50, b=20),
            )

            st.plotly_chart(
                risk_gauge,
                use_container_width=True,
            )

        with diversification_gauge_column:

            diversification_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=diversification_score,
                    number={"suffix": "/100"},
                    title={"text": "Diversification Score"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"thickness": 0.28},
                        "steps": [
                            {"range": [0, 25]},
                            {"range": [25, 50]},
                            {"range": [50, 75]},
                            {"range": [75, 100]},
                        ],
                        "threshold": {
                            "line": {"width": 4},
                            "thickness": 0.8,
                            "value": diversification_score,
                        },
                    },
                )
            )

            diversification_gauge.update_layout(
                height=320,
                margin=dict(l=20, r=20, t=50, b=20),
            )

            st.plotly_chart(
                diversification_gauge,
                use_container_width=True,
            )

        score_component_dataframe = pd.DataFrame(
            {
                "Component": [
                    "Concentration",
                    "Cash Reserve",
                    "Performance Balance",
                ],
                "Score": [
                    concentration_score,
                    safe_float(
                        portfolio_risk_result.get(
                            "cash_score",
                            0.0,
                        )
                    ),
                    safe_float(
                        portfolio_risk_result.get(
                            "performance_balance_score",
                            0.0,
                        )
                    ),
                ],
            }
        )

        component_chart = go.Figure()

        component_chart.add_trace(
            go.Bar(
                x=score_component_dataframe["Component"],
                y=score_component_dataframe["Score"],
                text=score_component_dataframe["Score"].map(
                    lambda value: f"{value:.1f}"
                ),
                textposition="auto",
                hovertemplate=(
                    "%{x}<br>"
                    "Score: %{y:.1f}/100"
                    "<extra></extra>"
                ),
            )
        )

        component_chart.update_layout(
            title="Portfolio Health Components",
            height=380,
            yaxis_title="Score",
            yaxis_range=[0, 100],
            margin=dict(l=20, r=20, t=60, b=20),
        )

        st.plotly_chart(
            component_chart,
            use_container_width=True,
        )

        with st.expander(
            "How the Portfolio Risk Score is calculated"
        ):

            st.write(
                "The score is a heuristic assessment based on allocation "
                "concentration, effective position count, cash reserves and "
                "the balance of winning versus losing open positions."
            )

            st.write(
                f"**Herfindahl concentration index:** "
                f"{safe_float(portfolio_risk_result.get('herfindahl_index', 0.0)):.4f}"
            )

            st.write(
                f"**Largest position:** "
                f"{safe_float(portfolio_risk_result.get('largest_position_percentage', 0.0)):.1f}%"
            )

            for risk_message in portfolio_risk_result.get(
                "messages",
                [],
            ):
                st.write(f"- {risk_message}")

            st.caption(
                "This score is an educational portfolio-health indicator. "
                "It does not estimate regulatory capital, value at risk or "
                "future investment losses."
            )

        st.subheader("Risk Diagnostics")

        risk_messages = []

        if largest_position_percentage >= 50:
            risk_messages.append(
                (
                    "error",
                    f"High concentration: the largest position represents "
                    f"{largest_position_percentage:.1f}% of invested capital."
                )
            )
        elif largest_position_percentage >= 35:
            risk_messages.append(
                (
                    "warning",
                    f"Moderate concentration: the largest position represents "
                    f"{largest_position_percentage:.1f}% of invested capital."
                )
            )
        else:
            risk_messages.append(
                (
                    "success",
                    f"Position concentration is controlled. The largest "
                    f"allocation is {largest_position_percentage:.1f}%."
                )
            )

        if analytics_cash_percentage < 10:
            risk_messages.append(
                (
                    "warning",
                    f"Low cash reserve: only {analytics_cash_percentage:.1f}% "
                    f"of account value remains available."
                )
            )
        elif analytics_cash_percentage > 60:
            risk_messages.append(
                (
                    "info",
                    f"Capital deployment is conservative: "
                    f"{analytics_cash_percentage:.1f}% remains in cash."
                )
            )
        else:
            risk_messages.append(
                (
                    "success",
                    f"Cash reserve is balanced at "
                    f"{analytics_cash_percentage:.1f}%."
                )
            )

        if losing_positions > winning_positions:
            risk_messages.append(
                (
                    "warning",
                    f"More open positions are currently losing "
                    f"({losing_positions}) than winning ({winning_positions})."
                )
            )
        else:
            risk_messages.append(
                (
                    "success",
                    f"Winning open positions ({winning_positions}) are at least "
                    f"equal to losing positions ({losing_positions})."
                )
            )

        for message_type, message_text in risk_messages:
            if message_type == "error":
                st.error(message_text)
            elif message_type == "warning":
                st.warning(message_text)
            elif message_type == "success":
                st.success(message_text)
            else:
                st.info(message_text)

        st.subheader("Position Detail")

        analytics_display = analytics_dataframe.copy()

        numeric_columns = [
            "Quantity",
            "Average Entry",
            "Current Price",
            "Cost Basis",
            "Market Value",
            "Unrealised P/L",
            "Return %",
            "Allocation %",
        ]

        for numeric_column in numeric_columns:
            if numeric_column in analytics_display.columns:
                analytics_display[numeric_column] = pd.to_numeric(
                    analytics_display[numeric_column],
                    errors="coerce",
                )

        analytics_display = analytics_display.sort_values(
            "Market Value",
            ascending=False,
        )

        st.dataframe(
            analytics_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Quantity": st.column_config.NumberColumn(format="%.4f"),
                "Average Entry": st.column_config.NumberColumn(format="£%.2f"),
                "Current Price": st.column_config.NumberColumn(format="£%.2f"),
                "Cost Basis": st.column_config.NumberColumn(format="£%.2f"),
                "Market Value": st.column_config.NumberColumn(format="£%.2f"),
                "Unrealised P/L": st.column_config.NumberColumn(format="£%.2f"),
                "Return %": st.column_config.NumberColumn(format="%.2f%%"),
                "Allocation %": st.column_config.ProgressColumn(
                    min_value=0,
                    max_value=100,
                    format="%.1f%%",
                ),
            },
        )

        analytics_csv = analytics_display.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Portfolio Analytics CSV",
            data=analytics_csv,
            file_name="tam_tradex_portfolio_analytics.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.caption(
        "Portfolio analytics use current downloaded market prices. "
        "Figures exclude brokerage fees, taxes, spreads and slippage."
    )


# ==================================================
# AI PORTFOLIO MANAGER SCREEN
# ==================================================

elif st.session_state.current_page == "portfolio_manager":

    st.header("AI Portfolio Manager")

    st.write(
        "Generate a structured rebalancing plan using current paper-portfolio "
        "values, position concentration, cash reserves and your selected "
        "risk profile."
    )

    manager_portfolio = load_portfolio()
    manager_positions = manager_portfolio.get(
        "positions",
        {},
    )
    manager_cash = safe_float(
        manager_portfolio.get(
            "cash",
            0.0,
        )
    )

    manager_rows = []
    manager_market_value = 0.0

    if manager_positions:

        with st.spinner(
            "Updating portfolio positions for the rebalancing model..."
        ):

            for manager_ticker, manager_position in manager_positions.items():

                try:

                    manager_data = load_asset_data(
                        manager_ticker
                    )

                    if manager_data is None or manager_data.empty:
                        st.warning(
                            f"No current data was returned for "
                            f"{manager_ticker}."
                        )
                        continue

                    manager_current_price = get_latest_price(
                        manager_data
                    )

                    manager_quantity = safe_float(
                        manager_position.get(
                            "quantity",
                            0.0,
                        )
                    )

                    manager_average_price = safe_float(
                        manager_position.get(
                            "average_price",
                            0.0,
                        )
                    )

                    manager_position_value = (
                        manager_quantity
                        * manager_current_price
                    )

                    manager_cost_basis = (
                        manager_quantity
                        * manager_average_price
                    )

                    manager_unrealised_pnl = (
                        manager_position_value
                        - manager_cost_basis
                    )

                    manager_market_value += (
                        manager_position_value
                    )

                    manager_rows.append(
                        {
                            "Ticker": manager_ticker,
                            "Quantity": manager_quantity,
                            "Average Entry": manager_average_price,
                            "Current Price": manager_current_price,
                            "Market Value": manager_position_value,
                            "Unrealised P/L": manager_unrealised_pnl,
                        }
                    )

                except Exception as error:

                    st.warning(
                        f"Could not update {manager_ticker}: {error}"
                    )

    manager_account_value = (
        manager_cash
        + manager_market_value
    )

    manager_profile = st.selectbox(
        "Portfolio Risk Profile",
        options=[
            "Conservative",
            "Balanced",
            "Aggressive",
        ],
        index=1,
        key="portfolio_manager_risk_profile",
    )

    if manager_rows:

        manager_dataframe = pd.DataFrame(
            manager_rows
        )

        manager_dataframe["Allocation %"] = (
            manager_dataframe["Market Value"]
            / manager_market_value
            * 100
            if manager_market_value > 0
            else 0.0
        )

    else:

        manager_dataframe = pd.DataFrame()

    try:

        manager_plan = generate_rebalance_plan(
            manager_dataframe,
            cash=manager_cash,
            account_value=manager_account_value,
            risk_profile=manager_profile,
        )

    except Exception as error:

        st.error(
            f"Portfolio-manager error: {error}"
        )

        manager_plan = {
            "rows": [],
            "summary": {},
            "messages": [],
        }

    manager_summary = manager_plan.get(
        "summary",
        {},
    )

    manager_metric_columns = st.columns(6)

    manager_metric_columns[0].metric(
        "Account Value",
        format_currency(
            manager_account_value
        ),
    )

    manager_metric_columns[1].metric(
        "Current Cash",
        format_currency(
            manager_cash
        ),
        delta=(
            f"{safe_float(manager_plan.get('current_cash_percentage', 0.0)):.1f}%"
        ),
    )

    manager_metric_columns[2].metric(
        "Target Cash",
        format_currency(
            safe_float(
                manager_plan.get(
                    "target_cash_value",
                    0.0,
                )
            )
        ),
        delta=(
            f"{safe_float(manager_plan.get('target_cash_percentage', 0.0)):.1f}%"
        ),
    )

    manager_metric_columns[3].metric(
        "Suggested Buys",
        format_currency(
            safe_float(
                manager_summary.get(
                    "buy_value",
                    0.0,
                )
            )
        ),
    )

    manager_metric_columns[4].metric(
        "Suggested Sells",
        format_currency(
            safe_float(
                manager_summary.get(
                    "sell_value",
                    0.0,
                )
            )
        ),
    )

    manager_metric_columns[5].metric(
        "Positions Reviewed",
        len(
            manager_plan.get(
                "rows",
                [],
            )
        ),
    )

    st.divider()

    if not manager_plan.get("rows"):

        st.info(
            "No open positions are available. Buy an asset in the "
            "paper-trading workspace before generating a rebalance plan."
        )

    else:

        manager_action_columns = st.columns(4)

        manager_action_columns[0].metric(
            "BUY",
            int(
                manager_summary.get(
                    "buy_count",
                    0,
                )
            ),
        )

        manager_action_columns[1].metric(
            "SELL",
            int(
                manager_summary.get(
                    "sell_count",
                    0,
                )
            ),
        )

        manager_action_columns[2].metric(
            "HOLD",
            int(
                manager_summary.get(
                    "hold_count",
                    0,
                )
            ),
        )

        manager_action_columns[3].metric(
            "REVIEW",
            int(
                manager_summary.get(
                    "review_count",
                    0,
                )
            ),
        )

        manager_plan_dataframe = pd.DataFrame(
            manager_plan["rows"]
        )

        st.subheader("Recommended Rebalancing Actions")

        st.dataframe(
            manager_plan_dataframe[
                [
                    "Ticker",
                    "Action",
                    "Current Allocation %",
                    "Target Allocation %",
                    "Allocation Gap %",
                    "Current Value",
                    "Target Value",
                    "Suggested Value Change",
                    "Suggested Quantity Change",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Current Allocation %": st.column_config.ProgressColumn(
                    min_value=0,
                    max_value=100,
                    format="%.1f%%",
                ),
                "Target Allocation %": st.column_config.NumberColumn(
                    format="%.1f%%"
                ),
                "Allocation Gap %": st.column_config.NumberColumn(
                    format="%+.1f%%"
                ),
                "Current Value": st.column_config.NumberColumn(
                    format="£%.2f"
                ),
                "Target Value": st.column_config.NumberColumn(
                    format="£%.2f"
                ),
                "Suggested Value Change": st.column_config.NumberColumn(
                    format="%+.2f"
                ),
                "Suggested Quantity Change": st.column_config.NumberColumn(
                    format="%+.4f"
                ),
            },
        )

        st.subheader("Current vs Target Allocation")

        allocation_comparison_chart = go.Figure()

        allocation_comparison_chart.add_trace(
            go.Bar(
                x=manager_plan_dataframe["Ticker"],
                y=manager_plan_dataframe[
                    "Current Allocation %"
                ],
                name="Current Allocation",
                hovertemplate=(
                    "%{x}<br>"
                    "Current: %{y:.1f}%"
                    "<extra></extra>"
                ),
            )
        )

        allocation_comparison_chart.add_trace(
            go.Bar(
                x=manager_plan_dataframe["Ticker"],
                y=manager_plan_dataframe[
                    "Target Allocation %"
                ],
                name="Target Allocation",
                hovertemplate=(
                    "%{x}<br>"
                    "Target: %{y:.1f}%"
                    "<extra></extra>"
                ),
            )
        )

        allocation_comparison_chart.update_layout(
            barmode="group",
            height=440,
            xaxis_title="Ticker",
            yaxis_title="Allocation (%)",
            margin=dict(
                l=20,
                r=20,
                t=30,
                b=20,
            ),
        )

        st.plotly_chart(
            allocation_comparison_chart,
            use_container_width=True,
        )

        st.subheader("Action Rationale")

        for _, manager_action_row in manager_plan_dataframe.iterrows():

            action = str(
                manager_action_row["Action"]
            )

            message = (
                f"**{manager_action_row['Ticker']} — {action}:** "
                f"{manager_action_row['Rationale']}"
            )

            if action == "BUY":
                st.success(message)
            elif action in ["SELL", "REVIEW"]:
                st.warning(message)
            else:
                st.info(message)

        with st.expander(
            "Portfolio Manager Assumptions",
            expanded=True,
        ):

            st.write(
                f"**Risk profile:** {manager_profile}"
            )

            st.write(
                f"**Target cash reserve:** "
                f"{safe_float(manager_plan.get('target_cash_percentage', 0.0)):.1f}%"
            )

            st.write(
                f"**Maximum target allocation per position:** "
                f"{safe_float(manager_plan.get('maximum_position_percentage', 0.0)):.1f}%"
            )

            st.write(
                f"**Rebalancing threshold:** "
                f"{safe_float(manager_plan.get('rebalance_threshold_percentage', 0.0)):.1f} percentage points"
            )

            for manager_message in manager_plan.get(
                "messages",
                [],
            ):
                st.write(
                    f"- {manager_message}"
                )

            st.caption(
                "The model equally weights invested capital across existing "
                "positions, subject to cash and concentration limits. It does "
                "not consider taxes, transaction costs, correlations, sector "
                "exposure or personalised investment objectives."
            )

        manager_csv = manager_plan_dataframe.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download Rebalancing Plan CSV",
            data=manager_csv,
            file_name="tam_tradex_rebalancing_plan.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.warning(
        "The AI Portfolio Manager is an educational simulation. "
        "Its outputs are not personalised financial advice."
    )


# ==================================================
# TRADING JOURNAL SCREEN
# ==================================================

elif st.session_state.current_page == "journal":

    st.header("Professional Trading Journal")

    st.write(
        "Review completed trades, evaluate decision quality and measure "
        "paper-trading performance."
    )

    st.markdown(
        """
        <style>
        .journal-summary-card {
            background: linear-gradient(145deg, rgba(31, 41, 55, 0.92), rgba(17, 24, 39, 0.92));
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 16px;
            padding: 18px 20px;
            margin-bottom: 10px;
        }
        .journal-summary-label {
            color: #94a3b8;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 6px;
        }
        .journal-summary-value {
            color: #f8fafc;
            font-size: 1.55rem;
            font-weight: 700;
        }
        .trade-card {
            background: linear-gradient(145deg, rgba(24, 31, 43, 0.98), rgba(14, 20, 30, 0.98));
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 18px;
            padding: 20px 22px;
            margin: 12px 0 18px 0;
            box-shadow: 0 10px 28px rgba(0, 0, 0, 0.18);
        }
        .trade-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 14px;
            margin-bottom: 14px;
        }
        .trade-ticker {
            color: #f8fafc;
            font-size: 1.45rem;
            font-weight: 800;
        }
        .trade-subtitle {
            color: #94a3b8;
            font-size: 0.88rem;
            margin-top: 2px;
        }
        .trade-badge {
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.06em;
        }
        .trade-win {
            color: #86efac;
            background: rgba(34, 197, 94, 0.14);
            border: 1px solid rgba(34, 197, 94, 0.42);
        }
        .trade-loss {
            color: #fca5a5;
            background: rgba(239, 68, 68, 0.14);
            border: 1px solid rgba(239, 68, 68, 0.42);
        }
        .trade-flat {
            color: #fde68a;
            background: rgba(245, 158, 11, 0.14);
            border: 1px solid rgba(245, 158, 11, 0.42);
        }
        .trade-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin: 14px 0;
        }
        .trade-field {
            background: rgba(15, 23, 42, 0.54);
            border: 1px solid rgba(148, 163, 184, 0.13);
            border-radius: 12px;
            padding: 11px 12px;
        }
        .trade-field-label {
            color: #94a3b8;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 5px;
        }
        .trade-field-value {
            color: #e2e8f0;
            font-size: 0.96rem;
            font-weight: 650;
        }
        .trade-positive { color: #86efac; }
        .trade-negative { color: #fca5a5; }
        .trade-notes {
            margin-top: 12px;
            padding: 12px 14px;
            border-radius: 12px;
            background: rgba(15, 23, 42, 0.45);
            border-left: 3px solid #60a5fa;
            color: #cbd5e1;
            font-size: 0.9rem;
        }
        @media (max-width: 900px) {
            .trade-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    journal_portfolio = load_portfolio()
    closed_trades = journal_portfolio.get("closed_trades", [])
    activity_history = journal_portfolio.get("trade_history", [])

    journal_tab1, journal_tab2 = st.tabs(
        ["Completed Trades", "All Trading Activity"]
    )

    with journal_tab1:

        if not closed_trades:
            st.info(
                "No completed trades are available yet. "
                "Buy and then sell an asset to create the first completed-trade record."
            )
        else:
            closed_dataframe = pd.DataFrame(closed_trades)

            for timestamp_column in ["entry_timestamp", "exit_timestamp"]:
                if timestamp_column not in closed_dataframe.columns:
                    closed_dataframe[timestamp_column] = pd.NaT
                closed_dataframe[timestamp_column] = pd.to_datetime(
                    closed_dataframe[timestamp_column],
                    errors="coerce",
                )

            numeric_columns = [
                "quantity",
                "entry_price",
                "exit_price",
                "realised_pnl",
                "return_percentage",
                "holding_days",
            ]
            for numeric_column in numeric_columns:
                if numeric_column not in closed_dataframe.columns:
                    closed_dataframe[numeric_column] = 0.0
                closed_dataframe[numeric_column] = pd.to_numeric(
                    closed_dataframe[numeric_column],
                    errors="coerce",
                ).fillna(0.0)

            if "outcome" not in closed_dataframe.columns:
                closed_dataframe["outcome"] = closed_dataframe["realised_pnl"].apply(
                    lambda value: "WIN" if value > 0 else "LOSS" if value < 0 else "BREAKEVEN"
                )

            filter_column1, filter_column2, filter_column3 = st.columns(3)

            available_tickers = sorted(
                closed_dataframe["ticker"].dropna().unique().tolist()
            )

            with filter_column1:
                journal_tickers = st.multiselect(
                    "Ticker",
                    options=available_tickers,
                    default=available_tickers,
                    key="journal_ticker_filter",
                )

            with filter_column2:
                journal_outcomes = st.multiselect(
                    "Outcome",
                    options=["WIN", "LOSS", "BREAKEVEN"],
                    default=["WIN", "LOSS", "BREAKEVEN"],
                    key="journal_outcome_filter",
                )

            with filter_column3:
                date_values = closed_dataframe["exit_timestamp"].dropna()
                if not date_values.empty:
                    minimum_date = date_values.min().date()
                    maximum_date = date_values.max().date()
                    journal_date_range = st.date_input(
                        "Exit Date Range",
                        value=(minimum_date, maximum_date),
                        min_value=minimum_date,
                        max_value=maximum_date,
                        key="journal_date_filter",
                    )
                else:
                    journal_date_range = ()

            filtered_trades = closed_dataframe.copy()

            filtered_trades = filtered_trades[
                filtered_trades["ticker"].isin(journal_tickers)
            ] if journal_tickers else filtered_trades.iloc[0:0]

            filtered_trades = filtered_trades[
                filtered_trades["outcome"].isin(journal_outcomes)
            ] if journal_outcomes else filtered_trades.iloc[0:0]

            if isinstance(journal_date_range, tuple) and len(journal_date_range) == 2:
                start_date, end_date = journal_date_range
                filtered_trades = filtered_trades[
                    filtered_trades["exit_timestamp"].dt.date.between(
                        start_date,
                        end_date,
                    )
                ]

            total_completed = len(filtered_trades)
            winners = filtered_trades[filtered_trades["realised_pnl"] > 0]
            losers = filtered_trades[filtered_trades["realised_pnl"] < 0]

            win_rate = (
                len(winners) / total_completed * 100
                if total_completed > 0
                else 0.0
            )
            net_realised = filtered_trades["realised_pnl"].sum()
            average_trade = (
                filtered_trades["realised_pnl"].mean()
                if total_completed > 0
                else 0.0
            )
            average_winner = winners["realised_pnl"].mean() if not winners.empty else 0.0
            average_loser = losers["realised_pnl"].mean() if not losers.empty else 0.0
            gross_profit = winners["realised_pnl"].sum()
            gross_loss = abs(losers["realised_pnl"].sum())
            profit_factor = (
                gross_profit / gross_loss
                if gross_loss > 0
                else gross_profit if gross_profit > 0 else 0.0
            )
            best_trade = filtered_trades["realised_pnl"].max() if total_completed else 0.0
            worst_trade = filtered_trades["realised_pnl"].min() if total_completed else 0.0
            average_holding_days = (
                filtered_trades["holding_days"].mean()
                if total_completed > 0
                else 0.0
            )

            summary_values = [
                ("Net Realised P/L", format_currency(net_realised)),
                ("Win Rate", f"{win_rate:.1f}%"),
                ("Profit Factor", f"{profit_factor:.2f}"),
                ("Average Trade", format_currency(average_trade)),
            ]
            summary_columns = st.columns(4)
            for summary_column, (label, value) in zip(summary_columns, summary_values):
                with summary_column:
                    st.markdown(
                        f"""
                        <div class="journal-summary-card">
                            <div class="journal-summary-label">{label}</div>
                            <div class="journal-summary-value">{value}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            detail_metrics = st.columns(4)
            detail_metrics[0].metric("Completed Trades", total_completed)
            detail_metrics[1].metric("Average Winner", format_currency(average_winner))
            detail_metrics[2].metric("Average Loser", format_currency(average_loser))
            detail_metrics[3].metric(
                "Average Holding Time",
                f"{average_holding_days:.1f} days",
            )

            detail_metrics_2 = st.columns(2)
            detail_metrics_2[0].metric("Best Trade", format_currency(best_trade))
            detail_metrics_2[1].metric("Worst Trade", format_currency(worst_trade))

            st.divider()
            st.subheader("Performance Curve")

            if not filtered_trades.empty:
                equity_data = filtered_trades.sort_values("exit_timestamp").copy()
                equity_data["cumulative_realised_pnl"] = equity_data["realised_pnl"].cumsum()
                equity_data["account_value_after_trade"] = (
                    STARTING_CASH + equity_data["cumulative_realised_pnl"]
                )

                journal_chart = go.Figure()
                journal_chart.add_trace(
                    go.Scatter(
                        x=equity_data["exit_timestamp"],
                        y=equity_data["account_value_after_trade"],
                        mode="lines+markers",
                        name="Realised Account Value",
                        hovertemplate="%{x}<br>Account value: £%{y:,.2f}<extra></extra>",
                    )
                )
                journal_chart.update_layout(
                    title="Account Value Based on Closed Trades",
                    height=450,
                    xaxis_title="Exit Date",
                    yaxis_title="Account Value (£)",
                    margin=dict(l=20, r=20, t=60, b=20),
                )
                st.plotly_chart(journal_chart, use_container_width=True)

                st.subheader("Completed Trade Cards")

                card_trades = filtered_trades.sort_values(
                    "exit_timestamp",
                    ascending=False,
                )

                for _, trade in card_trades.iterrows():
                    realised_pnl_value = safe_float(trade.get("realised_pnl", 0.0))
                    return_value = safe_float(trade.get("return_percentage", 0.0))
                    outcome = str(trade.get("outcome", "BREAKEVEN")).upper()

                    if outcome == "WIN":
                        badge_class = "trade-win"
                        pnl_class = "trade-positive"
                    elif outcome == "LOSS":
                        badge_class = "trade-loss"
                        pnl_class = "trade-negative"
                    else:
                        badge_class = "trade-flat"
                        pnl_class = ""

                    entry_time = trade.get("entry_timestamp")
                    exit_time = trade.get("exit_timestamp")
                    entry_text = (
                        entry_time.strftime("%d %b %Y, %H:%M")
                        if pd.notna(entry_time)
                        else "Not available"
                    )
                    exit_text = (
                        exit_time.strftime("%d %b %Y, %H:%M")
                        if pd.notna(exit_time)
                        else "Not available"
                    )

                    holding_days_value = safe_float(trade.get("holding_days", 0.0))
                    holding_text = (
                        f"{holding_days_value:.1f} days"
                        if holding_days_value >= 1
                        else f"{holding_days_value * 24:.1f} hours"
                    )

                    entry_notes = str(trade.get("entry_notes", "") or "").strip()
                    exit_notes = str(trade.get("exit_notes", "") or "").strip()
                    combined_notes = "<br>".join(
                        note for note in [
                            f"<strong>Entry:</strong> {entry_notes}" if entry_notes else "",
                            f"<strong>Exit:</strong> {exit_notes}" if exit_notes else "",
                        ] if note
                    )
                    if not combined_notes:
                        combined_notes = "No journal notes were entered for this trade."

                    ticker_text = str(trade.get("ticker", "Unknown"))
                    quantity_text = f"{safe_float(trade.get('quantity', 0.0)):g}"
                    entry_signal = str(trade.get("entry_signal", "UNKNOWN"))
                    exit_signal = str(trade.get("exit_signal", "UNKNOWN"))
                    entry_ai = str(trade.get("entry_ai_recommendation", "UNKNOWN"))
                    exit_ai = str(trade.get("exit_ai_recommendation", "UNKNOWN"))
                    risk_profile_text = str(trade.get("risk_profile", "Balanced"))

                    st.markdown(
                        f"""
                        <div class="trade-card">
                            <div class="trade-header">
                                <div>
                                    <div class="trade-ticker">{ticker_text}</div>
                                    <div class="trade-subtitle">{entry_text} → {exit_text}</div>
                                </div>
                                <div class="trade-badge {badge_class}">{outcome}</div>
                            </div>
                            <div class="trade-grid">
                                <div class="trade-field">
                                    <div class="trade-field-label">Quantity</div>
                                    <div class="trade-field-value">{quantity_text}</div>
                                </div>
                                <div class="trade-field">
                                    <div class="trade-field-label">Entry Price</div>
                                    <div class="trade-field-value">{format_currency(safe_float(trade.get('entry_price', 0.0)))}</div>
                                </div>
                                <div class="trade-field">
                                    <div class="trade-field-label">Exit Price</div>
                                    <div class="trade-field-value">{format_currency(safe_float(trade.get('exit_price', 0.0)))}</div>
                                </div>
                                <div class="trade-field">
                                    <div class="trade-field-label">Holding Time</div>
                                    <div class="trade-field-value">{holding_text}</div>
                                </div>
                                <div class="trade-field">
                                    <div class="trade-field-label">Realised P/L</div>
                                    <div class="trade-field-value {pnl_class}">{format_currency(realised_pnl_value)}</div>
                                </div>
                                <div class="trade-field">
                                    <div class="trade-field-label">Return</div>
                                    <div class="trade-field-value {pnl_class}">{return_value:+.2f}%</div>
                                </div>
                                <div class="trade-field">
                                    <div class="trade-field-label">Strategy</div>
                                    <div class="trade-field-value">{entry_signal} → {exit_signal}</div>
                                </div>
                                <div class="trade-field">
                                    <div class="trade-field-label">AI / Risk</div>
                                    <div class="trade-field-value">{entry_ai} → {exit_ai} · {risk_profile_text}</div>
                                </div>
                            </div>
                            <div class="trade-notes">{combined_notes}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with st.expander("View Completed Trades as a Table"):
                    display_columns = [
                        "entry_timestamp",
                        "exit_timestamp",
                        "ticker",
                        "quantity",
                        "entry_price",
                        "exit_price",
                        "realised_pnl",
                        "return_percentage",
                        "holding_days",
                        "outcome",
                        "entry_signal",
                        "exit_signal",
                        "entry_ai_recommendation",
                        "exit_ai_recommendation",
                        "risk_profile",
                        "entry_stop_loss",
                        "entry_take_profit",
                        "entry_notes",
                        "exit_notes",
                    ]
                    available_display_columns = [
                        column
                        for column in display_columns
                        if column in card_trades.columns
                    ]
                    journal_display = card_trades[available_display_columns]
                    st.dataframe(
                        journal_display,
                        use_container_width=True,
                        hide_index=True,
                    )

                csv_data = card_trades.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download Journal CSV",
                    data=csv_data,
                    file_name="tam_tradex_trading_journal.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.warning("No completed trades match the selected filters.")

    with journal_tab2:

        if activity_history:
            activity_dataframe = pd.DataFrame(activity_history)
            if "timestamp" in activity_dataframe.columns:
                activity_dataframe["timestamp"] = pd.to_datetime(
                    activity_dataframe["timestamp"],
                    errors="coerce",
                )
                activity_dataframe = activity_dataframe.sort_values(
                    "timestamp",
                    ascending=False,
                )

            activity_metric_columns = st.columns(3)
            activity_metric_columns[0].metric(
                "Total Orders",
                len(activity_dataframe),
            )
            activity_metric_columns[1].metric(
                "Buy Orders",
                int((activity_dataframe.get("action") == "BUY").sum()),
            )
            activity_metric_columns[2].metric(
                "Sell Orders",
                int((activity_dataframe.get("action") == "SELL").sum()),
            )

            st.dataframe(
                activity_dataframe,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No trading activity has been recorded yet.")


# ==================================================
# WATCHLIST SCREEN
# ==================================================

elif st.session_state.current_page == "watchlist":

    st.header("Professional Watchlist")

    st.write(
        "Track selected equities and crypto assets, compare live technical "
        "conditions and open any symbol directly in the analysis workspace."
    )

    watchlist_controls = st.columns([2, 1, 1])

    with watchlist_controls[0]:

        new_watchlist_ticker = st.text_input(
            "Add Ticker",
            placeholder="Examples: AAPL, SPY, BTC-USD",
            key="watchlist_add_ticker",
        )

    with watchlist_controls[1]:

        st.write("")
        st.write("")

        add_watchlist_button = st.button(
            "Add to Watchlist",
            use_container_width=True,
            type="primary",
            key="watchlist_add_button",
        )

    with watchlist_controls[2]:

        st.write("")
        st.write("")

        refresh_watchlist_button = st.button(
            "Refresh Prices",
            use_container_width=True,
            key="watchlist_refresh_button",
        )

    if add_watchlist_button:

        success, message = add_ticker(new_watchlist_ticker)

        if success:
            st.success(message)
            st.rerun()
        else:
            st.warning(message)

    watchlist_tickers = load_watchlist()

    if refresh_watchlist_button:
        st.cache_data.clear()
        st.rerun()

    search_column, sort_column = st.columns([2, 1])

    with search_column:

        watchlist_search = st.text_input(
            "Search Watchlist",
            placeholder="Filter by ticker",
            key="watchlist_search",
        ).strip().upper()

    with sort_column:

        watchlist_sort = st.selectbox(
            "Sort By",
            options=[
                "Ticker",
                "Daily Change %",
                "RSI",
                "Signal",
                "Current Price",
            ],
            key="watchlist_sort",
        )

    filtered_watchlist_tickers = [
        item
        for item in watchlist_tickers
        if watchlist_search in item
    ]

    watchlist_rows = []
    watchlist_errors = []

    if filtered_watchlist_tickers:

        with st.spinner("Updating watchlist market data..."):

            for watchlist_ticker in filtered_watchlist_tickers:

                try:

                    watchlist_data = load_asset_data(
                        watchlist_ticker
                    )

                    if watchlist_data is None or watchlist_data.empty:
                        watchlist_errors.append(
                            f"{watchlist_ticker}: no market data returned."
                        )
                        continue

                    watchlist_signal, watchlist_reason = generate_signal(
                        watchlist_data
                    )

                    current_price = get_latest_price(
                        watchlist_data
                    )

                    previous_price = safe_float(
                        watchlist_data["Close"].iloc[-2]
                    )

                    daily_change = (
                        (
                            current_price
                            - previous_price
                        )
                        / previous_price
                        * 100
                        if previous_price != 0
                        else 0.0
                    )

                    latest_rsi = safe_float(
                        watchlist_data["rsi"].iloc[-1]
                    )

                    short_average = safe_float(
                        watchlist_data["short_average"].iloc[-1]
                    )

                    long_average = safe_float(
                        watchlist_data["long_average"].iloc[-1]
                    )

                    if (
                        current_price > short_average
                        and short_average > long_average
                    ):
                        trend = "Bullish"
                    elif (
                        current_price < short_average
                        and short_average < long_average
                    ):
                        trend = "Bearish"
                    else:
                        trend = "Neutral"

                    volume_value = (
                        safe_float(
                            watchlist_data["Volume"].iloc[-1]
                        )
                        if "Volume" in watchlist_data.columns
                        else 0.0
                    )

                    watchlist_rows.append(
                        {
                            "Ticker": watchlist_ticker,
                            "Current Price": current_price,
                            "Daily Change %": daily_change,
                            "RSI": latest_rsi,
                            "Signal": watchlist_signal,
                            "Trend": trend,
                            "Volume": volume_value,
                            "Reason": watchlist_reason,
                        }
                    )

                except Exception as error:

                    watchlist_errors.append(
                        f"{watchlist_ticker}: {error}"
                    )

    if watchlist_rows:

        watchlist_dataframe = pd.DataFrame(
            watchlist_rows
        )

        ascending = True

        if watchlist_sort == "Ticker":
            sort_column_name = "Ticker"
        elif watchlist_sort == "Daily Change %":
            sort_column_name = "Daily Change %"
            ascending = False
        elif watchlist_sort == "RSI":
            sort_column_name = "RSI"
            ascending = False
        elif watchlist_sort == "Signal":
            signal_rank = {
                "BUY": 0,
                "HOLD": 1,
                "SELL": 2,
            }
            watchlist_dataframe["_signal_rank"] = (
                watchlist_dataframe["Signal"]
                .map(signal_rank)
                .fillna(3)
            )
            sort_column_name = "_signal_rank"
        else:
            sort_column_name = "Current Price"
            ascending = False

        watchlist_dataframe = watchlist_dataframe.sort_values(
            sort_column_name,
            ascending=ascending,
        )

        if "_signal_rank" in watchlist_dataframe.columns:
            watchlist_dataframe = watchlist_dataframe.drop(
                columns=["_signal_rank"]
            )

        buy_signals = int(
            (watchlist_dataframe["Signal"] == "BUY").sum()
        )

        sell_signals = int(
            (watchlist_dataframe["Signal"] == "SELL").sum()
        )

        hold_signals = int(
            (watchlist_dataframe["Signal"] == "HOLD").sum()
        )

        average_rsi = safe_float(
            watchlist_dataframe["RSI"].mean()
        )

        watchlist_metrics = st.columns(5)

        watchlist_metrics[0].metric(
            "Tracked Assets",
            len(watchlist_dataframe),
        )

        watchlist_metrics[1].metric(
            "BUY Signals",
            buy_signals,
        )

        watchlist_metrics[2].metric(
            "HOLD Signals",
            hold_signals,
        )

        watchlist_metrics[3].metric(
            "SELL Signals",
            sell_signals,
        )

        watchlist_metrics[4].metric(
            "Average RSI",
            f"{average_rsi:.1f}",
        )

        st.divider()

        st.subheader("Live Watchlist")

        st.dataframe(
            watchlist_dataframe[
                [
                    "Ticker",
                    "Current Price",
                    "Daily Change %",
                    "RSI",
                    "Signal",
                    "Trend",
                    "Volume",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Current Price": st.column_config.NumberColumn(
                    format="£%.2f"
                ),
                "Daily Change %": st.column_config.NumberColumn(
                    format="%+.2f%%"
                ),
                "RSI": st.column_config.NumberColumn(
                    format="%.1f"
                ),
                "Volume": st.column_config.NumberColumn(
                    format="%.0f"
                ),
            },
        )

        st.subheader("Quick Actions")

        selected_watchlist_ticker = st.selectbox(
            "Select Ticker",
            options=watchlist_dataframe["Ticker"].tolist(),
            key="watchlist_action_ticker",
        )

        action_column1, action_column2, action_column3 = st.columns(3)

        with action_column1:

            analyse_watchlist_ticker = st.button(
                f"Analyse {selected_watchlist_ticker}",
                use_container_width=True,
                type="primary",
                key="watchlist_analyse_button",
            )

        with action_column2:

            remove_watchlist_ticker = st.button(
                f"Remove {selected_watchlist_ticker}",
                use_container_width=True,
                key="watchlist_remove_button",
            )

        with action_column3:

            export_watchlist_csv = watchlist_dataframe.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "Export Watchlist CSV",
                data=export_watchlist_csv,
                file_name="tam_tradex_watchlist.csv",
                mime="text/csv",
                use_container_width=True,
            )

        if analyse_watchlist_ticker:

            matching_asset_name = next(
                (
                    asset_name
                    for asset_name, asset_ticker in ASSET_OPTIONS.items()
                    if asset_ticker == selected_watchlist_ticker
                ),
                None,
            )

            if matching_asset_name is not None:
                st.session_state["selected_asset_override"] = (
                    matching_asset_name
                )
                st.session_state.current_page = "analysis"
                st.rerun()
            else:
                st.warning(
                    "This custom ticker is not currently mapped to the "
                    "sidebar asset selector. Add it to ASSET_OPTIONS to open "
                    "it directly in Analyse Asset."
                )

        if remove_watchlist_ticker:

            success, message = remove_ticker(
                selected_watchlist_ticker
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                st.warning(message)

        with st.expander("Signal Explanations"):

            for _, row in watchlist_dataframe.iterrows():
                st.write(
                    f"**{row['Ticker']} — {row['Signal']}**: "
                    f"{row['Reason']}"
                )

    else:

        st.info(
            "The watchlist is empty or no selected symbols returned data."
        )

    if watchlist_errors:

        with st.expander("Watchlist Data Warnings"):

            for watchlist_error in watchlist_errors:
                st.warning(watchlist_error)

    st.divider()

    reset_watchlist_button = st.button(
        "Reset Default Watchlist",
        use_container_width=True,
        key="watchlist_reset_button",
    )

    if reset_watchlist_button:

        reset_watchlist()
        st.success("The default watchlist was restored.")
        st.rerun()


    st.divider()
    st.subheader("Smart Price and Signal Alerts")

    st.write(
        "Create persistent alerts for price thresholds, RSI levels "
        "and BUY, HOLD or SELL signal changes."
    )

    alert_form_columns = st.columns([1.2, 1.4, 1.2, 1])

    with alert_form_columns[0]:

        alert_ticker = st.selectbox(
            "Alert Ticker",
            options=watchlist_tickers,
            key="smart_alert_ticker",
        )

    with alert_form_columns[1]:

        alert_condition = st.selectbox(
            "Condition",
            options=[
                "Price Above",
                "Price Below",
                "RSI Above",
                "RSI Below",
                "Signal Equals",
            ],
            key="smart_alert_condition",
        )

    with alert_form_columns[2]:

        if alert_condition == "Signal Equals":

            alert_target = st.selectbox(
                "Signal Target",
                options=[
                    "BUY",
                    "HOLD",
                    "SELL",
                ],
                key="smart_alert_signal_target",
            )

        elif alert_condition.startswith("RSI"):

            alert_target = st.number_input(
                "RSI Target",
                min_value=0.0,
                max_value=100.0,
                value=70.0
                if alert_condition == "RSI Above"
                else 30.0,
                step=1.0,
                key="smart_alert_rsi_target",
            )

        else:

            default_alert_price = 100.0

            if watchlist_rows:
                matching_rows = [
                    row
                    for row in watchlist_rows
                    if row["Ticker"] == alert_ticker
                ]

                if matching_rows:
                    default_alert_price = safe_float(
                        matching_rows[0][
                            "Current Price"
                        ]
                    )

            alert_target = st.number_input(
                "Price Target",
                min_value=0.01,
                value=float(
                    max(
                        default_alert_price,
                        0.01,
                    )
                ),
                step=1.0,
                key="smart_alert_price_target",
            )

    with alert_form_columns[3]:

        st.write("")
        st.write("")

        create_alert_button = st.button(
            "Create Alert",
            type="primary",
            use_container_width=True,
            key="smart_alert_create_button",
        )

    if create_alert_button:

        alert_success, alert_message = create_alert(
            ticker=alert_ticker,
            condition=alert_condition,
            target=alert_target,
        )

        if alert_success:
            st.success(alert_message)
            st.rerun()
        else:
            st.warning(alert_message)

    alert_market_snapshot = {}

    for alert_row in watchlist_rows:
        alert_market_snapshot[
            alert_row["Ticker"]
        ] = {
            "price": safe_float(
                alert_row["Current Price"]
            ),
            "rsi": safe_float(
                alert_row["RSI"]
            ),
            "signal": alert_row["Signal"],
        }

    triggered_alerts = check_alerts(
        alert_market_snapshot
    )

    for triggered_alert in triggered_alerts:
        st.success(
            "🔔 "
            + str(
                triggered_alert.get(
                    "message",
                    "Alert triggered.",
                )
            )
        )

    saved_alerts = load_alerts()

    if saved_alerts:

        alert_rows = []

        for alert in saved_alerts:

            target_value = alert.get("target")

            if isinstance(
                target_value,
                float,
            ):
                target_display = (
                    f"{target_value:.2f}"
                )
            else:
                target_display = str(
                    target_value
                )

            alert_rows.append(
                {
                    "ID": alert.get("id"),
                    "Ticker": alert.get("ticker"),
                    "Condition": alert.get(
                        "condition"
                    ),
                    "Target": target_display,
                    "Active": bool(
                        alert.get("active", True)
                    ),
                    "Triggered": bool(
                        alert.get(
                            "triggered",
                            False,
                        )
                    ),
                    "Last Value": alert.get(
                        "last_value"
                    ),
                    "Triggered At": alert.get(
                        "triggered_at"
                    ),
                    "Message": alert.get(
                        "message",
                        "",
                    ),
                }
            )

        alert_dataframe = pd.DataFrame(
            alert_rows
        )

        alert_metrics = st.columns(4)

        alert_metrics[0].metric(
            "Total Alerts",
            len(alert_dataframe),
        )

        alert_metrics[1].metric(
            "Active Alerts",
            int(
                alert_dataframe[
                    "Active"
                ].sum()
            ),
        )

        alert_metrics[2].metric(
            "Triggered Alerts",
            int(
                alert_dataframe[
                    "Triggered"
                ].sum()
            ),
        )

        alert_metrics[3].metric(
            "Inactive Alerts",
            int(
                (
                    ~alert_dataframe[
                        "Active"
                    ]
                ).sum()
            ),
        )

        st.dataframe(
            alert_dataframe.drop(
                columns=["ID"]
            ),
            use_container_width=True,
            hide_index=True,
        )

        selected_alert_id = st.selectbox(
            "Manage Alert",
            options=[
                alert["id"]
                for alert in saved_alerts
            ],
            format_func=lambda alert_id: next(
                (
                    f"{alert['ticker']} — "
                    f"{alert['condition']} "
                    f"{alert['target']}"
                    for alert in saved_alerts
                    if alert["id"] == alert_id
                ),
                alert_id,
            ),
            key="smart_alert_manage_id",
        )

        selected_alert = next(
            (
                alert
                for alert in saved_alerts
                if alert["id"]
                == selected_alert_id
            ),
            None,
        )

        manage_alert_columns = st.columns(3)

        with manage_alert_columns[0]:

            if selected_alert:

                toggle_alert_label = (
                    "Disable Alert"
                    if selected_alert.get(
                        "active",
                        True,
                    )
                    else "Enable Alert"
                )

                toggle_alert_button = st.button(
                    toggle_alert_label,
                    use_container_width=True,
                    key="smart_alert_toggle_button",
                )

                if toggle_alert_button:

                    toggle_success, toggle_message = (
                        set_alert_active(
                            selected_alert_id,
                            not selected_alert.get(
                                "active",
                                True,
                            ),
                        )
                    )

                    if toggle_success:
                        st.success(toggle_message)
                        st.rerun()
                    else:
                        st.warning(toggle_message)

        with manage_alert_columns[1]:

            delete_alert_button = st.button(
                "Delete Alert",
                use_container_width=True,
                key="smart_alert_delete_button",
            )

            if delete_alert_button:

                delete_success, delete_message = (
                    delete_alert(
                        selected_alert_id
                    )
                )

                if delete_success:
                    st.success(delete_message)
                    st.rerun()
                else:
                    st.warning(delete_message)

        with manage_alert_columns[2]:

            refresh_alerts_button = st.button(
                "Check Alerts Now",
                use_container_width=True,
                key="smart_alert_refresh_button",
            )

            if refresh_alerts_button:
                st.rerun()

    else:

        st.info(
            "No smart alerts have been created yet."
        )

    st.caption(
        "Alerts are evaluated when the Watchlist page loads or refreshes. "
        "They do not run continuously while Streamlit is closed."
    )



# ==================================================
# STRATEGY LAB SCREEN
# ==================================================

elif st.session_state.current_page == "strategy_lab":

    st.header("Professional Strategy Lab")

    st.write(
        "Compare multiple systematic trading strategies, adjust model "
        "parameters and identify the strongest historical risk-adjusted "
        "approach for the selected asset."
    )

    strategy_lab_control1, strategy_lab_control2 = st.columns(2)

    with strategy_lab_control1:

        strategy_lab_capital = st.number_input(
            "Initial Capital",
            min_value=100.0,
            value=10_000.0,
            step=500.0,
            key="strategy_lab_initial_capital",
        )

    with strategy_lab_control2:

        st.metric(
            "Selected Asset",
            f"{selected_asset} ({ticker})",
        )

    strategy_lab_strategies = st.multiselect(
        "Strategies to Compare",
        options=[
            "Moving Average Crossover",
            "RSI Reversal",
            "MACD Crossover",
            "Bollinger Mean Reversion",
            "Breakout",
        ],
        default=[
            "Moving Average Crossover",
            "RSI Reversal",
            "MACD Crossover",
            "Bollinger Mean Reversion",
            "Breakout",
        ],
        key="strategy_lab_strategies",
    )

    with st.expander(
        "Strategy Parameters",
        expanded=True,
    ):

        parameter_column1, parameter_column2, parameter_column3 = st.columns(3)

        with parameter_column1:

            strategy_lab_short_ma = st.slider(
                "Short Moving Average",
                min_value=5,
                max_value=50,
                value=10,
                step=1,
                key="strategy_lab_short_ma",
            )

            strategy_lab_long_ma = st.slider(
                "Long Moving Average",
                min_value=20,
                max_value=200,
                value=30,
                step=5,
                key="strategy_lab_long_ma",
            )

            strategy_lab_breakout_window = st.slider(
                "Breakout Window",
                min_value=5,
                max_value=100,
                value=20,
                step=5,
                key="strategy_lab_breakout_window",
            )

        with parameter_column2:

            strategy_lab_rsi_buy = st.slider(
                "RSI Buy Threshold",
                min_value=10,
                max_value=40,
                value=30,
                step=1,
                key="strategy_lab_rsi_buy",
            )

            strategy_lab_rsi_sell = st.slider(
                "RSI Sell Threshold",
                min_value=60,
                max_value=90,
                value=70,
                step=1,
                key="strategy_lab_rsi_sell",
            )

            strategy_lab_bollinger_window = st.slider(
                "Bollinger Window",
                min_value=10,
                max_value=50,
                value=20,
                step=1,
                key="strategy_lab_bollinger_window",
            )

        with parameter_column3:

            strategy_lab_bollinger_std = st.slider(
                "Bollinger Standard Deviations",
                min_value=1.0,
                max_value=3.5,
                value=2.0,
                step=0.1,
                key="strategy_lab_bollinger_std",
            )

            strategy_lab_stop_loss = st.slider(
                "Stop Loss (%)",
                min_value=1.0,
                max_value=25.0,
                value=8.0,
                step=0.5,
                key="strategy_lab_stop_loss",
            )

            strategy_lab_take_profit = st.slider(
                "Take Profit (%)",
                min_value=2.0,
                max_value=50.0,
                value=15.0,
                step=0.5,
                key="strategy_lab_take_profit",
            )

    strategy_lab_run_button = st.button(
        f"Run Strategy Lab for {ticker}",
        type="primary",
        use_container_width=True,
        key=f"strategy_lab_run_{ticker}",
    )

    if strategy_lab_run_button:

        if not strategy_lab_strategies:
            st.warning(
                "Select at least one strategy before running the lab."
            )

        elif strategy_lab_short_ma >= strategy_lab_long_ma:
            st.warning(
                "The short moving average must be below the long moving average."
            )

        else:

            with st.spinner(
                f"Testing {len(strategy_lab_strategies)} strategies for {ticker}..."
            ):

                try:

                    strategy_lab_data = load_asset_data(
                        ticker
                    )

                    if (
                        strategy_lab_data is None
                        or strategy_lab_data.empty
                    ):
                        st.error(
                            "No historical market data was returned "
                            "for the selected asset."
                        )
                        st.stop()

                    strategy_lab_parameters = StrategyParameters(
                        short_ma=strategy_lab_short_ma,
                        long_ma=strategy_lab_long_ma,
                        rsi_buy=float(strategy_lab_rsi_buy),
                        rsi_sell=float(strategy_lab_rsi_sell),
                        bollinger_window=strategy_lab_bollinger_window,
                        bollinger_std=float(strategy_lab_bollinger_std),
                        breakout_window=strategy_lab_breakout_window,
                        stop_loss_pct=float(strategy_lab_stop_loss),
                        take_profit_pct=float(strategy_lab_take_profit),
                    )

                    strategy_lab_results = compare_strategies(
                        data=strategy_lab_data,
                        strategies=strategy_lab_strategies,
                        initial_capital=float(strategy_lab_capital),
                        parameters=strategy_lab_parameters,
                    )

                    st.session_state[
                        "strategy_lab_results"
                    ] = strategy_lab_results

                    st.session_state[
                        "strategy_lab_ticker"
                    ] = ticker

                    st.session_state[
                        "strategy_lab_capital_used"
                    ] = strategy_lab_capital

                except Exception as error:

                    st.error(
                        f"Strategy Lab error: {error}"
                    )

    stored_strategy_lab_results = st.session_state.get(
        "strategy_lab_results"
    )

    stored_strategy_lab_ticker = st.session_state.get(
        "strategy_lab_ticker"
    )

    if (
        stored_strategy_lab_results
        and stored_strategy_lab_ticker == ticker
    ):

        st.divider()

        strategy_lab_recommendation = (
            stored_strategy_lab_results[
                "recommendation"
            ]
        )

        st.success(
            f"Recommended Strategy: "
            f"{strategy_lab_recommendation['strategy']} | "
            f"Confidence: "
            f"{safe_float(strategy_lab_recommendation['confidence']):.1f}%"
        )

        st.caption(
            strategy_lab_recommendation[
                "reason"
            ]
        )

        strategy_lab_comparison = (
            stored_strategy_lab_results[
                "comparison"
            ].copy()
        )

        best_strategy_row = (
            strategy_lab_comparison
            .sort_values(
                "Sharpe",
                ascending=False,
            )
            .iloc[0]
        )

        strategy_lab_metric_columns = st.columns(5)

        strategy_lab_metric_columns[0].metric(
            "Best Return",
            f"{safe_float(strategy_lab_comparison['Return %'].max()):.2f}%",
        )

        strategy_lab_metric_columns[1].metric(
            "Best Sharpe",
            f"{safe_float(strategy_lab_comparison['Sharpe'].max()):.2f}",
        )

        strategy_lab_metric_columns[2].metric(
            "Lowest Drawdown",
            f"{safe_float(strategy_lab_comparison['Max Drawdown %'].max()):.2f}%",
        )

        strategy_lab_metric_columns[3].metric(
            "Highest Win Rate",
            f"{safe_float(strategy_lab_comparison['Win Rate %'].max()):.2f}%",
        )

        strategy_lab_metric_columns[4].metric(
            "Top Sharpe Strategy",
            str(best_strategy_row["Strategy"]),
        )

        st.subheader("Strategy Comparison")

        st.dataframe(
            strategy_lab_comparison[
                [
                    "Strategy",
                    "Final Value",
                    "Return %",
                    "CAGR %",
                    "Sharpe",
                    "Sortino",
                    "Max Drawdown %",
                    "Win Rate %",
                    "Profit Factor",
                    "Expectancy",
                    "Volatility %",
                    "Trades",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Final Value": st.column_config.NumberColumn(
                    format="£%.2f"
                ),
                "Return %": st.column_config.NumberColumn(
                    format="%+.2f%%"
                ),
                "CAGR %": st.column_config.NumberColumn(
                    format="%+.2f%%"
                ),
                "Max Drawdown %": st.column_config.NumberColumn(
                    format="%.2f%%"
                ),
                "Win Rate %": st.column_config.NumberColumn(
                    format="%.2f%%"
                ),
                "Expectancy": st.column_config.NumberColumn(
                    format="£%.2f"
                ),
                "Volatility %": st.column_config.NumberColumn(
                    format="%.2f%%"
                ),
            },
        )

        st.subheader("Equity Curve Comparison")

        strategy_lab_equity_chart = go.Figure()

        strategy_lab_initial_capital_used = safe_float(
            st.session_state.get(
                "strategy_lab_capital_used",
                10_000.0,
            )
        )

        strategy_lab_equity_chart.add_trace(
            go.Scatter(
                x=[
                    min(
                        result["equity_curve"].index
                    )
                    for result in stored_strategy_lab_results[
                        "results"
                    ].values()
                ][0:1]
                + [
                    max(
                        result["equity_curve"].index
                    )
                    for result in stored_strategy_lab_results[
                        "results"
                    ].values()
                ][0:1],
                y=[
                    strategy_lab_initial_capital_used,
                    strategy_lab_initial_capital_used,
                ],
                mode="lines",
                name="Initial Capital",
                line={"dash": "dash"},
            )
        )

        for (
            strategy_name,
            strategy_result,
        ) in stored_strategy_lab_results[
            "results"
        ].items():

            strategy_equity_curve = strategy_result[
                "equity_curve"
            ]

            strategy_lab_equity_chart.add_trace(
                go.Scatter(
                    x=strategy_equity_curve.index,
                    y=strategy_equity_curve.values,
                    mode="lines",
                    name=strategy_name,
                    hovertemplate=(
                        "%{x}<br>"
                        "Portfolio Value: £%{y:,.2f}"
                        "<extra></extra>"
                    ),
                )
            )

        strategy_lab_equity_chart.update_layout(
            height=520,
            xaxis_title="Date",
            yaxis_title="Portfolio Value (£)",
            hovermode="x unified",
            margin=dict(
                l=20,
                r=20,
                t=30,
                b=20,
            ),
        )

        st.plotly_chart(
            strategy_lab_equity_chart,
            use_container_width=True,
        )

        chart_column1, chart_column2 = st.columns(2)

        with chart_column1:

            return_chart = go.Figure()

            return_chart.add_trace(
                go.Bar(
                    x=strategy_lab_comparison["Strategy"],
                    y=strategy_lab_comparison["Return %"],
                    text=strategy_lab_comparison["Return %"].map(
                        lambda value: f"{value:.1f}%"
                    ),
                    textposition="auto",
                )
            )

            return_chart.update_layout(
                title="Total Return by Strategy",
                height=400,
                yaxis_title="Return (%)",
                margin=dict(
                    l=20,
                    r=20,
                    t=60,
                    b=20,
                ),
            )

            st.plotly_chart(
                return_chart,
                use_container_width=True,
            )

        with chart_column2:

            risk_adjusted_chart = go.Figure()

            risk_adjusted_chart.add_trace(
                go.Bar(
                    x=strategy_lab_comparison["Strategy"],
                    y=strategy_lab_comparison["Sharpe"],
                    text=strategy_lab_comparison["Sharpe"].map(
                        lambda value: f"{value:.2f}"
                    ),
                    textposition="auto",
                )
            )

            risk_adjusted_chart.update_layout(
                title="Sharpe Ratio by Strategy",
                height=400,
                yaxis_title="Sharpe Ratio",
                margin=dict(
                    l=20,
                    r=20,
                    t=60,
                    b=20,
                ),
            )

            st.plotly_chart(
                risk_adjusted_chart,
                use_container_width=True,
            )

        selected_strategy_detail = st.selectbox(
            "Inspect Strategy Trade Log",
            options=list(
                stored_strategy_lab_results[
                    "results"
                ].keys()
            ),
            key="strategy_lab_trade_log_selection",
        )

        selected_strategy_result = (
            stored_strategy_lab_results[
                "results"
            ][selected_strategy_detail]
        )

        selected_trade_log = selected_strategy_result[
            "trade_log"
        ]

        if selected_trade_log.empty:
            st.info(
                "This strategy produced no completed transactions."
            )
        else:
            st.dataframe(
                selected_trade_log,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Price": st.column_config.NumberColumn(
                        format="£%.2f"
                    ),
                    "Quantity": st.column_config.NumberColumn(
                        format="%.6f"
                    ),
                    "Trade P/L": st.column_config.NumberColumn(
                        format="£%.2f"
                    ),
                },
            )

        strategy_lab_csv = strategy_lab_comparison.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download Strategy Comparison CSV",
            data=strategy_lab_csv,
            file_name=f"tam_tradex_strategy_lab_{ticker}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.warning(
            "Strategy Lab results are historical simulations. "
            "They do not guarantee future performance and exclude "
            "transaction costs, slippage, taxes and liquidity constraints."
        )


    st.divider()
    st.subheader("AI Strategy Optimizer")

    st.write(
        "Search a controlled parameter grid and rank the strongest "
        "configuration using return, Sharpe ratio, drawdown, profit factor "
        "and trade quality."
    )

    optimizer_strategy = st.selectbox(
        "Strategy to Optimise",
        options=[
            "Moving Average Crossover",
            "RSI Reversal",
            "MACD Crossover",
            "Bollinger Mean Reversion",
            "Breakout",
        ],
        key="optimizer_strategy",
    )

    optimizer_column1, optimizer_column2 = st.columns(2)

    with optimizer_column1:
        optimizer_capital = st.number_input(
            "Optimizer Initial Capital",
            min_value=100.0,
            value=10_000.0,
            step=500.0,
            key="optimizer_initial_capital",
        )

    with optimizer_column2:
        optimizer_maximum_tests = st.slider(
            "Maximum Tests",
            min_value=10,
            max_value=500,
            value=150,
            step=10,
            key="optimizer_maximum_tests",
            help=(
                "A lower limit keeps the application responsive. "
                "Combinations above this limit are not run."
            ),
        )

    optimizer_parameter_grid = {}

    with st.expander(
        "Optimizer Parameter Grid",
        expanded=True,
    ):

        if optimizer_strategy == "Moving Average Crossover":

            optimizer_short_ma_values = st.multiselect(
                "Short MA Values",
                options=[
                    5,
                    8,
                    10,
                    12,
                    15,
                    20,
                    25,
                    30,
                ],
                default=[
                    5,
                    10,
                    15,
                    20,
                ],
                key="optimizer_short_ma_values",
            )

            optimizer_long_ma_values = st.multiselect(
                "Long MA Values",
                options=[
                    20,
                    30,
                    40,
                    50,
                    75,
                    100,
                    150,
                    200,
                ],
                default=[
                    30,
                    50,
                    100,
                ],
                key="optimizer_long_ma_values",
            )

            optimizer_stop_loss_values = st.multiselect(
                "Stop-Loss Values (%)",
                options=[
                    3.0,
                    5.0,
                    8.0,
                    10.0,
                    12.0,
                ],
                default=[
                    5.0,
                    8.0,
                    10.0,
                ],
                key="optimizer_ma_stop_loss_values",
            )

            optimizer_take_profit_values = st.multiselect(
                "Take-Profit Values (%)",
                options=[
                    8.0,
                    10.0,
                    15.0,
                    20.0,
                    25.0,
                    30.0,
                ],
                default=[
                    10.0,
                    15.0,
                    20.0,
                ],
                key="optimizer_ma_take_profit_values",
            )

            optimizer_parameter_grid = {
                "short_ma": optimizer_short_ma_values,
                "long_ma": optimizer_long_ma_values,
                "stop_loss_pct": optimizer_stop_loss_values,
                "take_profit_pct": optimizer_take_profit_values,
            }

        elif optimizer_strategy == "RSI Reversal":

            optimizer_rsi_buy_values = st.multiselect(
                "RSI Entry Values",
                options=[
                    20.0,
                    25.0,
                    30.0,
                    35.0,
                    40.0,
                ],
                default=[
                    25.0,
                    30.0,
                    35.0,
                ],
                key="optimizer_rsi_buy_values",
            )

            optimizer_rsi_sell_values = st.multiselect(
                "RSI Exit Values",
                options=[
                    60.0,
                    65.0,
                    70.0,
                    75.0,
                    80.0,
                ],
                default=[
                    65.0,
                    70.0,
                    75.0,
                ],
                key="optimizer_rsi_sell_values",
            )

            optimizer_stop_loss_values = st.multiselect(
                "Stop-Loss Values (%)",
                options=[
                    3.0,
                    5.0,
                    8.0,
                    10.0,
                    12.0,
                ],
                default=[
                    5.0,
                    8.0,
                    10.0,
                ],
                key="optimizer_rsi_stop_loss_values",
            )

            optimizer_take_profit_values = st.multiselect(
                "Take-Profit Values (%)",
                options=[
                    8.0,
                    10.0,
                    15.0,
                    20.0,
                    25.0,
                ],
                default=[
                    10.0,
                    15.0,
                    20.0,
                ],
                key="optimizer_rsi_take_profit_values",
            )

            optimizer_parameter_grid = {
                "rsi_buy": optimizer_rsi_buy_values,
                "rsi_sell": optimizer_rsi_sell_values,
                "stop_loss_pct": optimizer_stop_loss_values,
                "take_profit_pct": optimizer_take_profit_values,
            }

        elif optimizer_strategy == "MACD Crossover":

            optimizer_macd_fast_values = st.multiselect(
                "MACD Fast Periods",
                options=[
                    5,
                    8,
                    10,
                    12,
                    15,
                ],
                default=[
                    8,
                    12,
                ],
                key="optimizer_macd_fast_values",
            )

            optimizer_macd_slow_values = st.multiselect(
                "MACD Slow Periods",
                options=[
                    18,
                    21,
                    26,
                    30,
                    35,
                ],
                default=[
                    21,
                    26,
                    30,
                ],
                key="optimizer_macd_slow_values",
            )

            optimizer_macd_signal_values = st.multiselect(
                "MACD Signal Periods",
                options=[
                    5,
                    7,
                    9,
                    12,
                ],
                default=[
                    7,
                    9,
                ],
                key="optimizer_macd_signal_values",
            )

            optimizer_parameter_grid = {
                "macd_fast": optimizer_macd_fast_values,
                "macd_slow": optimizer_macd_slow_values,
                "macd_signal": optimizer_macd_signal_values,
            }

        elif optimizer_strategy == "Bollinger Mean Reversion":

            optimizer_bollinger_window_values = st.multiselect(
                "Bollinger Windows",
                options=[
                    10,
                    15,
                    20,
                    25,
                    30,
                    40,
                ],
                default=[
                    15,
                    20,
                    25,
                ],
                key="optimizer_bollinger_window_values",
            )

            optimizer_bollinger_std_values = st.multiselect(
                "Bollinger Standard Deviations",
                options=[
                    1.5,
                    1.75,
                    2.0,
                    2.25,
                    2.5,
                    3.0,
                ],
                default=[
                    1.75,
                    2.0,
                    2.25,
                ],
                key="optimizer_bollinger_std_values",
            )

            optimizer_parameter_grid = {
                "bollinger_window": optimizer_bollinger_window_values,
                "bollinger_std": optimizer_bollinger_std_values,
            }

        else:

            optimizer_breakout_window_values = st.multiselect(
                "Breakout Windows",
                options=[
                    5,
                    10,
                    15,
                    20,
                    30,
                    40,
                    50,
                    75,
                ],
                default=[
                    10,
                    20,
                    30,
                    50,
                ],
                key="optimizer_breakout_window_values",
            )

            optimizer_stop_loss_values = st.multiselect(
                "Stop-Loss Values (%)",
                options=[
                    3.0,
                    5.0,
                    8.0,
                    10.0,
                    12.0,
                ],
                default=[
                    5.0,
                    8.0,
                    10.0,
                ],
                key="optimizer_breakout_stop_loss_values",
            )

            optimizer_take_profit_values = st.multiselect(
                "Take-Profit Values (%)",
                options=[
                    8.0,
                    10.0,
                    15.0,
                    20.0,
                    25.0,
                    30.0,
                ],
                default=[
                    10.0,
                    15.0,
                    20.0,
                ],
                key="optimizer_breakout_take_profit_values",
            )

            optimizer_parameter_grid = {
                "breakout_window": optimizer_breakout_window_values,
                "stop_loss_pct": optimizer_stop_loss_values,
                "take_profit_pct": optimizer_take_profit_values,
            }

    optimizer_combination_count = 1

    for optimizer_values in optimizer_parameter_grid.values():
        optimizer_combination_count *= len(optimizer_values)

    optimizer_summary_columns = st.columns(3)

    optimizer_summary_columns[0].metric(
        "Requested Combinations",
        optimizer_combination_count,
    )

    optimizer_summary_columns[1].metric(
        "Maximum Tests",
        optimizer_maximum_tests,
    )

    optimizer_summary_columns[2].metric(
        "Selected Asset",
        ticker,
    )

    run_optimizer_button = st.button(
        f"Optimise {optimizer_strategy}",
        type="primary",
        use_container_width=True,
        key=f"run_optimizer_{ticker}_{optimizer_strategy}",
    )

    if run_optimizer_button:

        if any(
            len(optimizer_values) == 0
            for optimizer_values
            in optimizer_parameter_grid.values()
        ):
            st.warning(
                "Select at least one value for every parameter."
            )

        else:
            with st.spinner(
                f"Testing parameter combinations for {ticker}..."
            ):

                try:
                    optimizer_data = load_asset_data(ticker)

                    optimizer_results = optimise_strategy(
                        data=optimizer_data,
                        strategy_name=optimizer_strategy,
                        initial_capital=float(
                            optimizer_capital
                        ),
                        parameter_grid=optimizer_parameter_grid,
                        maximum_tests=optimizer_maximum_tests,
                    )

                    st.session_state[
                        "strategy_optimizer_results"
                    ] = optimizer_results

                    st.session_state[
                        "strategy_optimizer_ticker"
                    ] = ticker

                except Exception as error:
                    st.error(
                        f"Strategy Optimizer error: {error}"
                    )

    stored_optimizer_results = st.session_state.get(
        "strategy_optimizer_results"
    )

    stored_optimizer_ticker = st.session_state.get(
        "strategy_optimizer_ticker"
    )

    if (
        stored_optimizer_results
        and stored_optimizer_ticker == ticker
    ):

        optimizer_results_dataframe = (
            stored_optimizer_results[
                "results"
            ]
        )

        if optimizer_results_dataframe.empty:

            st.warning(
                "No valid optimisation run was completed."
            )

        else:

            optimizer_best_result = (
                stored_optimizer_results[
                    "best_result"
                ]
            )

            st.success(
                f"Best Configuration — "
                f"Score: "
                f"{safe_float(optimizer_best_result['Optimisation Score']):.1f}/100"
            )

            st.write(
                "**Recommended parameters:** "
                + ", ".join(
                    f"{parameter_name}={parameter_value}"
                    for parameter_name, parameter_value
                    in stored_optimizer_results[
                        "best_parameters"
                    ].items()
                )
            )

            optimizer_metric_columns = st.columns(6)

            optimizer_metric_columns[0].metric(
                "Return",
                f"{safe_float(optimizer_best_result['Return %']):.2f}%",
            )

            optimizer_metric_columns[1].metric(
                "CAGR",
                f"{safe_float(optimizer_best_result['CAGR %']):.2f}%",
            )

            optimizer_metric_columns[2].metric(
                "Sharpe",
                f"{safe_float(optimizer_best_result['Sharpe']):.2f}",
            )

            optimizer_metric_columns[3].metric(
                "Max Drawdown",
                f"{safe_float(optimizer_best_result['Max Drawdown %']):.2f}%",
            )

            optimizer_metric_columns[4].metric(
                "Win Rate",
                f"{safe_float(optimizer_best_result['Win Rate %']):.2f}%",
            )

            optimizer_metric_columns[5].metric(
                "Trades",
                int(
                    safe_float(
                        optimizer_best_result[
                            "Trades"
                        ]
                    )
                ),
            )

            if stored_optimizer_results.get(
                "truncated"
            ):
                st.info(
                    "The requested grid exceeded the maximum-test limit. "
                    "Only the first configured combinations were evaluated."
                )

            st.subheader("Top Optimisation Results")

            optimizer_display_columns = [
                column
                for column
                in optimizer_results_dataframe.columns
                if column not in [
                    "Return Rank",
                    "Sharpe Rank",
                    "Drawdown Rank",
                    "Profit Factor Rank",
                    "Trade Quality Rank",
                ]
            ]

            st.dataframe(
                optimizer_results_dataframe[
                    optimizer_display_columns
                ].head(25),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Final Value": st.column_config.NumberColumn(
                        format="£%.2f"
                    ),
                    "Return %": st.column_config.NumberColumn(
                        format="%+.2f%%"
                    ),
                    "CAGR %": st.column_config.NumberColumn(
                        format="%+.2f%%"
                    ),
                    "Max Drawdown %": st.column_config.NumberColumn(
                        format="%.2f%%"
                    ),
                    "Win Rate %": st.column_config.NumberColumn(
                        format="%.2f%%"
                    ),
                    "Optimisation Score": st.column_config.ProgressColumn(
                        min_value=0,
                        max_value=100,
                        format="%.1f",
                    ),
                },
            )

            optimizer_chart = go.Figure()

            optimizer_chart.add_trace(
                go.Scatter(
                    x=optimizer_results_dataframe[
                        "Max Drawdown %"
                    ],
                    y=optimizer_results_dataframe[
                        "Return %"
                    ],
                    mode="markers",
                    text=optimizer_results_dataframe[
                        "Test"
                    ].map(
                        lambda test_number: (
                            f"Test {int(test_number)}"
                        )
                    ),
                    marker={
                        "size": optimizer_results_dataframe[
                            "Optimisation Score"
                        ].clip(
                            lower=20,
                            upper=100,
                        ) / 4,
                    },
                    hovertemplate=(
                        "%{text}<br>"
                        "Return: %{y:.2f}%<br>"
                        "Drawdown: %{x:.2f}%"
                        "<extra></extra>"
                    ),
                )
            )

            optimizer_chart.update_layout(
                title="Return vs Maximum Drawdown",
                height=460,
                xaxis_title="Maximum Drawdown (%)",
                yaxis_title="Return (%)",
                margin=dict(
                    l=20,
                    r=20,
                    t=60,
                    b=20,
                ),
            )

            st.plotly_chart(
                optimizer_chart,
                use_container_width=True,
            )

            optimizer_csv = (
                optimizer_results_dataframe[
                    optimizer_display_columns
                ]
                .to_csv(index=False)
                .encode("utf-8")
            )

            st.download_button(
                "Download Optimisation Results CSV",
                data=optimizer_csv,
                file_name=(
                    f"tam_tradex_optimizer_"
                    f"{ticker}.csv"
                ),
                mime="text/csv",
                use_container_width=True,
            )

            with st.expander(
                "Optimizer Methodology"
            ):
                st.write(
                    "The ranking score gives 30% weight to Sharpe ratio, "
                    "25% to total return, 25% to drawdown control, "
                    "15% to profit factor and 5% to trade-count quality."
                )

                st.write(
                    f"Completed tests: "
                    f"{stored_optimizer_results['tested_combinations']}."
                )

                st.write(
                    f"Requested combinations: "
                    f"{stored_optimizer_results['requested_combinations']}."
                )

                st.caption(
                    "Optimisation is vulnerable to overfitting. "
                    "Validate the selected configuration on unseen data "
                    "before relying on it."
                )



# ==================================================
# BACKTESTING SCREEN
# ==================================================

elif st.session_state.current_page == "backtest":

    st.header("Strategy Backtesting")

    st.write(
        "Test the current TAM Tradex moving-average and RSI strategy "
        "against historical market data."
    )

    backtest_column1, backtest_column2 = st.columns(2)

    with backtest_column1:

        initial_capital = st.number_input(
            "Initial Capital",
            min_value=100.0,
            value=10_000.0,
            step=500.0,
            key="backtest_initial_capital",
        )

    with backtest_column2:

        st.metric(
            "Selected Asset",
            f"{selected_asset} ({ticker})",
        )

    run_backtest_button = st.button(
        f"Run {ticker} Backtest",
        type="primary",
        use_container_width=True,
        key=f"run_backtest_{ticker}",
    )

    if run_backtest_button:

        with st.spinner(
            f"Running historical backtest for {ticker}..."
        ):

            try:

                backtest_data = load_asset_data(
                    ticker
                )

                if (
                    backtest_data is None
                    or backtest_data.empty
                ):
                    st.error(
                        "No historical market data was returned "
                        "for the selected asset."
                    )
                    st.stop()

                backtest_results = run_backtest(
                    data=backtest_data,
                    initial_capital=initial_capital,
                )

                st.session_state[
                    "latest_backtest_results"
                ] = backtest_results

                st.session_state[
                    "latest_backtest_ticker"
                ] = ticker

            except Exception as error:

                st.error(
                    f"Backtesting error: {error}"
                )

    stored_results = st.session_state.get(
        "latest_backtest_results"
    )

    stored_ticker = st.session_state.get(
        "latest_backtest_ticker"
    )

    if (
        stored_results
        and stored_ticker == ticker
    ):

        st.divider()

        st.subheader(
            f"{ticker} Backtest Results"
        )

        (
            result_column1,
            result_column2,
            result_column3,
            result_column4,
            result_column5,
        ) = st.columns(5)

        result_column1.metric(
            "Initial Capital",
            format_currency(
                safe_float(
                    stored_results[
                        "initial_capital"
                    ]
                )
            ),
        )

        result_column2.metric(
            "Final Value",
            format_currency(
                safe_float(
                    stored_results[
                        "final_portfolio_value"
                    ]
                )
            ),
        )

        result_column3.metric(
            "Strategy Return",
            (
                f"{safe_float(stored_results['strategy_return']):.2f}%"
            ),
        )

        result_column4.metric(
            "Buy-and-Hold Return",
            (
                f"{safe_float(stored_results['buy_and_hold_return']):.2f}%"
            ),
        )

        result_column5.metric(
            "Maximum Drawdown",
            (
                f"{safe_float(stored_results['maximum_drawdown']):.2f}%"
            ),
        )

        (
            statistic_column1,
            statistic_column2,
            statistic_column3,
            statistic_column4,
        ) = st.columns(4)

        statistic_column1.metric(
            "Completed Trades",
            int(
                stored_results[
                    "completed_trades"
                ]
            ),
        )

        statistic_column2.metric(
            "Winning Trades",
            int(
                stored_results[
                    "winning_trades"
                ]
            ),
        )

        statistic_column3.metric(
            "Win Rate",
            (
                f"{safe_float(stored_results['win_rate']):.2f}%"
            ),
        )

        statistic_column4.metric(
            "Sharpe Ratio",
            (
                f"{safe_float(stored_results['sharpe_ratio']):.2f}"
            ),
        )

        if stored_results.get(
            "open_position"
        ):

            st.info(
                "The strategy still holds an open position "
                "at the end of the available historical period."
            )

        st.subheader("Equity Curve")

        equity_curve = stored_results[
            "equity_curve"
        ]

        equity_chart = go.Figure()

        equity_chart.add_trace(
            go.Scatter(
                x=equity_curve.index,
                y=equity_curve[
                    "Portfolio Value"
                ],
                mode="lines",
                name="Strategy Portfolio",
            )
        )

        equity_chart.update_layout(
            title=(
                f"{ticker} Strategy Portfolio Value"
            ),
            height=500,
            xaxis_title="Date",
            yaxis_title="Portfolio Value (£)",
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=20,
            ),
        )

        st.plotly_chart(
            equity_chart,
            use_container_width=True,
        )

        st.subheader("Trade History")

        trade_log = stored_results[
            "trade_log"
        ]

        if (
            trade_log is not None
            and not trade_log.empty
        ):

            st.dataframe(
                trade_log,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "The strategy did not complete any trades "
                "during the selected historical period."
            )

        st.caption(
            "Backtesting uses historical closing prices and does not include "
            "brokerage fees, bid-ask spreads, slippage, taxes or market impact."
        )

    else:

        st.info(
            "Choose an asset and click Run Backtest "
            "to calculate historical strategy performance."
        )


# ==================================================
# SINGLE ASSET ANALYSIS SCREEN
# ==================================================

elif st.session_state.current_page == "analysis":

    with st.spinner(
        f"Downloading {ticker} market data..."
    ):

        try:
            data = load_asset_data(ticker)

        except Exception as error:

            st.error(
                f"Market-data error: {error}"
            )

            st.stop()

    if data is None or data.empty:

        st.error(
            "No market data was received "
            "for the selected asset."
        )

        st.stop()

    try:

        signal, reason = generate_signal(
            data
        )

    except Exception as error:

        st.error(
            f"Strategy error: {error}"
        )

        st.stop()

    latest_price = safe_float(
        data["Close"].iloc[-1]
    )

    previous_price = safe_float(
        data["Close"].iloc[-2]
    )

    latest_short_average = safe_float(
        data["short_average"].iloc[-1]
    )

    latest_long_average = safe_float(
        data["long_average"].iloc[-1]
    )

    latest_rsi = safe_float(
        data["rsi"].iloc[-1]
    )

    price_change = (
        latest_price
        - previous_price
    )

    percentage_change = (
        (
            price_change
            / previous_price
        )
        * 100
        if previous_price != 0
        else 0.0
    )

    try:
        support_resistance = calculate_support_resistance(
            data=data,
            current_price=latest_price,
            lookback=120,
            pivot_window=5,
            max_levels=3,
        )
    except Exception as error:
        support_resistance = {
            "supports": [],
            "resistances": [],
            "nearest_support": None,
            "nearest_resistance": None,
            "support_distance_percentage": None,
            "resistance_distance_percentage": None,
            "breakout_status": "UNAVAILABLE",
        }
        support_resistance_error = str(error)
    else:
        support_resistance_error = None


    # ----------------------------------------------
    # MARKET OVERVIEW
    # ----------------------------------------------

    st.header(
        f"{selected_asset} Market Overview"
    )

    st.caption(
        f"Ticker: {ticker}"
    )

    (
        column1,
        column2,
        column3,
        column4,
    ) = st.columns(4)

    column1.metric(
        label="Latest Price",
        value=format_currency(
            latest_price
        ),
        delta=f"{percentage_change:.2f}%",
    )

    column2.metric(
        label="10-Day Average",
        value=format_currency(
            latest_short_average
        ),
    )

    column3.metric(
        label="30-Day Average",
        value=format_currency(
            latest_long_average
        ),
    )

    column4.metric(
        label="RSI",
        value=f"{latest_rsi:.2f}",
    )


    # ----------------------------------------------
    # PRICE CHART
    # ----------------------------------------------

    st.subheader("Price Chart")

    chart = go.Figure()

    chart.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"].squeeze(),
            high=data["High"].squeeze(),
            low=data["Low"].squeeze(),
            close=data["Close"].squeeze(),
            name="Market Price",
        )
    )

    chart.add_trace(
        go.Scatter(
            x=data.index,
            y=data[
                "short_average"
            ].squeeze(),
            mode="lines",
            name="10-Day Average",
        )
    )

    chart.add_trace(
        go.Scatter(
            x=data.index,
            y=data[
                "long_average"
            ].squeeze(),
            mode="lines",
            name="30-Day Average",
        )
    )

    for support_index, support_level in enumerate(
        support_resistance.get("supports", []),
        start=1,
    ):
        chart.add_hline(
            y=support_level,
            line_dash="dot",
            annotation_text=(
                f"Support {support_index}: "
                f"{format_currency(support_level)}"
            ),
            annotation_position="bottom right",
        )

    for resistance_index, resistance_level in enumerate(
        support_resistance.get("resistances", []),
        start=1,
    ):
        chart.add_hline(
            y=resistance_level,
            line_dash="dash",
            annotation_text=(
                f"Resistance {resistance_index}: "
                f"{format_currency(resistance_level)}"
            ),
            annotation_position="top right",
        )

    chart.update_layout(
        title=(
            f"{ticker} Candlestick Chart"
        ),
        height=600,
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    st.plotly_chart(
        chart,
        use_container_width=True,
    )


    # ----------------------------------------------
    # SUPPORT AND RESISTANCE
    # ----------------------------------------------

    st.subheader("Support and Resistance")

    nearest_support = support_resistance.get("nearest_support")
    nearest_resistance = support_resistance.get("nearest_resistance")
    support_distance = support_resistance.get(
        "support_distance_percentage"
    )
    resistance_distance = support_resistance.get(
        "resistance_distance_percentage"
    )
    breakout_status = support_resistance.get(
        "breakout_status",
        "UNAVAILABLE",
    )

    level_column1, level_column2, level_column3 = st.columns(3)

    level_column1.metric(
        "Nearest Support",
        (
            format_currency(safe_float(nearest_support))
            if nearest_support is not None
            else "Not detected"
        ),
        delta=(
            f"{safe_float(support_distance):.2f}% below price"
            if support_distance is not None
            else None
        ),
    )

    level_column2.metric(
        "Nearest Resistance",
        (
            format_currency(safe_float(nearest_resistance))
            if nearest_resistance is not None
            else "Not detected"
        ),
        delta=(
            f"{safe_float(resistance_distance):.2f}% above price"
            if resistance_distance is not None
            else None
        ),
    )

    level_column3.metric(
        "Price Structure",
        breakout_status,
    )

    if breakout_status == "BULLISH BREAKOUT":
        st.success(
            "Price has closed above the nearest detected resistance level. "
            "Confirm the move with volume and subsequent price action."
        )
    elif breakout_status == "BEARISH BREAKDOWN":
        st.error(
            "Price has closed below the nearest detected support level. "
            "Confirm the move with volume and subsequent price action."
        )
    elif breakout_status == "RANGE-BOUND":
        st.info(
            "Price remains between the nearest detected support and "
            "resistance levels."
        )
    elif support_resistance_error:
        st.warning(
            f"Support and resistance analysis is unavailable: "
            f"{support_resistance_error}"
        )
    else:
        st.info(
            "The recent price history did not produce two-sided levels."
        )

    with st.expander("View all detected levels"):

        detected_rows = []

        for level_number, support_level in enumerate(
            support_resistance.get("supports", []),
            start=1,
        ):
            detected_rows.append(
                {
                    "Type": "Support",
                    "Rank": level_number,
                    "Price": support_level,
                    "Distance from Current Price %": (
                        (latest_price - support_level)
                        / latest_price
                        * 100
                        if latest_price > 0
                        else 0.0
                    ),
                }
            )

        for level_number, resistance_level in enumerate(
            support_resistance.get("resistances", []),
            start=1,
        ):
            detected_rows.append(
                {
                    "Type": "Resistance",
                    "Rank": level_number,
                    "Price": resistance_level,
                    "Distance from Current Price %": (
                        (resistance_level - latest_price)
                        / latest_price
                        * 100
                        if latest_price > 0
                        else 0.0
                    ),
                }
            )

        if detected_rows:
            detected_dataframe = pd.DataFrame(detected_rows)

            st.dataframe(
                detected_dataframe,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Price": st.column_config.NumberColumn(
                        format="£%.2f"
                    ),
                    "Distance from Current Price %": (
                        st.column_config.NumberColumn(
                            format="%.2f%%"
                        )
                    ),
                },
            )
        else:
            st.info("No significant recent levels were detected.")


    # ----------------------------------------------
    # MOMENTUM ANALYSIS
    # ----------------------------------------------

    st.subheader("Momentum Analysis")

    if latest_rsi >= 70:

        st.warning(
            f"RSI is {latest_rsi:.2f}. "
            "The asset may be overbought."
        )

    elif latest_rsi <= 30:

        st.warning(
            f"RSI is {latest_rsi:.2f}. "
            "The asset may be oversold."
        )

    else:

        st.info(
            f"RSI is {latest_rsi:.2f}. "
            "Momentum is within a neutral range."
        )


    # ----------------------------------------------
    # TRADING SIGNAL
    # ----------------------------------------------

    st.subheader("Trading Signal Engine")

    display_signal(signal)

    st.write(
        f"**Strategy explanation:** {reason}"
    )



    # Prepare the current advisor snapshot for trading-journal metadata.
    advisor_risk_key = f"advisor_risk_profile_{ticker}"
    current_advisor_risk_profile = st.session_state.get(
        advisor_risk_key,
        "Balanced",
    )
    advisor_snapshot_portfolio = load_portfolio()
    advisor_snapshot_cash = safe_float(
        advisor_snapshot_portfolio.get("cash", 0.0)
    )
    advisor_snapshot_position = (
        advisor_snapshot_portfolio
        .get("positions", {})
        .get(ticker, {})
    )
    advisor_snapshot_owned_quantity = safe_float(
        advisor_snapshot_position.get("quantity", 0.0)
    )

    try:
        journal_trade_advice = generate_trade_advice(
            data=data,
            ticker=ticker,
            latest_price=latest_price,
            short_average=latest_short_average,
            long_average=latest_long_average,
            rsi=latest_rsi,
            rule_signal=signal,
            available_cash=advisor_snapshot_cash,
            owned_quantity=advisor_snapshot_owned_quantity,
            risk_profile=current_advisor_risk_profile,
        )
    except Exception:
        journal_trade_advice = {
            "recommendation": "UNAVAILABLE",
            "risk_profile": current_advisor_risk_profile,
            "stop_loss": None,
            "take_profit": None,
        }

    # ----------------------------------------------
    # PAPER TRADING
    # ----------------------------------------------

    st.subheader("Paper Trading")

    portfolio = load_portfolio()

    account_column1, account_column2 = (
        st.columns(2)
    )

    account_column1.metric(
        "Available Cash",
        format_currency(
            safe_float(
                portfolio.get(
                    "cash",
                    0.0,
                )
            )
        ),
    )

    account_column2.metric(
        "Realised P/L",
        format_currency(
            safe_float(
                portfolio.get(
                    "realised_pnl",
                    0.0,
                )
            )
        ),
    )

    current_position = (
        calculate_position_metrics(
            ticker=ticker,
            current_price=latest_price,
        )
    )

    if current_position:

        st.write(
            f"### Current {ticker} Position"
        )

        (
            position_column1,
            position_column2,
            position_column3,
            position_column4,
        ) = st.columns(4)

        position_column1.metric(
            "Quantity",
            f"{safe_float(current_position['quantity']):g}",
        )

        position_column2.metric(
            "Average Entry",
            format_currency(
                safe_float(
                    current_position[
                        "average_price"
                    ]
                )
            ),
        )

        position_column3.metric(
            "Market Value",
            format_currency(
                safe_float(
                    current_position[
                        "market_value"
                    ]
                )
            ),
        )

        position_column4.metric(
            "Position Return",
            (
                f"{safe_float(current_position['return_percentage']):.2f}%"
            ),
            delta=format_currency(
                safe_float(
                    current_position[
                        "unrealised_pnl"
                    ]
                )
            ),
        )

    st.write("### Place Simulated Order")

    order_column1, order_column2 = (
        st.columns(2)
    )

    with order_column1:

        st.write("#### Buy Order")

        buy_quantity = st.number_input(
            "Buy Quantity",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key=f"buy_quantity_{ticker}",
        )

        estimated_buy_cost = (
            buy_quantity
            * latest_price
        )

        st.caption(
            "Estimated cost: "
            f"{format_currency(estimated_buy_cost)}"
        )

        buy_notes = st.text_area(
            "Buy Journal Notes",
            placeholder="Why are you entering this trade?",
            key=f"buy_notes_{ticker}",
        )

        st.write("##### Execution Risk Manager")

        execution_risk_profile = st.selectbox(
            "Execution Risk Profile",
            options=[
                "Conservative",
                "Balanced",
                "Aggressive",
            ],
            index=1,
            key=f"execution_risk_profile_{ticker}",
        )

        default_stop_loss = safe_float(
            journal_trade_advice.get(
                "stop_loss",
                0.0,
            )
        )

        default_take_profit = safe_float(
            journal_trade_advice.get(
                "take_profit",
                0.0,
            )
        )

        execution_stop_loss = st.number_input(
            "Order Stop Loss",
            min_value=0.01,
            value=float(
                max(
                    default_stop_loss,
                    0.01,
                )
            ),
            step=0.50,
            key=f"execution_stop_loss_{ticker}",
        )

        execution_take_profit = st.number_input(
            "Order Take Profit",
            min_value=0.01,
            value=float(
                max(
                    default_take_profit,
                    latest_price + 0.01,
                )
            ),
            step=0.50,
            key=f"execution_take_profit_{ticker}",
        )

        execution_portfolio = load_portfolio()

        execution_cash = safe_float(
            execution_portfolio.get(
                "cash",
                0.0,
            )
        )

        execution_positions = execution_portfolio.get(
            "positions",
            {},
        )

        execution_total_market_value = 0.0

        for (
            execution_position_ticker,
            execution_position,
        ) in execution_positions.items():

            try:
                execution_position_data = load_asset_data(
                    execution_position_ticker
                )

                if (
                    execution_position_data is None
                    or execution_position_data.empty
                ):
                    continue

                execution_position_price = get_latest_price(
                    execution_position_data
                )

                execution_position_quantity = safe_float(
                    execution_position.get(
                        "quantity",
                        0.0,
                    )
                )

                execution_total_market_value += (
                    execution_position_quantity
                    * execution_position_price
                )

            except Exception:
                continue

        execution_account_value = (
            execution_cash
            + execution_total_market_value
        )

        execution_current_position = (
            execution_positions.get(
                ticker,
                {},
            )
        )

        execution_current_position_value = (
            safe_float(
                execution_current_position.get(
                    "quantity",
                    0.0,
                )
            )
            * latest_price
        )

        execution_daily_pnl = (
            calculate_daily_realised_pnl(
                execution_portfolio.get(
                    "trade_history",
                    [],
                ),
                current_date_prefix=(
                    datetime.now()
                    .date()
                    .isoformat()
                ),
            )
        )

        execution_review = evaluate_buy_order(
            ticker=ticker,
            quantity=buy_quantity,
            entry_price=latest_price,
            stop_loss=execution_stop_loss,
            take_profit=execution_take_profit,
            account_value=execution_account_value,
            available_cash=execution_cash,
            current_total_market_value=(
                execution_total_market_value
            ),
            current_position_value=(
                execution_current_position_value
            ),
            daily_realised_pnl=execution_daily_pnl,
            risk_profile=execution_risk_profile,
        )

        execution_metrics = st.columns(4)

        execution_metrics[0].metric(
            "Capital at Risk",
            format_currency(
                safe_float(
                    execution_review[
                        "capital_at_risk"
                    ]
                )
            ),
            delta=(
                f"{safe_float(execution_review['risk_per_trade_pct']):.2f}%"
            ),
        )

        execution_metrics[1].metric(
            "Risk/Reward",
            (
                f"{safe_float(execution_review['risk_reward_ratio']):.2f}:1"
            ),
        )

        execution_metrics[2].metric(
            "Position Exposure",
            (
                f"{safe_float(execution_review['position_exposure_pct']):.2f}%"
            ),
        )

        execution_metrics[3].metric(
            "Total Exposure",
            (
                f"{safe_float(execution_review['total_exposure_pct']):.2f}%"
            ),
        )

        st.caption(
            "Maximum suggested quantity under the current "
            f"risk limits: "
            f"{safe_float(execution_review['suggested_max_quantity']):.4f}"
        )

        if execution_review["approved"]:
            st.success(
                "Execution Risk Decision: APPROVED"
            )
        else:
            st.error(
                "Execution Risk Decision: BLOCKED"
            )

        with st.expander(
            "View Risk Checks",
            expanded=not execution_review[
                "approved"
            ],
        ):

            for risk_check in execution_review[
                "checks"
            ]:

                risk_check_message = (
                    f"**{risk_check['name']}:** "
                    f"{risk_check['message']}"
                )

                if risk_check["passed"]:
                    st.success(
                        risk_check_message
                    )
                else:
                    st.error(
                        risk_check_message
                    )

            profile_limits = execution_review[
                "profile_limits"
            ]

            st.caption(
                f"Profile limits — Risk/trade: "
                f"{profile_limits['risk_per_trade_pct']:.2f}% | "
                f"Position: {profile_limits['max_position_pct']:.2f}% | "
                f"Total exposure: "
                f"{profile_limits['max_total_exposure_pct']:.2f}% | "
                f"Minimum R/R: "
                f"{profile_limits['minimum_risk_reward']:.2f}:1 | "
                f"Daily loss: "
                f"{profile_limits['daily_loss_limit_pct']:.2f}%"
            )

        buy_button = st.button(
            f"Buy {ticker}",
            use_container_width=True,
            key=f"buy_button_{ticker}",
            disabled=not execution_review[
                "approved"
            ],
        )

        if buy_button:

            success, message = buy_asset(
                ticker=ticker,
                quantity=buy_quantity,
                price=latest_price,
                strategy_signal=signal,
                strategy_reason=reason,
                ai_recommendation=journal_trade_advice.get(
                    "recommendation",
                    "UNAVAILABLE",
                ),
                risk_profile=execution_risk_profile,
                stop_loss=execution_stop_loss,
                take_profit=execution_take_profit,
                notes=buy_notes,
            )

            if success:

                st.success(message)

                st.rerun()

            else:

                st.error(message)

    with order_column2:

        st.write("#### Sell Order")

        owned_quantity = 0.0

        if current_position:

            owned_quantity = safe_float(
                current_position[
                    "quantity"
                ]
            )

        if owned_quantity > 0:

            sell_quantity = st.number_input(
                "Sell Quantity",
                min_value=0.0,
                max_value=float(
                    owned_quantity
                ),
                value=0.0,
                step=1.0,
                key=f"sell_quantity_{ticker}",
            )

        else:

            sell_quantity = st.number_input(
                "Sell Quantity",
                min_value=0.0,
                value=0.0,
                step=1.0,
                disabled=True,
                key=f"sell_quantity_{ticker}",
            )

        estimated_sale_value = (
            sell_quantity
            * latest_price
        )

        st.caption(
            "Estimated proceeds: "
            f"{format_currency(estimated_sale_value)}"
        )

        sell_notes = st.text_area(
            "Sell Journal Notes",
            placeholder="Why are you exiting this trade?",
            key=f"sell_notes_{ticker}",
            disabled=owned_quantity <= 0,
        )

        sell_button = st.button(
            f"Sell {ticker}",
            use_container_width=True,
            key=f"sell_button_{ticker}",
            disabled=owned_quantity <= 0,
        )

        if sell_button:

            success, message = sell_asset(
                ticker=ticker,
                quantity=sell_quantity,
                price=latest_price,
                strategy_signal=signal,
                strategy_reason=reason,
                ai_recommendation=journal_trade_advice.get(
                    "recommendation",
                    "UNAVAILABLE",
                ),
                risk_profile=journal_trade_advice.get(
                    "risk_profile",
                    current_advisor_risk_profile,
                ),
                stop_loss=journal_trade_advice.get("stop_loss"),
                take_profit=journal_trade_advice.get("take_profit"),
                notes=sell_notes,
            )

            if success:

                st.success(message)

                st.rerun()

            else:

                st.error(message)


    # ----------------------------------------------
    # COMPANY NEWS
    # ----------------------------------------------

    st.subheader("Latest Market News")

    if ticker in [
        "BTC-USD",
        "ETH-USD",
    ]:

        st.info(
            "Company-specific Finnhub news "
            "is currently enabled for listed equities only."
        )

    else:

        with st.spinner(
            f"Loading recent {ticker} news..."
        ):

            try:

                news_articles = (
                    get_company_news(
                        symbol=ticker,
                        days=7,
                        limit=5,
                    )
                )

            except Exception as error:

                news_articles = []

                st.warning(
                    f"News service error: {error}"
                )

        if news_articles:

            for article in news_articles:

                headline = article.get(
                    "headline",
                    "Untitled article",
                )

                source = article.get(
                    "source",
                    "Unknown source",
                )

                summary = article.get(
                    "summary",
                    "",
                )

                article_url = article.get(
                    "url",
                    "",
                )

                with st.container(
                    border=True
                ):

                    st.markdown(
                        f"### {headline}"
                    )

                    st.caption(
                        f"Source: {source}"
                    )

                    if summary:

                        st.write(summary)

                    if article_url:

                        st.link_button(
                            "Read Full Article",
                            article_url,
                        )

        else:

            st.warning(
                "No recent news was returned. "
                "Check the Finnhub API key "
                "or try another stock."
            )


    # ----------------------------------------------
    # AI ANALYSIS
    # ----------------------------------------------

    st.subheader(
        "TAM Tradex AI Analysis"
    )

    with st.spinner(
        "AI is analysing the market..."
    ):

        try:

            ai_analysis = get_ai_analysis(
                ticker=ticker,
                latest_price=latest_price,
                short_average=(
                    latest_short_average
                ),
                long_average=(
                    latest_long_average
                ),
                rsi=latest_rsi,
                rule_signal=signal,
            )

            st.info(ai_analysis)

        except Exception as error:

            st.error(
                f"AI analysis error: {error}"
            )


    # ----------------------------------------------
    # AI TRADE ADVISOR
    # ----------------------------------------------

    st.subheader("AI Trade Advisor")

    st.caption(
        "Risk-aware decision support using trend, RSI, volatility, "
        "ATR and your paper-trading cash."
    )

    risk_profile = st.selectbox(
        "Risk Profile",
        options=[
            "Conservative",
            "Balanced",
            "Aggressive",
        ],
        index=1,
        key=f"advisor_risk_profile_{ticker}",
    )

    advisor_portfolio = load_portfolio()

    advisor_cash = safe_float(
        advisor_portfolio.get(
            "cash",
            0.0,
        )
    )

    advisor_owned_quantity = 0.0

    advisor_position = (
        advisor_portfolio
        .get(
            "positions",
            {},
        )
        .get(
            ticker,
            {},
        )
    )

    if advisor_position:

        advisor_owned_quantity = safe_float(
            advisor_position.get(
                "quantity",
                0.0,
            )
        )

    try:

        trade_advice = generate_trade_advice(
            data=data,
            ticker=ticker,
            latest_price=latest_price,
            short_average=latest_short_average,
            long_average=latest_long_average,
            rsi=latest_rsi,
            rule_signal=signal,
            available_cash=advisor_cash,
            owned_quantity=advisor_owned_quantity,
            risk_profile=risk_profile,
        )

        recommendation = trade_advice[
            "recommendation"
        ]

        if recommendation == "BUY":
            st.success(
                f"Advisor Recommendation: {recommendation}"
            )
        elif recommendation in [
            "REDUCE",
            "AVOID",
        ]:
            st.error(
                f"Advisor Recommendation: {recommendation}"
            )
        else:
            st.warning(
                f"Advisor Recommendation: {recommendation}"
            )

        (
            advisor_column1,
            advisor_column2,
            advisor_column3,
            advisor_column4,
        ) = st.columns(4)

        advisor_column1.metric(
            "Confidence",
            f"{safe_float(trade_advice['confidence']):.1f}%",
        )

        advisor_column2.metric(
            "Risk Level",
            trade_advice[
                "risk_level"
            ],
        )

        advisor_column3.metric(
            "Suggested Allocation",
            (
                f"{safe_float(trade_advice['suggested_allocation_percentage']):.2f}%"
            ),
        )

        advisor_column4.metric(
            "Suggested Quantity",
            (
                f"{safe_float(trade_advice['suggested_quantity']):g}"
            ),
        )

        (
            risk_column1,
            risk_column2,
            risk_column3,
            risk_column4,
        ) = st.columns(4)

        risk_column1.metric(
            "Stop Loss",
            format_currency(
                safe_float(
                    trade_advice[
                        "stop_loss"
                    ]
                )
            ),
        )

        risk_column2.metric(
            "Take Profit",
            format_currency(
                safe_float(
                    trade_advice[
                        "take_profit"
                    ]
                )
            ),
        )

        risk_column3.metric(
            "Risk/Reward",
            (
                f"{safe_float(trade_advice['risk_reward_ratio']):.2f}:1"
            ),
        )

        risk_column4.metric(
            "Annualised Volatility",
            (
                f"{safe_float(trade_advice['annualised_volatility']):.2f}%"
            ),
        )

        st.write(
            "**Suggested position value:** "
            f"{format_currency(safe_float(trade_advice['suggested_position_value']))}"
        )

        with st.expander(
            "Why the advisor produced this recommendation",
            expanded=True,
        ):

            for advisor_reason in trade_advice[
                "reasons"
            ]:

                st.write(
                    f"- {advisor_reason}"
                )

            st.caption(
                f"ATR: {format_currency(safe_float(trade_advice['atr']))} | "
                f"Trend gap: {safe_float(trade_advice['trend_gap_percentage']):.2f}% | "
                f"Risk profile: {trade_advice['risk_profile']}"
            )

        st.warning(
            "This output is a simulation and decision-support estimate. "
            "It is not personalised financial advice and does not guarantee returns."
        )

    except Exception as error:

        st.exception(error)


    # ----------------------------------------------
    # RAW MARKET DATA
    # ----------------------------------------------

    with st.expander(
        "View Recent Market Data"
    ):

        requested_columns = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "short_average",
            "long_average",
            "rsi",
        ]

        available_columns = [
            column
            for column
            in requested_columns
            if column in data.columns
        ]

        recent_data = data[
            available_columns
        ].tail(20)

        st.dataframe(
            recent_data,
            use_container_width=True,
        )

    st.divider()

    st.caption(
        "TAM Tradex provides market analysis "
        "for educational, research and simulation purposes. "
        "It does not provide personalised financial advice."
    )


# ==================================================
# HOME SCREEN
# ==================================================

else:

    st.markdown(
        """
        <style>
        .tam-hero {
            padding: 18px 20px;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 20px;
            background:
                radial-gradient(circle at top right, rgba(59, 130, 246, 0.14), transparent 34%),
                linear-gradient(145deg, rgba(17, 24, 39, 0.98), rgba(8, 15, 28, 0.98));
            margin-bottom: 18px;
        }
        .tam-eyebrow {
            color: #60a5fa;
            font-size: 0.76rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            margin-bottom: 7px;
        }
        .tam-hero-title {
            color: #f8fafc;
            font-size: 1.45rem;
            font-weight: 800;
            margin-bottom: 8px;
        }
        .tam-hero-copy {
            color: #94a3b8;
            font-size: 0.82rem;
            max-width: 780px;
            line-height: 1.55;
        }
        .tam-section-label {
            color: #cbd5e1;
            font-size: 0.8rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin: 12px 0 10px 0;
        }
        .tam-action-card {
            min-height: 132px;
            padding: 18px 18px 16px 18px;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 16px;
            background: linear-gradient(
                145deg,
                rgba(21, 30, 45, 0.98),
                rgba(11, 18, 30, 0.98)
            );
            box-shadow: 0 10px 26px rgba(0, 0, 0, 0.16);
            margin-bottom: 8px;
        }
        .tam-action-icon {
            font-size: 1.65rem;
            margin-bottom: 10px;
        }
        .tam-action-title {
            color: #f8fafc;
            font-size: 1.03rem;
            font-weight: 800;
            margin-bottom: 7px;
        }
        .tam-action-copy {
            color: #94a3b8;
            font-size: 0.84rem;
            line-height: 1.45;
        }
        .tam-status-card {
            padding: 16px 17px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 15px;
            background: rgba(15, 23, 42, 0.72);
            margin-bottom: 10px;
        }
        .tam-status-label {
            color: #94a3b8;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            margin-bottom: 5px;
        }
        .tam-status-value {
            color: #f8fafc;
            font-size: 1.32rem;
            font-weight: 800;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="tam-hero">
            <div class="tam-eyebrow">TAM Tradex Command Centre</div>
            <div class="tam-hero-title">Markets, portfolio and AI intelligence in one workspace</div>
            <div class="tam-hero-copy">
                Review your paper portfolio, inspect live market conditions,
                track decision signals and launch the core trading tools from
                a single professional dashboard.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------
    # PORTFOLIO SNAPSHOT
    # --------------------------------------------------

    home_portfolio = load_portfolio()
    home_positions = home_portfolio.get("positions", {})
    home_cash = safe_float(home_portfolio.get("cash", 0.0))
    home_realised_pnl = safe_float(
        home_portfolio.get("realised_pnl", 0.0)
    )

    home_position_rows = []
    home_market_value = 0.0
    home_unrealised_pnl = 0.0

    if home_positions:

        with st.spinner("Updating command-centre data..."):

            for home_ticker, home_position in home_positions.items():

                try:
                    home_data = load_asset_data(home_ticker)

                    if home_data is None or home_data.empty:
                        continue

                    home_current_price = get_latest_price(home_data)
                    home_quantity = safe_float(
                        home_position.get("quantity", 0.0)
                    )
                    home_average_price = safe_float(
                        home_position.get("average_price", 0.0)
                    )

                    home_position_value = (
                        home_quantity * home_current_price
                    )

                    home_position_cost = (
                        home_quantity * home_average_price
                    )

                    home_position_pnl = (
                        home_position_value - home_position_cost
                    )

                    home_position_return = (
                        home_position_pnl
                        / home_position_cost
                        * 100
                        if home_position_cost > 0
                        else 0.0
                    )

                    home_market_value += home_position_value
                    home_unrealised_pnl += home_position_pnl

                    home_position_rows.append(
                        {
                            "Ticker": home_ticker,
                            "Quantity": home_quantity,
                            "Current Price": home_current_price,
                            "Market Value": home_position_value,
                            "Unrealised P/L": home_position_pnl,
                            "Return %": home_position_return,
                        }
                    )

                except Exception:
                    continue

    home_account_value = home_cash + home_market_value
    home_total_return_value = home_account_value - STARTING_CASH

    home_total_return_percentage = (
        home_total_return_value
        / STARTING_CASH
        * 100
        if STARTING_CASH > 0
        else 0.0
    )

    home_trade_history = home_portfolio.get(
        "trade_history",
        [],
    )

    home_closed_trades = home_portfolio.get(
        "closed_trades",
        [],
    )

    home_win_rate = 0.0

    if home_closed_trades:
        home_winning_trades = sum(
            1
            for trade in home_closed_trades
            if safe_float(
                trade.get("realised_pnl", 0.0)
            ) > 0
        )

        home_win_rate = (
            home_winning_trades
            / len(home_closed_trades)
            * 100
        )

    kpi_columns = st.columns(6)

    kpi_columns[0].metric(
        "Portfolio Value",
        format_currency(home_account_value),
        delta=format_currency(home_total_return_value),
    )

    kpi_columns[1].metric(
        "Total Return",
        f"{home_total_return_percentage:.2f}%",
    )

    kpi_columns[2].metric(
        "Available Cash",
        format_currency(home_cash),
    )

    kpi_columns[3].metric(
        "Unrealised P/L",
        format_currency(home_unrealised_pnl),
    )

    kpi_columns[4].metric(
        "Open Positions",
        len(home_position_rows),
    )

    kpi_columns[5].metric(
        "Win Rate",
        f"{home_win_rate:.1f}%",
    )

    st.divider()

    # --------------------------------------------------
    # MARKET + AI SNAPSHOT
    # --------------------------------------------------

    market_panel, ai_panel = st.columns([1.45, 1])

    with market_panel:

        st.subheader("Market Overview")

        try:
            home_selected_data = load_asset_data(ticker)

            if (
                home_selected_data is not None
                and not home_selected_data.empty
            ):

                home_latest_price = get_latest_price(
                    home_selected_data
                )

                home_previous_price = safe_float(
                    home_selected_data["Close"].iloc[-2]
                )

                home_daily_change = (
                    (
                        home_latest_price
                        - home_previous_price
                    )
                    / home_previous_price
                    * 100
                    if home_previous_price != 0
                    else 0.0
                )

                home_signal, home_signal_reason = generate_signal(
                    home_selected_data
                )

                home_rsi = safe_float(
                    home_selected_data["rsi"].iloc[-1]
                )

                home_short_average = safe_float(
                    home_selected_data[
                        "short_average"
                    ].iloc[-1]
                )

                home_long_average = safe_float(
                    home_selected_data[
                        "long_average"
                    ].iloc[-1]
                )

                market_metrics = st.columns(4)

                market_metrics[0].metric(
                    "Asset",
                    ticker,
                )

                market_metrics[1].metric(
                    "Latest Price",
                    format_currency(home_latest_price),
                    delta=f"{home_daily_change:.2f}%",
                )

                market_metrics[2].metric(
                    "RSI",
                    f"{home_rsi:.1f}",
                )

                market_metrics[3].metric(
                    "Signal",
                    home_signal,
                )

                home_market_chart = go.Figure()

                home_market_chart.add_trace(
                    go.Scatter(
                        x=home_selected_data.index,
                        y=home_selected_data["Close"].squeeze(),
                        mode="lines",
                        name="Close",
                    )
                )

                home_market_chart.add_trace(
                    go.Scatter(
                        x=home_selected_data.index,
                        y=home_selected_data[
                            "short_average"
                        ].squeeze(),
                        mode="lines",
                        name="10-Day Average",
                    )
                )

                home_market_chart.add_trace(
                    go.Scatter(
                        x=home_selected_data.index,
                        y=home_selected_data[
                            "long_average"
                        ].squeeze(),
                        mode="lines",
                        name="30-Day Average",
                    )
                )

                home_market_chart.update_layout(
                    height=330,
                    xaxis_title="",
                    yaxis_title="Price",
                    margin=dict(
                        l=20,
                        r=20,
                        t=20,
                        b=20,
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                    ),
                )

                st.plotly_chart(
                    home_market_chart,
                    use_container_width=True,
                )

            else:
                st.info(
                    "No current market data is available."
                )

        except Exception as error:
            st.warning(
                f"Market overview unavailable: {error}"
            )

    with ai_panel:

        st.subheader("AI Decision Support")

        if "home_signal" in locals():

            if home_signal == "BUY":
                st.success(
                    f"Rule Signal: {home_signal}"
                )
            elif home_signal == "SELL":
                st.error(
                    f"Rule Signal: {home_signal}"
                )
            else:
                st.warning(
                    f"Rule Signal: {home_signal}"
                )

            st.write(
                f"**Signal rationale:** {home_signal_reason}"
            )

            try:
                home_advice = generate_trade_advice(
                    data=home_selected_data,
                    ticker=ticker,
                    latest_price=home_latest_price,
                    short_average=home_short_average,
                    long_average=home_long_average,
                    rsi=home_rsi,
                    rule_signal=home_signal,
                    available_cash=home_cash,
                    owned_quantity=safe_float(
                        home_positions
                        .get(ticker, {})
                        .get("quantity", 0.0)
                    ),
                    risk_profile="Balanced",
                )

                st.metric(
                    "Advisor Recommendation",
                    home_advice.get(
                        "recommendation",
                        "UNAVAILABLE",
                    ),
                    delta=(
                        f"{safe_float(home_advice.get('confidence', 0.0)):.1f}% confidence"
                    ),
                )

                ai_metrics = st.columns(2)

                ai_metrics[0].metric(
                    "Risk Level",
                    home_advice.get(
                        "risk_level",
                        "Unavailable",
                    ),
                )

                ai_metrics[1].metric(
                    "Suggested Allocation",
                    (
                        f"{safe_float(home_advice.get('suggested_allocation_percentage', 0.0)):.2f}%"
                    ),
                )

                st.write(
                    "**Stop loss:** "
                    f"{format_currency(safe_float(home_advice.get('stop_loss', 0.0)))}"
                )

                st.write(
                    "**Take profit:** "
                    f"{format_currency(safe_float(home_advice.get('take_profit', 0.0)))}"
                )

                st.write(
                    "**Risk/reward:** "
                    f"{safe_float(home_advice.get('risk_reward_ratio', 0.0)):.2f}:1"
                )

            except Exception as error:
                st.info(
                    f"Advisor snapshot unavailable: {error}"
                )

        st.caption(
            "Educational decision support only; not personalised financial advice."
        )

    st.divider()

    # --------------------------------------------------
    # QUICK ACTIONS - 2 ROWS x 3 COLUMNS
    # --------------------------------------------------

    st.markdown(
        '<div class="tam-section-label">Quick Actions</div>',
        unsafe_allow_html=True,
    )

    quick_actions = [
        {
            "icon": "📈",
            "title": "Asset Analysis",
            "copy": "Open price charts, support and resistance, RSI, signals, AI analysis and paper trading.",
            "button": "Open Asset Analysis",
            "page": "analysis",
        },
        {
            "icon": "💼",
            "title": "Portfolio",
            "copy": "Review open positions, current values, unrealised P/L, realised P/L and trading history.",
            "button": "Open Portfolio",
            "page": "portfolio",
        },
        {
            "icon": "🧪",
            "title": "Strategy Lab",
            "copy": "Compare strategies, optimise parameters and inspect risk-adjusted performance.",
            "button": "Open Strategy Lab",
            "page": "strategy_lab",
        },
        {
            "icon": "⭐",
            "title": "Watchlist",
            "copy": "Track selected symbols, daily change, RSI, trend and BUY, HOLD or SELL signals.",
            "button": "Open Watchlist",
            "page": "watchlist",
        },
        {
            "icon": "📓",
            "title": "Trading Journal",
            "copy": "Review completed trades, win rate, profit factor, notes and cumulative realised performance.",
            "button": "Open Trading Journal",
            "page": "journal",
        },
        {
            "icon": "📊",
            "title": "Portfolio Analytics",
            "copy": "Inspect allocation, concentration, diversification, risk score and rebalancing diagnostics.",
            "button": "Open Portfolio Analytics",
            "page": "portfolio_analytics",
        },
    ]

    for row_start in range(0, len(quick_actions), 3):

        action_columns = st.columns(3)

        for column, action in zip(
            action_columns,
            quick_actions[row_start:row_start + 3],
        ):

            with column:

                st.markdown(
                    f"""
                    <div class="tam-action-card">
                        <div class="tam-action-icon">{action['icon']}</div>
                        <div class="tam-action-title">{action['title']}</div>
                        <div class="tam-action-copy">{action['copy']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    action["button"],
                    use_container_width=True,
                    key=f"home_action_{action['page']}",
                ):
                    st.session_state.current_page = action["page"]
                    st.rerun()

    st.divider()

    # --------------------------------------------------
    # PORTFOLIO + WATCHLIST
    # --------------------------------------------------

    portfolio_panel, watchlist_panel = st.columns(2)

    with portfolio_panel:

        st.subheader("Portfolio Snapshot")

        if home_position_rows:

            home_positions_dataframe = pd.DataFrame(
                home_position_rows
            ).sort_values(
                "Market Value",
                ascending=False,
            )

            st.dataframe(
                home_positions_dataframe,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Quantity": st.column_config.NumberColumn(
                        format="%.4f"
                    ),
                    "Current Price": st.column_config.NumberColumn(
                        format="£%.2f"
                    ),
                    "Market Value": st.column_config.NumberColumn(
                        format="£%.2f"
                    ),
                    "Unrealised P/L": st.column_config.NumberColumn(
                        format="£%.2f"
                    ),
                    "Return %": st.column_config.NumberColumn(
                        format="%+.2f%%"
                    ),
                },
            )

            portfolio_chart = go.Figure(
                data=[
                    go.Pie(
                        labels=home_positions_dataframe[
                            "Ticker"
                        ],
                        values=home_positions_dataframe[
                            "Market Value"
                        ],
                        hole=0.55,
                    )
                ]
            )

            portfolio_chart.update_layout(
                height=330,
                margin=dict(
                    l=20,
                    r=20,
                    t=20,
                    b=20,
                ),
            )

            st.plotly_chart(
                portfolio_chart,
                use_container_width=True,
            )

        else:
            st.info(
                "No open paper-trading positions."
            )

    with watchlist_panel:

        st.subheader("Watchlist Signals")

        home_watchlist_rows = []

        for home_watchlist_ticker in load_watchlist()[:8]:

            try:
                home_watchlist_data = load_asset_data(
                    home_watchlist_ticker
                )

                if (
                    home_watchlist_data is None
                    or home_watchlist_data.empty
                ):
                    continue

                home_watchlist_signal, _ = generate_signal(
                    home_watchlist_data
                )

                home_watchlist_price = get_latest_price(
                    home_watchlist_data
                )

                home_watchlist_previous = safe_float(
                    home_watchlist_data[
                        "Close"
                    ].iloc[-2]
                )

                home_watchlist_change = (
                    (
                        home_watchlist_price
                        - home_watchlist_previous
                    )
                    / home_watchlist_previous
                    * 100
                    if home_watchlist_previous != 0
                    else 0.0
                )

                home_watchlist_rows.append(
                    {
                        "Ticker": home_watchlist_ticker,
                        "Price": home_watchlist_price,
                        "Daily Change %": home_watchlist_change,
                        "RSI": safe_float(
                            home_watchlist_data[
                                "rsi"
                            ].iloc[-1]
                        ),
                        "Signal": home_watchlist_signal,
                    }
                )

            except Exception:
                continue

        if home_watchlist_rows:

            home_watchlist_dataframe = pd.DataFrame(
                home_watchlist_rows
            )

            st.dataframe(
                home_watchlist_dataframe,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Price": st.column_config.NumberColumn(
                        format="£%.2f"
                    ),
                    "Daily Change %": st.column_config.NumberColumn(
                        format="%+.2f%%"
                    ),
                    "RSI": st.column_config.NumberColumn(
                        format="%.1f"
                    ),
                },
            )

            signal_counts = (
                home_watchlist_dataframe[
                    "Signal"
                ]
                .value_counts()
            )

            signal_chart = go.Figure()

            signal_chart.add_trace(
                go.Bar(
                    x=signal_counts.index,
                    y=signal_counts.values,
                    text=signal_counts.values,
                    textposition="auto",
                )
            )

            signal_chart.update_layout(
                title="Signal Distribution",
                height=330,
                xaxis_title="Signal",
                yaxis_title="Assets",
                margin=dict(
                    l=20,
                    r=20,
                    t=60,
                    b=20,
                ),
            )

            st.plotly_chart(
                signal_chart,
                use_container_width=True,
            )

        else:
            st.info(
                "No watchlist data is currently available."
            )

    st.divider()

    # --------------------------------------------------
    # RECENT TRADING ACTIVITY
    # --------------------------------------------------

    st.subheader("Recent Trading Activity")

    if home_trade_history:

        recent_activity = pd.DataFrame(
            home_trade_history[-8:]
        ).iloc[::-1]

        st.dataframe(
            recent_activity,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info(
            "No paper-trading activity has been recorded yet."
        )

    st.caption(
        "TAM Tradex is an educational and simulated trading platform. "
        "It does not provide personalised financial advice."
    )


# ==================================================
# GLOBAL STATUS BAR
# ==================================================

#render_status_bar(
 #   current_page=st.session_state.current_page,
    #selected_ticker=ticker,
   # market_connected=True,
#)