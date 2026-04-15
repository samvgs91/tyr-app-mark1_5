import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from model.reporting import (
    get_detalle_ingresos,
    get_presupuesto_vs_gastos,
    get_totales_ingresos_presupuesto_gastos,
)
from page_utils.drilldown import (
    aggregate_level,
    ensure_drill_state,
    filter_by_drill_path,
    get_active_level,
    reset_from_level,
    sanitize_drill_filters,
)
from page_utils.streamlit_tables import append_total_row, render_table

st.set_page_config(page_title="Budget vs Expenses Drill Down", layout="wide")
st.title("Budget vs Expenses Report Drill-Down")
st.caption(
    "Pure Streamlit drill-down on the real budget vs expenses dataset."
)

DRILL_COLUMNS = [
    ("agrupacionpresupuesto", "Agrupacion"),
    ("categoria", "Categoria"),
    ("subcategoria", "Subcategoria"),
]
DRILL_STATE_KEY = "budget_expense_drill_filters"
WIDGET_PREFIX = "budget_expense"


@st.cache_data(ttl=120)
def load_data() -> pd.DataFrame:
    return get_presupuesto_vs_gastos()


@st.cache_data(ttl=120)
def load_totals_data() -> pd.DataFrame:
    return get_totales_ingresos_presupuesto_gastos()


@st.cache_data(ttl=120)
def load_income_data() -> pd.DataFrame:
    return get_detalle_ingresos()

def render_breadcrumbs(available_drill_columns: list[tuple[str, str]]) -> None:
    st.subheader("Current Path")
    cols = st.columns(len(available_drill_columns) + 1)

    with cols[0]:
        # "All" always returns to the root of the hierarchy.
        if st.button("All", use_container_width=True):
            reset_from_level(0, DRILL_STATE_KEY, DRILL_COLUMNS, WIDGET_PREFIX)
            st.rerun()

    for index, (column, label) in enumerate(available_drill_columns, start=1):
        selected = st.session_state[DRILL_STATE_KEY].get(column)
        button_label = f"{label}: {selected}" if selected else label
        with cols[index]:
            # Clicking any breadcrumb jumps back to that level.
            if st.button(button_label, use_container_width=True):
                reset_from_level(index - 1, DRILL_STATE_KEY, DRILL_COLUMNS, WIDGET_PREFIX)
                st.rerun()


def render_selector(
    scope_df: pd.DataFrame,
    level_column: str,
    level_label: str,
    value_column: str,
    available_drill_columns: list[tuple[str, str]],
) -> None:
    summary_df = aggregate_level(scope_df, level_column, value_column)
    if summary_df.empty:
        st.info(f"No values available for {level_label.lower()}.")
        return

    options = summary_df[level_column].tolist()
    current = st.session_state[DRILL_STATE_KEY].get(level_column)
    default_index = options.index(current) if current in options else 0
    selected = st.selectbox(
        f"Choose a {level_label.lower()}",
        options=options,
        index=default_index,
        key=f"{WIDGET_PREFIX}_{level_column}_selector",
    )

    # The explicit button avoids accidental auto-drill on rerun. A selectbox
    # always has a value, so we only advance when the user confirms it.
    button_label = (
        f"Drill into {selected}"
        if selected is not None
        else f"Drill into {level_label.lower()}"
    )
    if st.button(
        button_label,
        key=f"{WIDGET_PREFIX}_{level_column}_drill_button",
        use_container_width=True,
        disabled=selected is None or selected == current,
    ):
        st.session_state[DRILL_STATE_KEY][level_column] = selected
        next_level = [column for column, _ in available_drill_columns].index(level_column) + 1
        reset_from_level(next_level, DRILL_STATE_KEY, DRILL_COLUMNS, WIDGET_PREFIX)
        st.session_state[DRILL_STATE_KEY][level_column] = selected
        st.rerun()


def render_pie(summary_df: pd.DataFrame, level_column: str, value_column: str, title: str) -> None:
    # Pre-build hover text so we don't rely on customdata alignment.
    hover_texts = [
        f"<b>{row[level_column]}</b><br>"
        f"Monto: {row[value_column]:,.2f}<br>"
        f"Participacion: {row['share']:.1%}"
        for _, row in summary_df.iterrows()
    ]

    fig = go.Figure(
        go.Pie(
            labels=summary_df[level_column],
            values=summary_df[value_column],
            hole=0.45,
            textinfo="percent+label",
            hovertext=hover_texts,
            hoverinfo="text",
        )
    )
    fig.update_layout(title_text=title)
    st.plotly_chart(fig, use_container_width=True)


def render_scope_metrics(scope_df: pd.DataFrame, budget_col: str, gasto_col: str) -> None:
    # These metrics reflect only the currently visible drill scope.
    visible_budget = scope_df[budget_col].sum() if budget_col in scope_df.columns else 0
    visible_expense = scope_df[gasto_col].sum() if gasto_col in scope_df.columns else 0
    variance = visible_budget - visible_expense

    col1, col2, col3 = st.columns(3)
    col1.metric("Visible Presupuesto", f"{visible_budget:,.2f}")
    col2.metric("Visible Gastos", f"{visible_expense:,.2f}")
    col3.metric("Visible Varianza", f"{variance:,.2f}")


df = load_data()
totals_df = load_totals_data()

if df.empty:
    st.info("No data available for the report.")
    st.stop()

st.sidebar.header("Filters")

available_periods = sorted(df["aniomes"].dropna().unique().tolist(), reverse=True)
selected_period = st.sidebar.selectbox(
    "Period (aniomes)", options=available_periods, index=0
)
filtered_df = df[df["aniomes"] == selected_period].copy()

if filtered_df.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

budget_col = next((c for c in filtered_df.columns if "presupuestosoles" in c.lower()), None)
gasto_col = next((c for c in filtered_df.columns if "montosoles" in c.lower()), None)

if not budget_col or not gasto_col:
    st.error("The dataset does not include the expected budget and expense columns.")
    st.stop()

available_drill_columns = [
    (column, label) for column, label in DRILL_COLUMNS if column in filtered_df.columns
]
if not available_drill_columns:
    st.error("The dataset does not include drill-down columns.")
    st.stop()

for column, _ in available_drill_columns:
    if filtered_df[column].dtype == "object":
        filtered_df[column] = filtered_df[column].fillna("Unassigned")

ensure_drill_state(DRILL_STATE_KEY)
# Keep the drill path valid after period changes or data refreshes.
sanitize_drill_filters(
    filtered_df,
    available_drill_columns,
    DRILL_STATE_KEY,
    WIDGET_PREFIX,
)

filtered_totals_df = pd.DataFrame()
if totals_df is not None and not totals_df.empty and "aniomes" in totals_df.columns:
    filtered_totals_df = totals_df[totals_df["aniomes"] == selected_period].copy()

col1, col2, col3, col4 = st.columns(4)

total_presupuesto_metric = (
    filtered_totals_df["presupuestosoles"].sum()
    if "presupuestosoles" in filtered_totals_df.columns
    else 0
)
total_gastos_metric = (
    filtered_totals_df["gastosoles"].sum()
    if "gastosoles" in filtered_totals_df.columns
    else 0
)
total_ingresos_metric = (
    filtered_totals_df["ingresosoles"].sum()
    if "ingresosoles" in filtered_totals_df.columns
    else 0
)
total_ahorrado_metric = (
    filtered_totals_df["ahorrosoles"].sum()
    if "ahorrosoles" in filtered_totals_df.columns
    else 0
)

col1.metric("Total Presupuesto", f"{total_presupuesto_metric:,.2f}")
col2.metric("Total Gastos", f"{total_gastos_metric:,.2f}")
col3.metric("Total Ingresos", f"{total_ingresos_metric:,.2f}")
col4.metric("Total Ahorrado", f"{total_ahorrado_metric:,.2f}")

st.divider()

chart_value_label = st.radio(
    "Chart Measure",
    options=["Gastos", "Presupuesto"],
    horizontal=True,
)
# The same drill hierarchy can be explored with either expenses or budget.
chart_value_column = gasto_col if chart_value_label == "Gastos" else budget_col

# All downstream sections use the same scoped dataframe so charts and tables
# stay synchronized while drilling up and down.
scope_df = filter_by_drill_path(filtered_df, available_drill_columns, DRILL_STATE_KEY)
if scope_df.empty:
    st.warning("No data matches the current drill-down path.")
    st.stop()

active_level_index, current_level_column, current_level_label = get_active_level(
    available_drill_columns,
    DRILL_STATE_KEY,
)
summary_df = aggregate_level(scope_df, current_level_column, chart_value_column)

with st.expander("Drill-Down by Hierarchy", expanded=True):
    render_breadcrumbs(available_drill_columns)
    render_scope_metrics(scope_df, budget_col, gasto_col)

    chart_col, scope_col = st.columns([1.3, 1])

    with chart_col:
        if summary_df.empty:
            st.info(f"No values available for {current_level_label.lower()}.")
        else:
            render_pie(
                summary_df,
                current_level_column,
                chart_value_column,
                f"{chart_value_label} by {current_level_label}",
            )
            if active_level_index < len(available_drill_columns):
                render_selector(
                    scope_df,
                    current_level_column,
                    current_level_label,
                    chart_value_column,
                    available_drill_columns,
                )

    with scope_col:
        st.subheader("Current Scope")
        scope_columns = [
            column for column, _ in available_drill_columns if column in scope_df.columns
        ]
        scope_preview = (
            scope_df[scope_columns + [budget_col, gasto_col]]
            .sort_values(by=gasto_col, ascending=False)
            .head(15)
        )
        render_table(scope_preview, height=420)

st.divider()

if {"agrupacionpresupuesto", "categoria"}.issubset(scope_df.columns):
    with st.expander("Scoped Summary by Agrupacion & Categoria", expanded=True):
        grouped_scope_df = (
            scope_df.groupby(
                ["agrupacionpresupuesto", "categoria"], as_index=False
            )[[budget_col, gasto_col]].sum()
        )
        grouped_scope_df["varianza"] = grouped_scope_df[budget_col] - grouped_scope_df[gasto_col]
        grouped_scope_df = append_total_row(
            grouped_scope_df,
            {
                "agrupacionpresupuesto": "TOTAL",
                "categoria": "",
                budget_col: grouped_scope_df[budget_col].sum(),
                gasto_col: grouped_scope_df[gasto_col].sum(),
                "varianza": grouped_scope_df["varianza"].sum(),
            },
        )
        render_table(grouped_scope_df, height=min(50 + 35 * len(grouped_scope_df), 400))

st.divider()
st.subheader("Scoped Detail")

selected_columns = [
    "agrupacionpresupuesto",
    "categoria",
    "subcategoria",
    budget_col,
    gasto_col,
]

selected_columns_df = scope_df[
    [col for col in selected_columns if col in scope_df.columns]
].copy()

selected_columns_df = append_total_row(
    selected_columns_df,
    {
        "agrupacionpresupuesto": "TOTAL",
        "categoria": "",
        "subcategoria": "",
        budget_col: scope_df[budget_col].sum() if budget_col in scope_df.columns else 0,
        gasto_col: scope_df[gasto_col].sum() if gasto_col in scope_df.columns else 0,
    },
)

render_table(selected_columns_df, height=450)

st.divider()
st.subheader("Income Detail")

income_df = load_income_data()

if income_df is not None and not income_df.empty:
    if "aniomes" in income_df.columns:
        filtered_income_df = income_df[income_df["aniomes"] == selected_period].copy()
    else:
        filtered_income_df = income_df.copy()

    if not filtered_income_df.empty:
        filtered_income_df = append_total_row(
            filtered_income_df,
            {
                "nombresubcategoria": (
                    "TOTAL"
                    if "nombresubcategoria" in filtered_income_df.columns
                    else ""
                ),
                "descripcion": "",
                "moneda": "",
                "ingresosoles": (
                    filtered_income_df["ingresosoles"].sum()
                    if "ingresosoles" in filtered_income_df.columns
                    else ""
                ),
                "ingresodolar": (
                    filtered_income_df["ingresodolar"].sum()
                    if "ingresodolar" in filtered_income_df.columns
                    else ""
                ),
            },
        )
        render_table(filtered_income_df, height=450)
    else:
        st.info("No income data available for the selected period.")
else:
    st.info("No income data available.")
