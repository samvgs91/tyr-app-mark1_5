import streamlit as st
import pandas as pd
from datetime import date
from db import get_connection

st.set_page_config(page_title="Expense Viewer", layout="wide")

# --- Fetch Real Data from Postgres ---
@st.cache_data(ttl=60) # Cachea los datos por 60 segundos para que la app sea muy rápida
def get_report_data():
    try:
        conn = get_connection()
        query = '''
            SELECT 
                t.fecha AS "Date", 
                t.descripcion AS "Description", 
                sc.nombresubcategoria AS "Category", 
                t.monto AS "Amount" 
            FROM transaccion t 
            LEFT JOIN subcategoria sc ON t.subcategoriaid = sc.id 
            WHERE t.eliminado = false
        '''
        df = pd.read_sql(query, conn)
        conn.close()
        
        if not df.empty:
            # Blindaje contra las minúsculas automáticas de Postgres
            col_map = {'date': 'Date', 'description': 'Description', 'category': 'Category', 'amount': 'Amount'}
            df = df.rename(columns=lambda x: col_map.get(x.lower(), x))
            
            # Aseguramos que la columna Date sea reconocida como fecha por Pandas
            df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return pd.DataFrame()

df = get_report_data()

# --- Normalize / derive fields once ---
if not df.empty:
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Period"] = df["Date"].dt.to_period("M")  # e.g., 2025-08

st.title("📅 Filter Expenses by Month/Year")

# --- Build Month/Year options from data ---
if df.empty:
    st.info("No hay datos de gastos registrados aún. ¡Empieza a registrar transacciones para ver tus reportes!")
    st.stop()

periods = sorted(df["Period"].unique(), reverse=True)  # newest first

def period_label(p):
    # p is a Period('YYYY-MM'); turn into 'Aug 2025'
    return pd.Period(p, freq="M").strftime("%b %Y")

choices = ["All months"] + [period_label(p) for p in periods]
default_index = 0  # default to All

selected_label = st.selectbox("Month", options=choices, index=default_index, key="period_filter")

# Map label back to Period (or None for All)
selected_period = None if selected_label == "All months" else periods[choices.index(selected_label) - 1]

# --- Apply filter ---
if selected_period is None:
    view = df.sort_values("Date")
else:
    view = df[df["Period"] == selected_period].sort_values("Date")

# --- KPIs ---
c1, c2, c3 = st.columns(3)
c1.metric("Total spend", f"${view['Amount'].sum():,.2f}")
c2.metric("Transactions", f"{len(view):,}")
c3.metric("Distinct categories", view["Category"].nunique())

st.divider()

# --- Table ---
st.subheader("📋 Expenses")
st.dataframe(view[["Date","Description","Category","Amount"]], use_container_width=True, hide_index=True)

# --- Charts ---
left, right = st.columns(2)

with left:
    st.subheader("📊 By Category")
    if not view.empty:
        cat = (view.groupby("Category", as_index=False)["Amount"]
                    .sum()
                    .sort_values("Amount", ascending=False))
        st.bar_chart(cat, x="Category", y="Amount", use_container_width=True)
    else:
        st.info("No data for the selected period.")

with right:
    st.subheader("📈 Daily Trend")
    if not view.empty:
        daily = (view.groupby("Date", as_index=False)["Amount"].sum())
        st.line_chart(daily, x="Date", y="Amount", use_container_width=True)
    else:
        st.info("No data for the selected period.")