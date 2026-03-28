import streamlit as st
import pandas as pd
from datetime import datetime, date
from crud import *
from ai_module import *
import pandas as pd
from util import * # Replace with actual functions/classes needed from util
from utilitaries.session import init_session_state,reset_on_expense_type_change
from utilitaries.month_mapping import month_mapping, years_data,get_month_range,expense_type_mapping
from utilitaries.master_data import load_subcategories_df
from services.credit_card_transformation import procesar_registros

init_session_state()

# --- VALIDACIÓN DEFENSIVA PARA EL MAESTRO DE SUBCATEGORÍAS ---
SUBCATEGORIAS_PD = load_subcategories_df()
if not SUBCATEGORIAS_PD.empty and 'nombresubcategoria' in SUBCATEGORIAS_PD.columns:
    nombres_lista = SUBCATEGORIAS_PD['nombresubcategoria'].tolist()
    subcategorias_dic = {nombre: i+1 for i, nombre in enumerate(nombres_lista)}
else:
    subcategorias_dic = {}

st.set_page_config(page_title="Registrar Gastos (Cuentas Bancaria & Tarjeta de Crédito)", layout="centered")
st.title("💸 Registrar Gastos (Cuentas Bancaria & Tarjeta de Crédito)")


def formulario_procesar_gastos(expense_type_code:int):
    with st.form("Procesar_Registro", clear_on_submit=False):
        st.subheader("Procesar registros de gastos")
        excel_gastos_tc = st.session_state['excel_gastos_tc']
        
        # Validar si el excel tiene datos antes de mostrar
        if excel_gastos_tc is None or excel_gastos_tc.empty:
            st.warning("No hay datos en el archivo cargado para procesar.")
            st.form_submit_button("Cerrar")
            return

        # ---------- DATAFRAME WITH SELECTION ----------
        event = st.dataframe(
            excel_gastos_tc,
            selection_mode=["multi-row"],
            on_select="rerun",
            use_container_width=True
        )

        # 🔍 Selected row indices
        selected_rows = event.selection["rows"]

        if len(selected_rows) == 0:
            selected_rows = list(range(len(excel_gastos_tc)))
            st.info(f"No hay filas seleccionadas. Se procesarán todas las {len(excel_gastos_tc)} filas.")
        else:
            st.write(f"Filas seleccionadas: {len(selected_rows)} de {len(excel_gastos_tc)}")

        submitted = st.form_submit_button("Procesar registros")
        cancel = st.form_submit_button("Cancelar")
        
        if submitted:
            st.info("🔄 Inicio procesando registros ...")
            # Filter dataframe to only selected rows
            excel_gastos_tc_filtered = excel_gastos_tc.iloc[selected_rows].copy()

            st.session_state['excel_gastos_tc_procesados'] = procesar_registros(excel_gastos_tc_filtered, expense_type_code)
            st.session_state['excel_gastos_tc'] = None
            excel_gastos_tc_procesados = st.session_state['excel_gastos_tc_procesados']
            insert_message = batch_load_transacciones(excel_gastos_tc_procesados)
            if insert_message == "Load complete!":
                st.session_state['excel_gastos_tc_procesados'] = None
                st.session_state['fecha_maxima_cargada'] = None
                st.success("Gastos cargados!")
                st.rerun()
            else:
                st.error(insert_message)
        elif cancel:
            st.session_state['excel_gastos_tc'] = None
            st.session_state['excel_gastos_tc_procesados'] = None
            st.session_state['tc_nuevos_registros_mode'] = False
            st.session_state['fecha_maxima_cargada'] = None
            st.info("Proceso cancelado.")
            st.rerun()

def mostrar_opcion_cargar_archivo(expense_type_code:int):
        # File uploader for Excel files
        uploaded_file = st.file_uploader("Elije el archivo de excel para cargar los gastos de tarjeta de credito", type=["xlsx"])

        if uploaded_file is not None:
            # Read the uploaded Excel file
            try:
                data_test_df = pd.read_excel(uploaded_file, sheet_name=0)  # Reads the first sheet
                data_test_df.columns = [str(col).lower().strip() for col in data_test_df.columns]
                
                # --- VALIDACIÓN DEFENSIVA PARA EL EXCEL ---
                if data_test_df.empty:
                    st.error("El archivo Excel está vacío.")
                    return
                
                if 'fecha' not in data_test_df.columns or 'monto' not in data_test_df.columns:
                    st.error("El archivo Excel debe contener las columnas exactas 'fecha' y 'monto'.")
                    return

                anio_seleccionado = st.session_state['anio_seleccionado']
                mes_seleccionado = st.session_state['mes_seleccionado']

                current_month = month_mapping.get(mes_seleccionado)
                start_date, end_date = get_month_range(anio_seleccionado, current_month)

                # filter depending on the type of expense
                if expense_type_code == 3:  # Gastos Tarjeta de Credito
                    data_test_df = data_test_df[(data_test_df['fecha'] > start_date) & (data_test_df['fecha'] < end_date) & (data_test_df['monto'] < 0)]
                    data_test_df['monto'] = data_test_df['monto'].abs()
                elif expense_type_code == 1:  # Gastos Cuenta Bancaria
                    data_test_df = data_test_df[(data_test_df['fecha'] > start_date) & (data_test_df['fecha'] < end_date)]
                    data_test_df['monto'] = data_test_df['monto'].abs()

                fecha_maxima_cargada = st.session_state.get('fecha_maxima_cargada')

                if fecha_maxima_cargada is not None:
                        try:
                            # Asegurarnos de que sea string antes de parsear
                            fecha_str = str(fecha_maxima_cargada)[:10] 
                            fecha_maxima_cargada_dt = datetime.strptime(fecha_str, '%Y-%m-%d')
                        except ValueError:
                            try:
                                fecha_maxima_cargada_dt = datetime.strptime(fecha_str, '%d/%m/%Y')
                            except ValueError:
                                st.warning("Formato de fecha no reconocido para la máxima fecha cargada. Se omitirá el filtro de fecha máxima.")
                                fecha_maxima_cargada_dt = None
                        if fecha_maxima_cargada_dt is not None:
                            fecha_maxima_cargada_str = fecha_maxima_cargada_dt.date().strftime('%Y-%m-%d')
                            data_test_df = data_test_df[data_test_df['fecha'] >= fecha_maxima_cargada_str]

                st.session_state.excel_gastos_tc = data_test_df

            except Exception as e:
                st.error(f"Error reading the spreadsheet: {e}")
        else:
            st.info("Carga un archivo excel con el detalle del presupuesto.")

def formulario_actualizar_registro():
    id_seleccionado = st.session_state['id_seleccionado']
    id_seleccionado = int(id_seleccionado)

    with st.form("Actualizar_Registro", clear_on_submit=False):
        st.subheader("Actualizar registro")
        registro_seleccionado = st.session_state['registro_seleccionado']

        # Validar si la fecha viene como string o como objeto datetime de la base de datos
        fecha_val = registro_seleccionado['fecha']
        if isinstance(fecha_val, str):
            valor_fecha = datetime.strptime(fecha_val[:10], "%Y-%m-%d").date()
        else:
            valor_fecha = fecha_val 
            
        fecha = st.date_input("Fecha", value=valor_fecha, disabled=True)
        descripcion = st.text_input("Descripción", registro_seleccionado.get('descripcion', ''), disabled=True)
        monto = st.number_input("Monto", float(registro_seleccionado.get('monto', 0.0)), disabled=True)
        
        # --- NUEVA LÓGICA A PRUEBA DE BALAS ---
        # 1. Cargamos los datos frescos en el momento
        subs_df = load_subcategories_df()

        # 3. Modo Diagnóstico: Si la tabla viene vacía, lo mostramos en pantalla
        if subs_df.empty or 'nombresubcategoria' not in subs_df.columns:
            st.error("⚠️ La base de datos no devolvió subcategorías a esta pantalla.")
            st.warning("💡 Diagnóstico: Es muy probable que la función 'get_all_subcategories()' en tu archivo 'crud.py' esté consultando una tabla con el nombre equivocado o esté fallando en silencio.")
            st.write("Datos en crudo recibidos de crud.py:", subs_df)
            st.form_submit_button("Cerrar")
            return

        # 4. Si hay datos, armamos el selectbox
        sub_list = subs_df['nombresubcategoria'].tolist()
        cat_actual = registro_seleccionado.get('subcategoria', 'Sin asignar')
        safe_index = sub_list.index(cat_actual) if cat_actual in sub_list else 0
        
        selected_subcategoria = st.selectbox("SubCategoria", sub_list, index=safe_index)
        
        # 5. Buscamos el ID exacto a guardar
        subcat_match = subs_df[subs_df['nombresubcategoria'] == selected_subcategoria]
        nuevo_id_subcategoria = subcat_match.iloc[0]['subcategoriaid'] if not subcat_match.empty else None
        # --------------------------------------

        submitted, cancel = st.columns(2)
        with submitted:
            submitted_btn = st.form_submit_button("Actualizar registro")
            if submitted_btn and nuevo_id_subcategoria is not None:  
                update_subcategoria_de_transaction(int(id_seleccionado), int(nuevo_id_subcategoria))
                st.success("Registro actualizado!")
                st.session_state['tc_update_mode'] = False
                st.rerun()
        with cancel:
            cancel_btn = st.form_submit_button("Cancelar")
            if cancel_btn:
                st.session_state['tc_update_mode'] = False
                st.rerun()

def administrar_registros():
        # mostrar meses 
        indice_mes = (datetime.now().month)-1

        col1, col2, col3 = st.columns(3)
        with col1:
            anio_seleccionado = st.selectbox("Año", years_data, index=0)
        with col2:
            mes_seleccionado = st.selectbox("Mes", list(month_mapping.keys()), index=indice_mes)
        with col3:
            expense_type = st.selectbox(
                "Tipo de gasto",
                list(expense_type_mapping.keys()),
                index=1,
                key="tipo_gasto_selectbox",
                on_change=reset_on_expense_type_change
            )

        st.session_state['expense_type'] = expense_type
        st.session_state['anio_seleccionado'] = anio_seleccionado
        st.session_state['mes_seleccionado'] = mes_seleccionado

        # Map expense type to code
        expense_type_code = expense_type_mapping.get(expense_type, 1)
        st.session_state['expense_type_code'] = expense_type_code

        gastos_tc = get_transacciones_by_month(anio_seleccionado, month_mapping.get(mes_seleccionado), [expense_type_code])
        

        st.text(f"Tipo de Gasto : {expense_type}")

        if not gastos_tc.empty:
            fecha_maxima_cargada = gastos_tc['fecha'].max()
            st.session_state['fecha_maxima_cargada'] = fecha_maxima_cargada

            st.subheader("Registros de gastos de tarjeta de credito")

            display_df = gastos_tc.rename(
                columns={
                    'fecha': 'Fecha',
                    'moneda': 'Moneda',
                    'monto': 'Monto',
                    'descripcion': 'Descripción',
                    'subcategoria': 'SubCategoria',
                }
            )[["id", "Fecha", "Moneda", "Monto", "Descripción", "SubCategoria"]]

            event = st.dataframe(
                display_df,
                on_select="rerun",
                selection_mode=["single-row"],
            )

            selection =  event.selection
            id_seleccionado = gastos_tc.iloc[0]['id']

            if len(selection.rows)>0:
                selected_row = selection.rows[0]
                id_seleccionado = gastos_tc.iloc[selected_row]['id']

            st.session_state['id_seleccionado'] = id_seleccionado

            # Guardar registro seleccionado
            registro_seleccionado = gastos_tc[gastos_tc['id'] == id_seleccionado].iloc[0]

            # Botones en tres columnas para eficiencia
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            with btn_col1:
                if st.button(f"Cargar nuevos registros"):
                    st.session_state['tc_nuevos_registros_mode'] = True
            with btn_col2:
                if st.button(f"Actualizar registro"):
                    st.session_state['tc_update_mode'] = True
                    st.session_state['registro_seleccionado'] = registro_seleccionado
            with btn_col3:
                if st.button(f"Eliminar registro : {id_seleccionado}"):
                    update_message = soft_delete_transaccion(id_seleccionado)
                    if update_message == "Soft delete complete!":
                        st.success(update_message)
                        st.rerun()
                    else:
                        st.error(update_message)

            # Botón separado para eliminar todos los registros del mes
            st.markdown("---")
            if st.button("🗑️ Eliminar TODOS los registros del mes", help="Esta acción eliminará todos los gastos del mes seleccionado."):
                update_message = soft_batch_delete_transacciones(anio_seleccionado, month_mapping.get(mes_seleccionado), [expense_type_code])
                if update_message == "Soft delete complete!":
                    st.success(update_message)
                    st.rerun()
                else:
                    st.error(update_message)

            if st.session_state.get('tc_update_mode', False):
                formulario_actualizar_registro()

            if st.session_state.get('tc_nuevos_registros_mode', False) is True:
                mostrar_opcion_cargar_archivo(expense_type_code=expense_type_code)

            if st.session_state.get('excel_gastos_tc') is not None: 
                    st.session_state['tc_nuevos_registros_mode'] = False
                    st.session_state['fecha_maxima_cargada'] = None
                    formulario_procesar_gastos(expense_type_code)   

        else:
            st.info("No hay transacciones registradas para este periodo.")
            #opcion para cargar archivo
            mostrar_opcion_cargar_archivo(expense_type_code)

            if st.session_state.get('excel_gastos_tc') is not None and st.session_state.get('excel_gastos_tc_procesados') is None:
                st.session_state['fecha_maxima_cargada'] = None
                formulario_procesar_gastos(expense_type_code)

administrar_registros()
