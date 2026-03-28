import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, GridOptionsBuilder, JsCode

from model.reporting import (
    get_presupuesto_vs_gastos,
    get_detalle_ingresos,
    get_totales_ingresos_presupuesto_gastos,
)

st.set_page_config(page_title="Budget vs Expenses", layout="wide")
st.title("Budget vs Expenses Report")


@st.cache_data(ttl=120)
def load_data() -> pd.DataFrame:
    return get_presupuesto_vs_gastos()


@st.cache_data(ttl=120)
def load_totals_data() -> pd.DataFrame:
    return get_totales_ingresos_presupuesto_gastos()


df = load_data()
totals_df = load_totals_data()

if df.empty:
    st.info("No data available for the report.")
    st.stop()

st.sidebar.header("Filters")

# Periodo (aniomes) filter
available_periods = sorted(df["aniomes"].dropna().unique().tolist(), reverse=True)
selected_period = st.sidebar.selectbox(
    "Period (aniomes)", options=available_periods, index=0
)
filtered_df = df[df["aniomes"] == selected_period]

if filtered_df.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

filtered_totals_df = pd.DataFrame()
if totals_df is not None and not totals_df.empty and "aniomes" in totals_df.columns:
    filtered_totals_df = totals_df[totals_df["aniomes"] == selected_period].copy()

col1, col2, col3, col4 = st.columns(4)

budget_col = next((c for c in filtered_df.columns if "presupuestosoles" in c.lower()), None)
gasto_col  = next((c for c in filtered_df.columns if "montosoles" in c.lower()), None)

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
    with st.expander("Presupuesto & Gasto by Agrupación", expanded=True):
        pie_df = (
            filtered_df
            .groupby("agrupacionpresupuesto", as_index=False)[[budget_col, gasto_col]]
            .sum()
        )
        total_budget = pie_df[budget_col].sum()
        total_gasto  = pie_df[gasto_col].sum()
        pie_df["pct_presupuesto"] = (pie_df[budget_col] / total_budget * 100).round(1).astype(str) + "%"
        pie_df["pct_gasto"]       = (pie_df[gasto_col]  / total_gasto  * 100).round(1).astype(str) + "%"

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
                hovertemplate="<b>%{label}</b><br>Presupuesto: %{value:,.2f}<br>%{percent}<extra></extra>"
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
                hovertemplate="<b>%{label}</b><br>Gasto: %{value:,.2f}<br>%{percent}<extra></extra>"
            )
            st.plotly_chart(fig_g, use_container_width=True)

st.divider()


if budget_col and gasto_col and {"agrupacionpresupuesto", "categoria"}.issubset(filtered_df.columns):
    with st.expander("Summary by Agrupacion & Categori­a", expanded=True):
        summary_df = (
            filtered_df
            .groupby(["agrupacionpresupuesto", "categoria"], as_index=False)[[budget_col, gasto_col]]
            .sum()
        )
        summary_df["varianza"] = summary_df[budget_col] - summary_df[gasto_col]

        gb_s = GridOptionsBuilder.from_dataframe(summary_df)
        gb_s.configure_default_column(resizable=True, sortable=True, filter=True)
        gb_s.configure_column("agrupacionpresupuesto", header_name="Agrupacion Presupuesto")
        gb_s.configure_column("categoria", header_name="Categori­a")
        gb_s.configure_column(budget_col, header_name="Presupuesto", type=["numericColumn"], valueFormatter="x.toLocaleString('en-US', {minimumFractionDigits:2})")
        gb_s.configure_column(gasto_col, header_name="Gasto", type=["numericColumn"], valueFormatter="x.toLocaleString('en-US', {minimumFractionDigits:2})")
        gb_s.configure_column("varianza", header_name="Varianza", type=["numericColumn"], valueFormatter="x.toLocaleString('en-US', {minimumFractionDigits:2})")
        grid_opts_s = gb_s.build()
        grid_opts_s["pinnedBottomRowData"] = [{
            "agrupacionpresupuesto": "TOTAL",
            "categoria": "",
            budget_col: summary_df[budget_col].sum(),
            gasto_col: summary_df[gasto_col].sum(),
            "varianza": summary_df["varianza"].sum(),
        }]
        AgGrid(
            summary_df,
            gridOptions=grid_opts_s,
            data_return_mode=DataReturnMode.AS_INPUT,
            update_mode=GridUpdateMode.NO_UPDATE,
            fit_columns_on_grid_load=True,
            theme="streamlit",
            height=min(50 + 35 * len(summary_df), 400),
            use_container_width=True,
        )

st.divider()

st.subheader("Detail")

selected_columns = [
    "agrupacionpresupuesto",
    "categoria",
    "subcategoria",
    "presupuestosoles",
    "montosoles",
]

selected_columns_df = filtered_df[[col for col in selected_columns if col in filtered_df.columns]]

gb = GridOptionsBuilder.from_dataframe(selected_columns_df)
gb.configure_default_column(resizable=True, sortable=True, filter=True)
gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
gb.configure_side_bar(filters_panel=True, columns_panel=True)

formatter = "x == null ? '' : x.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})"

gb.configure_column(
    "presupuestosoles",
    type=["numericColumn"],
    valueFormatter=formatter,
)
gb.configure_column(
    "montosoles",
    type=["numericColumn"],
    valueFormatter=formatter,
)
gb.configure_column(
    "agrupacionpresupuesto",
    cellStyle={
        "fontWeight": "normal",
    },
    # Override style for pinned row via JS
)

grid_options = gb.build()

# Compute totals
total_presupuesto = filtered_df["presupuestosoles"].sum() if "presupuestosoles" in filtered_df.columns else 0
total_monto = filtered_df["montosoles"].sum() if "montosoles" in filtered_df.columns else 0

total_row = {
    "agrupacionpresupuesto": "TOTAL",
    "categoria": "",
    "subcategoria": "",
    "presupuestosoles": total_presupuesto,
    "montosoles": total_monto,
}

grid_options["pinnedBottomRowData"] = [total_row]

# Bold + background styling for the pinned total row
# grid_options["getRowStyle"] = JsCode("""
#     function(params) {
#         if (params.node.rowPinned) {
#             return {
#                 'fontWeight': 'bold',
#                 'backgroundColor': '#f0f2f6',
#                 'borderTop': '2px solid #4a4a4a',
#             };
#         }
#     }
# """)

AgGrid(
    selected_columns_df,
    gridOptions=grid_options,
    data_return_mode=DataReturnMode.AS_INPUT,
    update_mode=GridUpdateMode.NO_UPDATE,
    fit_columns_on_grid_load=False,
    theme="streamlit",
    height=450,
    use_container_width=True,
    allow_unsafe_jscode=True,   # Ã¢â€ Â required for JsCode to work
)

st.divider()
st.subheader("Income Detail")

# Load and display income data
@st.cache_data(ttl=120)
def load_income_data() -> pd.DataFrame:
    return get_detalle_ingresos()

income_df = load_income_data()

if income_df is not None and not income_df.empty:
    # Filter by selected period (aniomes)
    if "aniomes" in income_df.columns:
        filtered_income_df = income_df[income_df["aniomes"] == selected_period]
    else:
        filtered_income_df = income_df

    if not filtered_income_df.empty:
        gb_income = GridOptionsBuilder.from_dataframe(filtered_income_df)
        gb_income.configure_default_column(resizable=True, sortable=True, filter=True)
        gb_income.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
        gb_income.configure_side_bar(filters_panel=True, columns_panel=True)
        # Build total row explicitly, following the summary example
        total_row = {
            "nombresubcategoria": "TOTAL" if "nombresubcategoria" in filtered_income_df.columns else "",
            "descripcion": "",
            "moneda": "",
            "ingresosoles": filtered_income_df["ingresosoles"].sum() if "ingresosoles" in filtered_income_df.columns else "",
            "ingresodolar": filtered_income_df["ingresodolar"].sum() if "ingresodolar" in filtered_income_df.columns else "",
        }
        grid_options_income = gb_income.build()
        grid_options_income["pinnedBottomRowData"] = [total_row]

        AgGrid(
            filtered_income_df,
            gridOptions=grid_options_income,
            data_return_mode=DataReturnMode.AS_INPUT,
            update_mode=GridUpdateMode.NO_UPDATE,
            fit_columns_on_grid_load=False,
            theme="streamlit",
            height=450,
            use_container_width=True,
        )
    else:
        st.info("No income data available for the selected period.")
else:
    st.info("No income data available.")
