import streamlit as st
import pandas as pd   
from crud import batch_load_categoria 

if "df" not in st.session_state:
    st.session_state.df = None  # Start with no DataFrame loaded

# File uploader for Excel files
uploaded_file = st.file_uploader("Choose an Excel file to load the categories", type=["xlsx"])

# Placeholder for the grid display
grid_placeholder = st.empty()

if uploaded_file is not None:
    # Read the uploaded Excel file
    try:
        st.session_state.df = pd.read_excel(uploaded_file, sheet_name=0)  # Reads the first sheet
        
        # VALIDACIÓN 1: ¿El Excel está vacío?
        if st.session_state.df.empty:
            st.warning("El archivo Excel que subiste está vacío. Por favor verifica el archivo.")
        else:
            # VALIDACIÓN 2: ¿Tiene las columnas correctas?
            expected_columns = ['Categoria', 'Agrupamiento']
            missing_cols = [col for col in expected_columns if col not in st.session_state.df.columns]
            
            if missing_cols:
                st.error(f"El archivo no tiene el formato correcto. Faltan las siguientes columnas: {', '.join(missing_cols)}")
                st.info("Asegúrate de que los encabezados del Excel sean exactamente 'Categoria' y 'Agrupamiento'.")
            else:
                st.write("### Displaying data from the first sheet, validate if data is ok for loading:")
                grid_placeholder.dataframe(st.session_state.df)

                if st.button("Load Categorias"):
                    load_message = batch_load_categoria(st.session_state.df)

                    if "Load complete!" in load_message:
                        st.success(load_message)
                        st.session_state.df = None  # Clear the DataFrame from session state
                        grid_placeholder.empty()     # Clear the placeholder content
                    else: 
                        st.error(load_message)

    except Exception as e:
        st.error(f"Error reading the spreadsheet: {e}")
else:
    st.info("Upload an Excel file to display its contents.")