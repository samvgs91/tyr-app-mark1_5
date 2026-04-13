import pandas as pd
import plotly.express as px
import streamlit as st

from model.reporting import (
    get_detalle_ingresos,
    get_presupuesto_vs_gastos,
    get_totales_ingresos_presupuesto_gastos,
)

st.set_page_config(page_title="Budget vs Expenses", layout="wide")
st.title("Budget vs Expenses Report")


def append_total_row(df: pd.DataFrame, total_row: dict) -> pd.DataFrame:
    total_df = pd.DataFrame([total_row])
    return pd.concat([df, total_df], ignore_index=True)


def build_column_config(df: pd.DataFrame) -> dict:
    column_config = {}
    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            column_config[column] = st.column_config.NumberColumn(
                column,
                format="%.2f",
            )
    return column_config


def render_table(df: pd.DataFrame, height: int = 450):
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=height,
        column_config=build_column_config(df),
    )


@st.cache_data(ttl=120)
def load_data() -> pd.DataFrame:
    return get_presupuesto_vs_gastos()


@st.cache_data(ttl=120)
def load_totals_data() -> pd.DataFrame:
    return get_totales_ingresos_presupuesto_gastos()


@st.cache_data(ttl=120)
def load_income_data() -> pd.DataFrame:
    return get_detalle_ingresos()


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

filtered_totals_df = pd.DataFrame()
if totals_df is not None and not totals_df.empty and "aniomes" in totals_df.columns:
    filtered_totals_df = totals_df[totals_df["aniomes"] == selected_period].copy()

col1, col2, col3, col4 = st.columns(4)

budget_col = next((c for c in filtered_df.columns if "presupuestosoles" in c.lower()), None)
gasto_col = next((c for c in filtered_df.columns if "montosoles" in c.lower()), None)

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

if budget_col and gasto_col and "agrupacionpresupuesto" in filtered_df.columns:
    with st.expander("Presupuesto & Gasto by Agrupacion", expanded=True):
        pie_df = (
            filtered_df.groupby("agrupacionpresupuesto", as_index=False)[
                [budget_col, gasto_col]
            ].sum()
        )

        col_a, col_b = st.columns(2)
        with col_a:
            fig_b = px.pie(
                pie_df,
                names="agrupacionpresupuesto",
                values=budget_col,
                title="Presupuesto por Agrupacion",
            )
            fig_b.update_traces(
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Presupuesto: %{value:,.2f}<br>%{percent}<extra></extra>",
            )
            st.plotly_chart(fig_b, use_container_width=True)
        with col_b:
            fig_g = px.pie(
                pie_df,
                names="agrupacionpresupuesto",
                values=gasto_col,
                title="Gasto por Agrupacion",
            )
            fig_g.update_traces(
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Gasto: %{value:,.2f}<br>%{percent}<extra></extra>",
            )
            st.plotly_chart(fig_g, use_container_width=True)

st.divider()

if budget_col and gasto_col and {"agrupacionpresupuesto", "categoria"}.issubset(
    filtered_df.columns
):
    with st.expander("Summary by Agrupacion & Categoria", expanded=True):
        summary_df = (
            filtered_df.groupby(
                ["agrupacionpresupuesto", "categoria"], as_index=False
            )[[budget_col, gasto_col]].sum()
        )
        summary_df["varianza"] = summary_df[budget_col] - summary_df[gasto_col]
        summary_df = append_total_row(
            summary_df,
            {
                "agrupacionpresupuesto": "TOTAL",
                "categoria": "",
                budget_col: summary_df[budget_col].sum(),
                gasto_col: summary_df[gasto_col].sum(),
                "varianza": summary_df["varianza"].sum(),
            },
        )
        render_table(summary_df, height=min(50 + 35 * len(summary_df), 400))

st.divider()
st.subheader("Detail")

selected_columns = [
    "agrupacionpresupuesto",
    "categoria",
    "subcategoria",
    "presupuestosoles",
    "montosoles",
]

selected_columns_df = filtered_df[
    [col for col in selected_columns if col in filtered_df.columns]
].copy()

selected_columns_df = append_total_row(
    selected_columns_df,
    {
        "agrupacionpresupuesto": "TOTAL",
        "categoria": "",
        "subcategoria": "",
        "presupuestosoles": (
            filtered_df["presupuestosoles"].sum()
            if "presupuestosoles" in filtered_df.columns
            else 0
        ),
        "montosoles": (
            filtered_df["montosoles"].sum()
            if "montosoles" in filtered_df.columns
            else 0
        ),
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
