from datetime import datetime
from typing import Any

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st


APP_VERSION = "3.1"


# ==================================================
# PLOTLY THEME
# ==================================================

def apply_plotly_theme() -> None:
    """
    Apply the global TAM Tradex Plotly theme.

    This affects Plotly charts created after this function is called.
    """

    template = go.layout.Template()

    template.layout = go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Inter, Segoe UI, Arial, sans-serif",
            "color": "#d6d3c8",
            "size": 12,
        },
        title={
            "font": {
                "family": "Inter, Segoe UI, Arial, sans-serif",
                "color": "#f4f1e8",
                "size": 18,
            }
        },
        colorway=[
            "#d6a94f",
            "#5e9ed6",
            "#5dbb8a",
            "#c97575",
            "#9c82d4",
            "#d48c55",
        ],
        xaxis={
            "gridcolor": "rgba(148, 163, 184, 0.10)",
            "linecolor": "rgba(148, 163, 184, 0.20)",
            "zerolinecolor": "rgba(148, 163, 184, 0.16)",
            "tickfont": {
                "color": "#99968d",
            },
            "title": {
                "font": {
                    "color": "#b9b3a7",
                }
            },
        },
        yaxis={
            "gridcolor": "rgba(148, 163, 184, 0.10)",
            "linecolor": "rgba(148, 163, 184, 0.20)",
            "zerolinecolor": "rgba(148, 163, 184, 0.16)",
            "tickfont": {
                "color": "#99968d",
            },
            "title": {
                "font": {
                    "color": "#b9b3a7",
                }
            },
        },
        legend={
            "bgcolor": "rgba(0,0,0,0)",
            "font": {
                "color": "#b9b3a7",
            },
        },
        hoverlabel={
            "bgcolor": "#1a1915",
            "bordercolor": "#4d483c",
            "font": {
                "color": "#f4f1e8",
            },
        },
        margin={
            "l": 40,
            "r": 30,
            "t": 55,
            "b": 40,
        },
    )

    pio.templates["tam_tradex"] = template
    pio.templates.default = "tam_tradex"


# ==================================================
# GLOBAL CSS
# ==================================================

def inject_global_css() -> None:
    """
    Inject the global TAM Tradex Streamlit styling.
    """

    st.markdown(
        """
        <style>

        /* ==========================================
           DESIGN TOKENS
           ========================================== */

        :root {
            --tam-bg: #0d0c09;
            --tam-panel: #151410;
            --tam-panel-soft: #1a1915;
            --tam-panel-raised: #201e19;

            --tam-text: #f4f1e8;
            --tam-soft: #d6d3c8;
            --tam-muted: #99968d;

            --tam-border: rgba(214, 169, 79, 0.18);
            --tam-border-soft: rgba(148, 163, 184, 0.14);

            --tam-amber: #d6a94f;
            --tam-amber-soft: #f0c96d;

            --tam-green: #61c58b;
            --tam-red: #df7474;
            --tam-blue: #67a8df;

            --tam-radius-sm: 8px;
            --tam-radius-md: 12px;
            --tam-radius-lg: 16px;

            --tam-shadow:
                0 16px 38px rgba(0, 0, 0, 0.22);
        }


        /* ==========================================
           STREAMLIT APPLICATION
           ========================================== */

        html,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            background:
                radial-gradient(
                    circle at 85% 0%,
                    rgba(214, 169, 79, 0.055),
                    transparent 30%
                ),
                linear-gradient(
                    180deg,
                    #0d0c09 0%,
                    #11100c 100%
                );
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1500px;
            padding-top: 1.4rem;
            padding-bottom: 3rem;
        }

        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stDecoration"] {
            display: none;
        }


        /* ==========================================
           TYPOGRAPHY
           ========================================== */

        h1,
        h2,
        h3,
        h4 {
            color: var(--tam-text) !important;
            letter-spacing: -0.015em;
        }

        p,
        label,
        .stMarkdown,
        [data-testid="stCaptionContainer"] {
            color: var(--tam-soft);
        }

        a {
            color: var(--tam-amber-soft) !important;
        }

        code {
            color: var(--tam-amber-soft);
            background: rgba(214, 169, 79, 0.08);
            border: 1px solid rgba(214, 169, 79, 0.14);
            border-radius: 5px;
        }


        /* ==========================================
           APPLICATION HEADING
           ========================================== */

        .tam-app-heading {
            display: grid;
            grid-template-columns:
                minmax(0, 1fr)
                minmax(170px, auto);

            align-items: end;
            gap: 1.25rem;

            margin-bottom: 1.4rem;
            padding: 1.15rem 1.25rem;

            background:
                linear-gradient(
                    135deg,
                    rgba(30, 28, 22, 0.98),
                    rgba(18, 17, 13, 0.98)
                );

            border: 1px solid var(--tam-border);
            border-left: 3px solid var(--tam-amber);
            border-radius: var(--tam-radius-md);

            box-shadow: var(--tam-shadow);
        }

        .tam-app-kicker {
            margin-bottom: 0.35rem;

            color: var(--tam-amber);
            font-family:
                "Cascadia Mono",
                Consolas,
                monospace;

            font-size: 0.65rem;
            font-weight: 800;

            letter-spacing: 0.16em;
            text-transform: uppercase;
        }

        .tam-app-title {
            color: var(--tam-text);

            font-size: clamp(1.55rem, 3vw, 2.25rem);
            font-weight: 780;

            line-height: 1.05;
            letter-spacing: -0.035em;
        }

        .tam-app-subtitle {
            margin-top: 0.42rem;

            color: var(--tam-muted);
            font-size: 0.82rem;
            line-height: 1.45;
        }

        .tam-app-meta {
            color: var(--tam-muted);

            font-family:
                "Cascadia Mono",
                Consolas,
                monospace;

            font-size: 0.63rem;
            line-height: 1.7;

            text-align: right;
            letter-spacing: 0.08em;
        }


        /* ==========================================
           SIDEBAR
           ========================================== */

        section[data-testid="stSidebar"] {
            background:
                linear-gradient(
                    180deg,
                    #12110d 0%,
                    #0d0c09 100%
                );

            border-right: 1px solid var(--tam-border);
        }

        section[data-testid="stSidebar"]
        [data-testid="stSidebarContent"] {
            padding-top: 1.15rem;
        }

        .tam-sidebar-brand {
            margin-bottom: 1rem;
            padding: 0.85rem 0.75rem;

            background: rgba(214, 169, 79, 0.04);
            border: 1px solid rgba(214, 169, 79, 0.14);
            border-radius: var(--tam-radius-md);
        }

        .tam-sidebar-mark {
            display: inline-block;

            width: 8px;
            height: 8px;

            margin-right: 0.45rem;

            background: var(--tam-amber);
            border-radius: 50%;

            box-shadow:
                0 0 12px rgba(214, 169, 79, 0.65);
        }

        .tam-sidebar-name {
            color: var(--tam-text);
            font-size: 1rem;
            font-weight: 780;
        }

        .tam-sidebar-caption {
            margin-top: 0.35rem;

            color: var(--tam-muted);
            font-size: 0.7rem;
            line-height: 1.45;
        }

        .tam-sidebar-section {
            margin: 0.9rem 0 0.35rem;

            color: var(--tam-amber);

            font-size: 0.62rem;
            font-weight: 800;

            letter-spacing: 0.13em;
            text-transform: uppercase;
        }


        /* ==========================================
           SIDEBAR INPUTS
           ========================================== */

        section[data-testid="stSidebar"]
        div[data-baseweb="select"] > div {
            background: #191813;
            border-color: rgba(214, 169, 79, 0.17);
        }

        section[data-testid="stSidebar"]
        [data-testid="stRadio"] label {
            padding: 0.28rem 0.35rem;
            border-radius: 6px;
        }

        section[data-testid="stSidebar"]
        [data-testid="stRadio"] label:hover {
            background: rgba(214, 169, 79, 0.06);
        }


        /* ==========================================
           BUTTONS
           ========================================== */

        .stButton > button,
        .stDownloadButton > button,
        .stFormSubmitButton > button {
            min-height: 2.45rem;

            color: #11100c;
            background:
                linear-gradient(
                    135deg,
                    #e1b75d,
                    #c79236
                );

            border: 1px solid rgba(240, 201, 109, 0.4);
            border-radius: var(--tam-radius-sm);

            font-weight: 760;

            transition:
                transform 120ms ease,
                filter 120ms ease,
                box-shadow 120ms ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stFormSubmitButton > button:hover {
            color: #0d0c09;
            filter: brightness(1.06);

            border-color: rgba(240, 201, 109, 0.7);

            box-shadow:
                0 8px 22px rgba(214, 169, 79, 0.15);

            transform: translateY(-1px);
        }

        .stButton > button:active,
        .stDownloadButton > button:active,
        .stFormSubmitButton > button:active {
            transform: translateY(0);
        }


        /* ==========================================
           INPUTS
           ========================================== */

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] > div,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextInput"] input {
            color: var(--tam-text);
            background: var(--tam-panel);

            border-color: var(--tam-border-soft);
            border-radius: var(--tam-radius-sm);
        }

        div[data-baseweb="input"] > div:focus-within,
        div[data-baseweb="select"] > div:focus-within,
        div[data-baseweb="textarea"] > div:focus-within {
            border-color: rgba(214, 169, 79, 0.55);

            box-shadow:
                0 0 0 1px rgba(214, 169, 79, 0.15);
        }

        [data-testid="stSlider"] {
            padding-top: 0.15rem;
        }


        /* ==========================================
           METRICS
           ========================================== */

        [data-testid="stMetric"] {
            min-height: 112px;
            padding: 0.9rem 1rem;

            background:
                linear-gradient(
                    145deg,
                    rgba(28, 26, 21, 0.98),
                    rgba(20, 19, 15, 0.98)
                );

            border: 1px solid var(--tam-border-soft);
            border-top: 2px solid rgba(214, 169, 79, 0.48);
            border-radius: var(--tam-radius-md);

            box-shadow:
                0 12px 28px rgba(0, 0, 0, 0.16);
        }

        [data-testid="stMetricLabel"] {
            color: var(--tam-muted);
            font-size: 0.7rem;
            font-weight: 750;

            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        [data-testid="stMetricValue"] {
            color: var(--tam-text);
            font-size: 1.45rem;
            font-weight: 780;
        }

        [data-testid="stMetricDelta"] {
            font-size: 0.72rem;
        }


        /* ==========================================
           EXPANDERS, TABS AND CONTAINERS
           ========================================== */

        [data-testid="stExpander"] {
            overflow: hidden;

            background: rgba(21, 20, 16, 0.88);
            border: 1px solid var(--tam-border-soft);
            border-radius: var(--tam-radius-md);
        }

        [data-testid="stExpander"] summary {
            color: var(--tam-soft);
            font-weight: 700;
        }

        [data-baseweb="tab-list"] {
            gap: 0.35rem;

            background: transparent;
            border-bottom: 1px solid var(--tam-border-soft);
        }

        [data-baseweb="tab"] {
            color: var(--tam-muted);
            background: transparent;
        }

        [aria-selected="true"][data-baseweb="tab"] {
            color: var(--tam-amber-soft);
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(21, 20, 16, 0.55);
            border-color: var(--tam-border-soft);
            border-radius: var(--tam-radius-md);
        }


        /* ==========================================
           ALERTS
           ========================================== */

        [data-testid="stAlert"] {
            border-radius: var(--tam-radius-md);
            border-width: 1px;
        }


        /* ==========================================
           DATAFRAMES
           ========================================== */

        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            overflow: hidden;

            border: 1px solid var(--tam-border-soft);
            border-radius: var(--tam-radius-md);
        }


        /* ==========================================
           ACTION CARDS USED BY DASHBOARD
           ========================================== */

        .tam-action-card {
            min-height: 132px;
            padding: 18px 18px 16px;

            background:
                linear-gradient(
                    145deg,
                    rgba(29, 27, 22, 0.98),
                    rgba(18, 17, 13, 0.98)
                );

            border: 1px solid var(--tam-border-soft);
            border-radius: var(--tam-radius-lg);

            box-shadow:
                0 14px 32px rgba(0, 0, 0, 0.20);

            margin-bottom: 8px;
        }

        .tam-action-card:hover {
            border-color: rgba(214, 169, 79, 0.35);

            box-shadow:
                0 18px 38px rgba(0, 0, 0, 0.24),
                0 0 24px rgba(214, 169, 79, 0.045);
        }

        .tam-action-icon {
            margin-bottom: 10px;
            font-size: 1.65rem;
        }

        .tam-action-title {
            margin-bottom: 7px;

            color: var(--tam-text);
            font-size: 1.03rem;
            font-weight: 800;
        }

        .tam-action-copy {
            color: var(--tam-muted);
            font-size: 0.84rem;
            line-height: 1.45;
        }


        /* ==========================================
           STATUS CARDS
           ========================================== */

        .tam-status-card {
            padding: 16px 17px;

            background: rgba(21, 20, 16, 0.82);
            border: 1px solid var(--tam-border-soft);
            border-radius: var(--tam-radius-md);

            margin-bottom: 10px;
        }

        .tam-status-label {
            margin-bottom: 5px;

            color: var(--tam-muted);
            font-size: 0.72rem;

            letter-spacing: 0.09em;
            text-transform: uppercase;
        }

        .tam-status-value {
            color: var(--tam-soft);
            font-weight: 700;
        }


        /* ==========================================
           GLOBAL BOTTOM STATUS BAR
           ========================================== */

        .tam-status-bar {
            display: grid;

            grid-template-columns:
                repeat(4, minmax(0, auto));

            justify-content: space-between;
            align-items: center;
            gap: 0.8rem;

            margin-top: 1.3rem;
            padding: 0.62rem 0.75rem;

            color: var(--tam-muted);
            background: #151410;

            border-top: 1px solid var(--tam-border);
            border-bottom: 1px solid var(--tam-border);

            font-family:
                "Cascadia Mono",
                Consolas,
                monospace;

            font-size: 0.65rem;
            letter-spacing: 0.025em;
        }

        .tam-status-bar > span {
            display: inline-flex;
            align-items: center;
            gap: 0.32rem;
            white-space: nowrap;
        }

        .tam-status-bar .tam-status-value {
            color: var(--tam-soft);
            font-size: inherit;
            font-weight: 700;
        }

        .tam-status-bar .tam-status-online {
            color: var(--tam-green);
            font-weight: 800;
        }

        .tam-status-bar .tam-status-offline {
            color: var(--tam-red);
            font-weight: 800;
        }


        /* ==========================================
           RESPONSIVE LAYOUT
           ========================================== */

        @media (max-width: 900px) {
            .tam-app-heading {
                grid-template-columns: 1fr;
            }

            .tam-app-meta {
                text-align: left;
            }

            .tam-status-bar {
                grid-template-columns: 1fr 1fr;
            }
        }

        @media (max-width: 560px) {
            [data-testid="stMainBlockContainer"] {
                padding-left: 0.8rem;
                padding-right: 0.8rem;
            }

            .tam-status-bar {
                grid-template-columns: 1fr;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# ==================================================
# MAIN APPLICATION HEADER
# ==================================================

def render_app_heading() -> None:
    """
    Render the institutional TAM Tradex application heading.
    """

    now = datetime.now()

    st.markdown(
        f"""
        <div class="tam-app-heading">
            <div>
                <div class="tam-app-kicker">
                    Research · Execution · Risk
                </div>

                <div class="tam-app-title">
                    TAM Tradex
                </div>

                <div class="tam-app-subtitle">
                    AI market intelligence and paper-trading workstation
                </div>
            </div>

            <div class="tam-app-meta">
                VERSION {APP_VERSION}<br>
                SESSION {now.strftime("%Y-%m-%d %H:%M")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==================================================
# SIDEBAR BRAND
# ==================================================

def render_sidebar_brand() -> None:
    """
    Render the TAM Tradex sidebar brand.
    """

    st.sidebar.markdown(
        """
        <div class="tam-sidebar-brand">
            <div>
                <span class="tam-sidebar-mark"></span>

                <span class="tam-sidebar-name">
                    TAM TRADEX
                </span>
            </div>

            <div class="tam-sidebar-caption">
                Institutional research and simulated execution
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==================================================
# SIDEBAR SECTION
# ==================================================

def render_sidebar_section(title: str) -> None:
    """
    Render a sidebar section label.
    """

    safe_title = str(title).strip()

    st.sidebar.markdown(
        f'<div class="tam-sidebar-section">{safe_title}</div>',
        unsafe_allow_html=True,
    )


# ==================================================
# BOTTOM STATUS BAR
# ==================================================

def render_status_bar(
    current_page: str,
    selected_ticker: str,
    market_connected: bool = True,
    **_,
) -> None:
    """Render the terminal status bar."""

    page_text = str(current_page or "Dashboard").replace("_", " ").upper()
    ticker_text = str(selected_ticker or "N/A").upper()

    if market_connected:
        connection_text = "CONNECTED"
        connection_class = "tam-status-online"
    else:
        connection_text = "OFFLINE"
        connection_class = "tam-status-offline"

    status_html = (
        '<div class="tam-status-bar">'
        f'<span>PAGE <span class="tam-status-value">{page_text}</span></span>'
        f'<span>ASSET <span class="tam-status-value">{ticker_text}</span></span>'
        f'<span>DATA <span class="{connection_class}">{connection_text}</span></span>'
        '<span>ENGINE <span class="tam-status-value">SIMULATION</span></span>'
        '</div>'
    )

    st.markdown(
        status_html,
        unsafe_allow_html=True,
    )
