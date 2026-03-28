import streamlit as st
import pandas as pd
from datetime import date
from crud import get_all_monedas, get_all_subcategories
from model.transaction_model import (
    get_transacciones_by_month,
    insert_transaccion,
    update_transaccion,
    soft_delete_transaccion,
)
from utilitaries.month_mapping import month_mapping, years_data, expense_type_mapping


DESCRIPCION_COL = "Descripci\u00f3n"

st.set_page_config(page_title="Registro de Gastos Manual", layout="wide")
st.title("Transacciones de Gastos")
st.caption("Esta pagina consulta y actualiza transacciones directamente desde la base de datos.")


def normalize_monedas_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["monedaid", "moneda"])

    col_map = {
        "monedaid": "monedaid",
        "moneda": "moneda",
        "simbolomoneda": "moneda",
    }
    return df.rename(columns=lambda x: col_map.get(str(x).lower(), x))


def normalize_subcategorias_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["subcategoriaid", "nombresubcategoria"])

    col_map = {
        "subcategoriaid": "subcategoriaid",
        "nombresubcategoria": "nombresubcategoria",
        "nombre_subcategoria": "nombresubcategoria",
    }
    return df.rename(columns=lambda x: col_map.get(str(x).lower(), x))


def normalize_transacciones_df(df: pd.DataFrame) -> pd.DataFrame:
    expected_columns = ["id", "fecha", "monedaid", "moneda", "monto", "descripcion", "subcategoriaid", "subcategoria"]
    if df.empty:
        return pd.DataFrame(columns=expected_columns)

    col_map = {
        "id": "id",
        "fecha": "fecha",
        "monedaid": "monedaid",
        "moneda": "moneda",
        "monto": "monto",
        "descripción": "descripcion",
        "descripciã³n": "descripcion",
        "descripcion": "descripcion",
        "subcategoriaid": "subcategoriaid",
        "subcategoria": "subcategoria",
    }
    df = df.rename(columns=lambda x: col_map.get(str(x).lower(), x))
    df = df.loc[:, ~df.columns.duplicated()]
    return df.reindex(columns=expected_columns)


def build_record_label(record: pd.Series) -> str:
    descripcion = record.get("descripcion") or "Sin descripcion"
    return f"#{int(record['id'])} | {record['fecha']} | {descripcion}"


def build_form_defaults(record: dict | None, default_moneda_id: int, default_subcategoria_id: int) -> dict:
    if record is None:
        return {
            "fecha": date.today(),
            "monedaid": default_moneda_id,
            "monto": 0.0,
            "descripcion": "",
            "subcategoriaid": default_subcategoria_id,
        }

    fecha_val = record.get("fecha")
    if hasattr(fecha_val, "date"):
        fecha_val = fecha_val.date()

    return {
        "fecha": fecha_val or date.today(),
        "monedaid": int(record.get("monedaid")) if pd.notna(record.get("monedaid")) else default_moneda_id,
        "monto": float(record.get("monto")) if pd.notna(record.get("monto")) else 0.0,
        "descripcion": record.get("descripcion") or "",
        "subcategoriaid": int(record.get("subcategoriaid")) if pd.notna(record.get("subcategoriaid")) else default_subcategoria_id,
    }


monedas_df = normalize_monedas_df(get_all_monedas())
subcategorias_df = normalize_subcategorias_df(get_all_subcategories())

if monedas_df.empty:
    st.error("No se encontraron monedas activas para cargar el formulario.")
    st.stop()

if subcategorias_df.empty:
    st.error("No se encontraron subcategorias activas para cargar el formulario.")
    st.stop()

moneda_options = monedas_df["monedaid"].astype(int).tolist()
subcategoria_options = subcategorias_df["subcategoriaid"].astype(int).tolist()
moneda_labels = dict(zip(moneda_options, monedas_df["moneda"].tolist()))
subcategoria_labels = dict(zip(subcategoria_options, subcategorias_df["nombresubcategoria"].tolist()))

action_filters = st.columns(3)
indice_mes = date.today().month - 1
with action_filters[0]:
    anio_seleccionado = st.selectbox("Año", years_data, index=0, key="demo_year")
with action_filters[1]:
    mes_seleccionado = st.selectbox("Mes", list(month_mapping.keys()), index=indice_mes, key="demo_month")
with action_filters[2]:
    filtered_expense_types = [
        expense_type
        for expense_type in expense_type_mapping.keys()
        if expense_type == "Gastos Cuenta Bancarias BCP"
    ]
    tipo_gasto = st.selectbox(
        "Tipo de gasto",
        filtered_expense_types,
        index=0,
        key="demo_expense_type",
    )

expense_type_code = int(expense_type_mapping[tipo_gasto])
transacciones_df = normalize_transacciones_df(
    get_transacciones_by_month(anio_seleccionado, month_mapping.get(mes_seleccionado), [expense_type_code])
)

selector_options = {0: "Nuevo registro"}
if not transacciones_df.empty:
    selector_options.update({int(row["id"]): build_record_label(row) for _, row in transacciones_df.iterrows()})

if "expense_demo_selected_id" not in st.session_state:
    st.session_state["expense_demo_selected_id"] = 0

selector_ids = list(selector_options.keys())
current_selected_id = st.session_state.get("expense_demo_selected_id", 0)
if current_selected_id not in selector_ids:
    current_selected_id = 0

default_index = selector_ids.index(current_selected_id)
selected_option = st.selectbox(
    "Selecciona una transaccion para editar o elige crear una nueva",
    options=selector_ids,
    index=default_index,
    format_func=lambda option: selector_options[option],
)

st.session_state["expense_demo_selected_id"] = int(selected_option)
selected_record_id = None if selected_option == 0 else int(selected_option)
selected_record = None
if selected_record_id is not None:
    selected_rows = transacciones_df[transacciones_df["id"] == selected_record_id]
    if not selected_rows.empty:
        selected_record = selected_rows.iloc[0].to_dict()

form_defaults = build_form_defaults(selected_record, moneda_options[0], subcategoria_options[0])

left_col, right_col = st.columns([1.0, 1.2])

with left_col:
    with st.form("expense_demo_form", clear_on_submit=False):
        st.subheader("Formulario de gasto")

        fecha = st.date_input("Fecha", value=form_defaults["fecha"])
        moneda_id = st.selectbox(
            "Moneda",
            options=moneda_options,
            index=moneda_options.index(form_defaults["monedaid"]),
            format_func=lambda option: f"{option} - {moneda_labels.get(option, option)}",
        )
        monto = st.number_input("Monto", min_value=0.0, value=form_defaults["monto"], step=0.50, format="%.2f")
        descripcion = st.text_input(DESCRIPCION_COL, value=form_defaults["descripcion"], max_chars=150)
        subcategoria_id = st.selectbox(
            "SubCategoria",
            options=subcategoria_options,
            index=subcategoria_options.index(form_defaults["subcategoriaid"]),
            format_func=lambda option: f"{option} - {subcategoria_labels.get(option, option)}",
        )

        payload = {
            "fecha": fecha,
            "monedaid": moneda_id,
            "monto": monto,
            "descripcion": descripcion.strip(),
            "subcategoriaid": subcategoria_id,
            "fuentetransaccionid": expense_type_code,
            "tipotransactionid": 1,
        }

        action_col1, action_col2, action_col3 = st.columns(3)
        save_clicked = action_col1.form_submit_button("Guardar")
        delete_clicked = action_col2.form_submit_button("Eliminar")
        clear_clicked = action_col3.form_submit_button("Nuevo")

        if save_clicked:
            if payload["monto"] <= 0:
                st.error("El monto debe ser mayor que cero.")
            elif not payload["descripcion"]:
                st.error("La descripcion es obligatoria.")
            else:
                if selected_record_id is None:
                    new_id = insert_transaccion(
                        fecha=payload["fecha"],
                        fuentetransaccionid=payload["fuentetransaccionid"],
                        subcategoriaid=payload["subcategoriaid"],
                        monedaid=payload["monedaid"],
                        monto=payload["monto"],
                        descripcion=payload["descripcion"],
                        tipotransactionid=payload["tipotransactionid"],
                    )
                    if new_id is not None:
                        st.session_state["expense_demo_selected_id"] = new_id
                        st.success(f"Transaccion #{new_id} creada.")
                        st.rerun()
                    else:
                        st.error("No se pudo crear la transaccion.")
                else:
                    updated = update_transaccion(
                        transaccion_id=selected_record_id,
                        fecha=payload["fecha"],
                        subcategoriaid=payload["subcategoriaid"],
                        monedaid=payload["monedaid"],
                        monto=payload["monto"],
                        descripcion=payload["descripcion"],
                    )
                    if updated:
                        st.success(f"Transaccion #{selected_record_id} actualizada.")
                        st.rerun()
                    else:
                        st.error("No se pudo actualizar la transaccion.")

        if delete_clicked:
            if selected_record_id is None:
                st.error("Selecciona un registro para eliminar.")
            else:
                message = soft_delete_transaccion(selected_record_id)
                if message == "Soft delete complete!":
                    st.session_state["expense_demo_selected_id"] = 0
                    st.warning(f"Transaccion #{selected_record_id} marcada como eliminada.")
                    st.rerun()
                else:
                    st.error(message)

        if clear_clicked:
            st.session_state["expense_demo_selected_id"] = 0
            st.rerun()

    if selected_record_id is not None:
        st.info(f"Registro seleccionado: #{selected_record_id}")
    else:
        st.info("Modo alta: completa el formulario para registrar un nuevo gasto.")

with right_col:
    st.subheader("Listado de transacciones")
    listing_df = transacciones_df.rename(
        columns={
            "fecha": "Fecha",
            "moneda": "Moneda",
            "monto": "Monto",
            "descripcion": DESCRIPCION_COL,
            "subcategoria": "SubCategoria",
        }
    )[["id", "Fecha", "Moneda", "Monto", DESCRIPCION_COL, "SubCategoria"]]

    st.dataframe(
        listing_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Monto": st.column_config.NumberColumn("Monto", format="%.2f"),
            "Fecha": st.column_config.DateColumn("Fecha", format="YYYY-MM-DD"),
        },
    )

    total_registros = len(transacciones_df.index)
    total = transacciones_df["monto"].fillna(0).astype(float).sum() if "monto" in transacciones_df.columns else 0

    metric_col1, metric_col2 = st.columns(2)
    metric_col1.metric("Registros", total_registros)
    metric_col2.metric("Total gastos", f"{total:,.2f}")
