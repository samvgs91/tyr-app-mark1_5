import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import GridOptionsBuilder, GridUpdateMode, DataReturnMode
from safe_aggrid import render_aggrid

from model.reporting import get_detalle_gastos

st.set_page_config(page_title="Expense Detail", layout="wide")
st.title("Expense Detail Report")


@st.cache_data(ttl=120)
def load_data() -> pd.DataFrame:
    return get_detalle_gastos()


df = load_data()

if df.empty:
    st.info("No data available for the report.")
    st.stop()

# Detect key columns dynamically
fecha_col  = next((c for c in df.columns if "fecha" in c.lower()), None)
monto_col  = next((c for c in df.columns if "monto" in c.lower()), None)
aniomes_col = next((c for c in df.columns if "aniomes" in c.lower()), None)

# ── Sidebar filters ──────────────────────────────────────────────────────────
st.sidebar.header("Filters")


if aniomes_col:
    available_periods = sorted(df[aniomes_col].dropna().unique().tolist(), reverse=True)
    selected_period = st.sidebar.selectbox(
        "Período (aniomes)", options=available_periods, index=0
    )
    filtered_df = df[df[aniomes_col] == selected_period]
else:
    filtered_df = df

if filtered_df.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

# ── Summary metrics ──────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
if monto_col:
    col1.metric("Total Expenses", f"{filtered_df[monto_col].sum():,.2f}")
col2.metric("Transactions", f"{len(filtered_df):,}")

st.divider()

# ── Pie chart by Agrupación Presupuesto ────────────────────────────────
if monto_col and "agrupacionpresupuesto" in filtered_df.columns:
    with st.expander("Gastos por Agrupación Presupuesto", expanded=True):
        pie_df = (
            filtered_df
            .groupby("agrupacionpresupuesto", as_index=False)[monto_col]
            .sum()
        )
        total = pie_df[monto_col].sum()
        pie_df["porcentaje"] = (pie_df[monto_col] / total * 100).round(1).astype(str) + "%"
        fig = px.pie(
            pie_df,
            names="agrupacionpresupuesto",
            values=monto_col,
            title="Gastos por Agrupación Presupuesto",
        )
        fig.update_traces(
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Monto: %{value:,.2f}<br>%{percent}<extra></extra>"
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── AgGrid detail table ───────────────────────────────────────────────────────
st.subheader("Transactions")

gb = GridOptionsBuilder.from_dataframe(filtered_df)
gb.configure_default_column(resizable=True, sortable=True, filter=True)
if fecha_col:
    gb.configure_column(
        fecha_col,
        header_name="Fecha",
        valueFormatter="value ? new Date(value).toISOString().slice(0,10) : ''"
    )
if monto_col:
    gb.configure_column(
        monto_col,
        header_name="Monto",
        type=["numericColumn"],
        valueFormatter="x.toLocaleString('en-US', {minimumFractionDigits:2})"
    )
gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=25)
gb.configure_side_bar(filters_panel=True, columns_panel=True)

render_aggrid(
    filtered_df,
    gridOptions=gb.build(),
    data_return_mode=DataReturnMode.AS_INPUT,
    update_mode=GridUpdateMode.NO_UPDATE,
    fit_columns_on_grid_load=False,
    theme="streamlit",
    height=500,
    use_container_width=True,
    fallback_label="expense transactions",
)
