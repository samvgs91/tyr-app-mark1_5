import streamlit as st

st.set_page_config(
    page_title="TYR App MARK 1",
    page_icon="Tyr"
)

st.write("# Bienvenido a TYR App Mark 1! 👋")

st.sidebar.success("Es la primera opcion demo")

st.markdown(
    """
    Esta es la versión 1.5 de TYR App, 
    una aplicación de gestión financiera personal que utiliza inteligencia artificial para categorizar tus gastos automáticamente. 
    En esta versión, hemos mejorado la precisión del modelo de IA y añadido nuevas funcionalidades para facilitar el seguimiento de tus finanzas.
"""
)