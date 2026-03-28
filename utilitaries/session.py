"""
utils.session.py
Helper functions for Streamlit session state management.
"""
import streamlit as st


SESSION_NAMES = {
        'mes_seleccionado': None,
        'tc_update_mode': False,
        'test_subcategoria': 0,
        'id_seleccionado': None,
        'registro_seleccionado': None,
        'excel_gastos_tc': None,
        'excel_gastos_tc_procesados': None,
        'fecha_maxima_cargada': None,
        'tc_nuevos_registros_mode': None,
    }

def init_session_state():
    for key, value in SESSION_NAMES.items():
        if key not in st.session_state:
            st.session_state[key] = value


#asignando a nivel de sesion los valores del anio y el mes
def reset_on_expense_type_change():
    for key, value in SESSION_NAMES.items():
        st.session_state[key] = value