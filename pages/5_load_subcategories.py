import streamlit as st
import pandas as pd   
from crud import batch_load_subcategoria, get_all_categories

if "subcategoria" not in st.session_state:
    st.session_state.subcategoria = None  # Start with no DataFrame loaded

# File uploader for Excel files
uploaded_file = st.file_uploader("Choose an Excel file to load the sub categories", type=["xlsx"])

# Placeholder for the grid display
subcategoria_bch = st.empty()

if uploaded_file is not None:
    # Read the uploaded Excel file
    try:
        st.session_state.subcategoria = pd.read_excel(uploaded_file, sheet_name=0)  # Reads the first sheet
        
        # VALIDACIÓN 1: ¿El Excel está vacío?
        if st.session_state.subcategoria.empty:
            st.warning("El archivo Excel que subiste está vacío. Por favor verifica el archivo.")
        else:
            # VALIDACIÓN 2: ¿Tiene las columnas correctas?
            expected_columns = ['Categoria', 'SubCategoria']
            missing_cols = [col for col in expected_columns if col not in st.session_state.subcategoria.columns]
            
            if missing_cols:
                st.error(f"El archivo no tiene el formato correcto. Faltan las siguientes columnas: {', '.join(missing_cols)}")
                st.info("Asegúrate de que los encabezados del Excel sean exactamente 'Categoria' y 'SubCategoria'.")
            else:
                st.write("### Displaying data from the first sheet, validate if data is ok for loading:")
                subcategoria_bch.dataframe(st.session_state.subcategoria)

                if st.button("Load SubCategorias"):
                    categories = get_all_categories()
                    
                    # VALIDACIÓN 3: Asegurar mayúsculas para que el merge de Pandas no falle por culpa de Postgres
                    if not categories.empty and 'categoria' in categories.columns:
                        categories = categories.rename(columns={
                            'categoriaid': 'CategoriaId', 
                            'categoria': 'Categoria', 
                            'agrupacionpresupuesto': 'AgrupacionPresupuesto'
                        })
                        
                    load_message = batch_load_subcategoria(st.session_state.subcategoria, categories)

                    if "Load complete!" in load_message:
                        st.success(load_message)
                        st.session_state.subcategoria = None  # Clear the DataFrame from session state
                        subcategoria_bch.empty()     # Clear the placeholder content
                    else: 
                        st.error(load_message)

    except Exception as e:
        st.error(f"Error reading the spreadsheet: {e}")
else:
    st.info("Upload an Excel file to display its contents.")