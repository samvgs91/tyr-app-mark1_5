import streamlit as st
import pandas as pd
from datetime import datetime
from crud import (
    get_all_budgets, 
    insert_cabecera_presupuesto, 
    update_cabecera_presupuesto, 
    delete_cabecera_presupuesto,
    get_all_subcategories,
    get_all_monedas,
    get_presupuesto,
    get_detalle_presupuesto,
    soft_delete_detalle_presupuesto,
    batch_load_detalle_presupuesto,
    create_detalle_presupuesto,
    soft_delete_all_detalle_por_presupuesto_id
)

from util import parsear_detalle_presupuesto

# Status dictionary
status_options = {
    "Borrador": "Draft", 
    "En Validación": "Under Review",
    "Confirmado": "Confirmed"
}

# Month mapping
month_mapping = {
    "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4,
    "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8,
    "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12
}

def show_manage_budget_details(budget_id):

    detalle_presupuesto_df = get_detalle_presupuesto(budget_id)

    if not detalle_presupuesto_df.empty:
        st.dataframe(detalle_presupuesto_df)
        selected_budget_details_id = st.selectbox("Id de detalle de Presupuesto",detalle_presupuesto_df[['id']])

        if st.button(f"Eliminar Detalle de Presupuesto Registro {selected_budget_details_id}"):
            delete_message=soft_delete_detalle_presupuesto(selected_budget_details_id)

            if "Soft delete complete!" in delete_message:
                st.success(delete_message)
                st.rerun()
            else: 
                st.error(delete_message)
    else:
        st.write(f"No hay detalles para este presupuesto")

def run_manage_budgets():
    st.title("Manage Budgets")
    
    # Check if we're in add or update mode and show only those forms
    if 'add_mode' in st.session_state and st.session_state['add_mode']:
        show_add_budget_form()
        return
    
    if 'update_mode' in st.session_state and st.session_state['update_mode']:
        show_update_budget_form()
        return

    # Fetch budgets and display them in a grid
    budgets = get_all_budgets()

    if not budgets.empty:
        # Renombramos las columnas para que coincidan con las expectativas del frontend
        budgets = budgets.rename(columns={
            'anio': 'Anio', 
            'nombremes': 'NombreMes', 
            'status': 'Status', 
            'version': 'Version'
        })
        
        st.subheader("Available Budgets")
        event = st.dataframe(budgets[['id', 'Anio', 'NombreMes', 'Status', 'Version']],               
                on_select="rerun",
                selection_mode=["single-row"],
                column_config={"id":None},
                hide_index=True, 
                use_container_width=True,  )
        
        selection = event.selection
        id_seleccionado = None

        if st.button("Add New Budget"):
            st.session_state['add_mode'] = True
            st.session_state['update_mode'] = False
            st.session_state['clone_mode'] = False
            st.rerun()  # Refresh the page to show add interface

        # VALIDACIÓN AÑADIDA: Solo proceder si hay una fila seleccionada
        if len(selection.rows) > 0:
            selected_row = selection.rows[0]
            id_seleccionado = budgets.iloc[selected_row]['id']
            selected_budget_id = id_seleccionado
            
            # Extraer el presupuesto seleccionado
            selected_budget = budgets[budgets['id'] == selected_budget_id].iloc[0]
            st.session_state['budget_id'] = selected_budget_id

            if st.button(f"Update Budget {selected_budget_id}"):
                st.session_state['selected_budget'] = selected_budget
                st.session_state['update_mode'] = True
                st.session_state['add_mode'] = False
                st.session_state['clone_mode'] = False
                st.rerun()

            if st.button(f"Delete Budget {selected_budget_id}"):
                delete_message = soft_delete_all_detalle_por_presupuesto_id(int(selected_budget_id))
                cabecera_delete_message = delete_cabecera_presupuesto(int(selected_budget_id))
                
                if "Soft delete complete!" in delete_message and "Budget deleted successfully!" in cabecera_delete_message  :
                    st.success(f"Budget {selected_budget_id} deleted successfully!")
                    st.rerun()  # Refresh the page after deletion
                else:
                    st.error(f"Failed to delete budget {selected_budget_id}.")

            if st.button("Clone New Budget"):
                st.session_state['clone_mode'] = True
                st.session_state['add_mode'] = False
                st.session_state['update_mode'] = False
                st.rerun()  # Refresh the page to show clone interface

    else:
        st.write("No budgets available.")
        if st.button("Add New Budget"):
            st.session_state['add_mode'] = True
            st.session_state['update_mode'] = False
            st.rerun()

def show_add_budget_form():
    # Check if we're in add or edit detail mode within add budget form
    if 'add_detail_in_add_mode' in st.session_state and st.session_state['add_detail_in_add_mode']:
        show_add_detail_for_new_budget()
        return
    
    if 'edit_detail_in_add_mode' in st.session_state and st.session_state['edit_detail_in_add_mode']:
        show_edit_detail_for_new_budget()
        return
    
    # Initialize empty budget details dataframe in session state if not exists
    if 'new_budget_details' not in st.session_state:
        st.session_state['new_budget_details'] = pd.DataFrame(columns=['SubCategoria', 'SubCategoriaId', 'Moneda', 'MonedaId', 'Monto'])
    
    # Display budget details section OUTSIDE the form
    st.subheader("Budget Details (Preview)")
    if not st.session_state['new_budget_details'].empty:
        display_df = st.session_state['new_budget_details'][['SubCategoria', 'Moneda', 'Monto']].copy()
        event = st.dataframe(
            display_df,
            on_select="rerun",
            selection_mode=["single-row"],
            hide_index=True,
            use_container_width=True
        )
        
        # Check if a row is selected
        selection = event.selection
        if len(selection.rows) > 0:
            selected_row = selection.rows[0]
            st.write(f"Selected Detail Row: {selected_row + 1}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Edit Selected Detail", key="edit_detail_new"):
                    st.session_state['edit_detail_in_add_mode'] = True
                    st.session_state['selected_detail_row'] = selected_row
                    st.rerun()
            
            with col2:
                if st.button("Delete Selected Detail", key="delete_detail_new"):
                    st.session_state['new_budget_details'] = st.session_state['new_budget_details'].drop(
                        st.session_state['new_budget_details'].index[selected_row]
                    ).reset_index(drop=True)
                    st.success("Detail removed from preview!")
                    st.rerun()
            
            with col3:
                if st.button("Add New Detail", key="add_detail_new"):
                    st.session_state['add_detail_in_add_mode'] = True
                    st.rerun()
        else:
            if st.button("Add New Detail", key="add_detail_new_no_selection"):
                st.session_state['add_detail_in_add_mode'] = True
                st.rerun()
    else:
        st.info("No budget details added yet. Add details below.")
        if st.button("Add New Detail", key="add_detail_empty"):
            st.session_state['add_detail_in_add_mode'] = True
            st.rerun()
    
    st.divider()
    
    with st.form("Add_Budget", clear_on_submit=True):
        st.subheader("Add New Budget Header")
        anio = st.number_input("Año", min_value=2020, max_value=datetime.now().year)
        selected_month = st.selectbox("Mes", list(month_mapping.keys()))
        num_mes = month_mapping[selected_month]
        status = st.selectbox("Estado del Presupuesto", list(status_options.keys()))
        version = st.number_input("Versión", min_value=1)
        
        # Two columns for buttons
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Submit New Budget")
        with col2:
            cancelled = st.form_submit_button("Cancel")
        
        if submitted:
            # Insert budget header first
            new_budget_id = insert_cabecera_presupuesto(anio, num_mes, selected_month, status, version)
            
            # Insert budget details if any exist
            if not st.session_state['new_budget_details'].empty:
                for _, row in st.session_state['new_budget_details'].iterrows():
                    create_detalle_presupuesto(
                        new_budget_id, 
                        int(row['SubCategoriaId']), 
                        int(row['MonedaId']), 
                        float(row['Monto'])
                    )
            
            st.success("Budget header and details added successfully!")
            # Clean up session state
            st.session_state['add_mode'] = False
            if 'new_budget_details' in st.session_state:
                del st.session_state['new_budget_details']
            st.rerun()
        
        if cancelled:
            st.session_state['add_mode'] = False
            if 'new_budget_details' in st.session_state:
                del st.session_state['new_budget_details']
            st.rerun()

def show_add_detail_for_new_budget():
    st.subheader("Add New Budget Detail")
    
    # Get subcategories and currencies for dropdowns
    subcategorias_df = get_all_subcategories()
    monedas_df = get_all_monedas()
    
    with st.form("Add_Detail_New_Budget", clear_on_submit=True):
        subcategoria = st.selectbox(
            "Subcategoría",
            options=subcategorias_df['nombresubcategoria'].tolist() if not subcategorias_df.empty else [],
            key="add_subcat_new_budget"
        )
        
        moneda = st.selectbox(
            "Moneda",
            options=monedas_df['Moneda'].tolist() if not monedas_df.empty else [],
            key="add_moneda_new_budget"
        )
        
        monto = st.number_input("Monto", min_value=0.0, format="%.2f", key="add_monto_new_budget")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Add Detail")
        with col2:
            cancelled = st.form_submit_button("Cancel")
        
        if submitted:
            if subcategorias_df.empty or monedas_df.empty:
                st.error("No hay subcategorías o monedas registradas.")
            else:
                subcategoria_id = subcategorias_df[subcategorias_df['nombresubcategoria'] == subcategoria]['subcategoriaid'].iloc[0]
                moneda_id = monedas_df[monedas_df['Moneda'] == moneda]['MonedaId'].iloc[0]
                
                # Add to session state dataframe
                new_row = pd.DataFrame({
                    'SubCategoria': [subcategoria],
                    'SubCategoriaId': [subcategoria_id],
                    'Moneda': [moneda],
                    'MonedaId': [moneda_id],
                    'Monto': [monto]
                })
                st.session_state['new_budget_details'] = pd.concat(
                    [st.session_state['new_budget_details'], new_row], 
                    ignore_index=True
                )
                
                st.success("Detail added to preview!")
                st.session_state['add_detail_in_add_mode'] = False
                st.rerun()
        
        if cancelled:
            st.session_state['add_detail_in_add_mode'] = False
            st.rerun()

def show_edit_detail_for_new_budget():
    selected_row = st.session_state['selected_detail_row']
    selected_detail = st.session_state['new_budget_details'].iloc[selected_row]
    
    st.subheader(f"Edit Budget Detail Row: {selected_row + 1}")
    
    # Get subcategories and currencies for dropdowns
    subcategorias_df = get_all_subcategories()
    monedas_df = get_all_monedas()
    
    # Find current indices
    try:
        current_subcategoria_index = subcategorias_df[
            subcategorias_df['nombresubcategoria'] == selected_detail['SubCategoria']
        ].index[0]
    except:
        current_subcategoria_index = 0
    
    try:
        current_moneda_index = monedas_df[
            monedas_df['Moneda'] == selected_detail['Moneda']
        ].index[0]
    except:
        current_moneda_index = 0
    
    with st.form("Edit_Detail_New_Budget", clear_on_submit=True):
        subcategoria = st.selectbox(
            "Subcategoría",
            options=subcategorias_df['nombresubcategoria'].tolist() if not subcategorias_df.empty else [],
            index=current_subcategoria_index,
            key="edit_subcat_new_budget"
        )
        
        moneda = st.selectbox(
            "Moneda",
            options=monedas_df['Moneda'].tolist() if not monedas_df.empty else [],
            index=current_moneda_index,
            key="edit_moneda_new_budget"
        )
        
        monto = st.number_input(
            "Monto", 
            min_value=0.0, 
            format="%.2f", 
            value=float(selected_detail['Monto']), 
            key="edit_monto_new_budget"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Update Detail")
        with col2:
            cancelled = st.form_submit_button("Cancel")
        
        if submitted:
            if subcategorias_df.empty or monedas_df.empty:
                st.error("No hay subcategorías o monedas registradas.")
            else:
                subcategoria_id = subcategorias_df[subcategorias_df['nombresubcategoria'] == subcategoria]['subcategoriaid'].iloc[0]
                moneda_id = monedas_df[monedas_df['Moneda'] == moneda]['MonedaId'].iloc[0]
                
                # Update the row in session state dataframe
                st.session_state['new_budget_details'].at[selected_row, 'SubCategoria'] = subcategoria
                st.session_state['new_budget_details'].at[selected_row, 'SubCategoriaId'] = subcategoria_id
                st.session_state['new_budget_details'].at[selected_row, 'Moneda'] = moneda
                st.session_state['new_budget_details'].at[selected_row, 'MonedaId'] = moneda_id
                st.session_state['new_budget_details'].at[selected_row, 'Monto'] = monto
                
                st.success("Detail updated in preview!")
                st.session_state['edit_detail_in_add_mode'] = False
                st.rerun()
        
        if cancelled:
            st.session_state['edit_detail_in_add_mode'] = False
            st.rerun()

def show_update_budget_form():
    selected_budget = st.session_state['selected_budget']
    budget_id = int(selected_budget['id'])
    
    # Check if we're in edit or add detail mode
    if 'edit_detail_mode' in st.session_state and st.session_state['edit_detail_mode']:
        show_edit_detail_form(budget_id)
        return
    
    if 'add_detail_mode' in st.session_state and st.session_state['add_detail_mode']:
        show_add_detail_form(budget_id)
        return
    
    # Display budget details OUTSIDE the form
    st.subheader("Budget Details")
    detalle_presupuesto_df = get_detalle_presupuesto(budget_id)
    if not detalle_presupuesto_df.empty:
        event = st.dataframe(
            detalle_presupuesto_df,
            on_select="rerun",
            selection_mode=["single-row"],
            hide_index=True,
            use_container_width=True
        )
        
        # Check if a row is selected
        selection = event.selection
        if len(selection.rows) > 0:
            selected_row = selection.rows[0]
            selected_detail_id = detalle_presupuesto_df.iloc[selected_row]['id']
            st.write(f"Selected Budget Detail ID: {selected_detail_id}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Edit Selected Detail"):
                    st.session_state['edit_detail_mode'] = True
                    st.session_state['selected_detail_id'] = selected_detail_id
                    st.session_state['selected_detail'] = detalle_presupuesto_df.iloc[selected_row]
                    st.rerun()
            
            with col2:
                if st.button("Delete Selected Detail"):
                    delete_message = soft_delete_detalle_presupuesto(selected_detail_id)
                    if "Soft delete complete!" in delete_message:
                        st.success(delete_message)
                        st.rerun()
                    else:
                        st.error(delete_message)
            
            with col3:
                if st.button("Add New Detail"):
                    st.session_state['add_detail_mode'] = True
                    st.rerun()
        else:
            if st.button("Add New Detail"):
                st.session_state['add_detail_mode'] = True
                st.rerun()
    else:
        st.info("No budget details found for this budget.")
        if st.button("Add New Detail"):
            st.session_state['add_detail_mode'] = True
            st.rerun()
    
    st.divider()  # Visual separator
    
    # Reverse lookup to find the month name from the number
    try:
        month_name = [key for key, value in month_mapping.items() if value == selected_budget['NumMes']][0]
    except IndexError:
        # Fallback in case NumMes is missing or invalid
        month_name = list(month_mapping.keys())[0]
    
    with st.form("Update_Budget", clear_on_submit=True):
        st.subheader(f"Update Budget Header (ID: {budget_id})")
        anio = st.number_input("Año", value=int(selected_budget.get('Anio', datetime.now().year)))
        
        # Correctly set the index based on the reverse lookup of the month
        selected_month = st.selectbox("Mes", list(month_mapping.keys()), index=list(month_mapping.keys()).index(month_name))
        
        num_mes = month_mapping[selected_month]
        status_val = selected_budget.get('Status', list(status_options.keys())[0])
        status = st.selectbox("Estado del Presupuesto", list(status_options.keys()), index=list(status_options.keys()).index(status_val))
        version = st.number_input("Versión", value=int(selected_budget.get('Version', 1)))
        
        col1, col2 = st.columns(2)
        submitted = col1.form_submit_button("Submit Updates")
        cancelled = col2.form_submit_button("Cancel")
        
        if submitted:
            update_cabecera_presupuesto(budget_id, anio, num_mes, selected_month, status, version)
            st.success("Budget header updated successfully!")
            st.session_state['update_mode'] = False
            st.rerun()
        
        if cancelled:
            st.session_state['update_mode'] = False
            st.rerun()

def show_add_detail_form(budget_id):
    st.subheader(f"Add New Budget Detail for Budget ID: {budget_id}")
    
    # Get subcategories and currencies for dropdowns
    subcategorias_df = get_all_subcategories()
    monedas_df = get_all_monedas()
    
    with st.form("Add_Detail", clear_on_submit=True):
        subcategoria = st.selectbox(
            "Subcategoría",
            options=subcategorias_df['nombresubcategoria'].tolist() if not subcategorias_df.empty else [],
            key="add_subcategoria"
        )
        
        moneda = st.selectbox(
            "Moneda",
            options=monedas_df['Moneda'].tolist() if not monedas_df.empty else [],
            key="add_moneda"
        )
        
        monto = st.number_input("Monto", min_value=0.0, format="%.2f", key="add_monto")
        
        # Two columns for buttons
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Submit")
        with col2:
            cancelled = st.form_submit_button("Cancel")
        
        if submitted:
            if subcategorias_df.empty or monedas_df.empty:
                st.error("No hay subcategorías o monedas registradas.")
            else:
                # Get IDs from the dataframes
                subcategoria_id = subcategorias_df[subcategorias_df['nombresubcategoria'] == subcategoria]['subcategoriaid'].iloc[0]
                moneda_id = monedas_df[monedas_df['Moneda'] == moneda]['MonedaId'].iloc[0]
                
                # Create the budget detail using the new function
                result = create_detalle_presupuesto(budget_id, subcategoria_id, moneda_id, monto)
                if "Create complete!" in result:
                    st.success("Budget detail added successfully!")
                    st.session_state['add_detail_mode'] = False
                    st.rerun()
                else:
                    st.error("Failed to add budget detail.")
        
        if cancelled:
            st.session_state['add_detail_mode'] = False
            st.rerun()

def show_edit_detail_form(budget_id):
    selected_detail = st.session_state['selected_detail']
    detail_id = st.session_state['selected_detail_id']
    
    st.subheader(f"Edit Budget Detail ID: {detail_id}")
    
    # Get subcategories and currencies for dropdowns
    subcategorias_df = get_all_subcategories()
    monedas_df = get_all_monedas()
    
    # Find current indices and convert to native Python int
    try:
        current_subcategoria_index = int(subcategorias_df[subcategorias_df['subcategoriaid'] == selected_detail['subcategoriaid']].index[0])
    except:
        current_subcategoria_index = 0
        
    try:
        current_moneda_index = int(monedas_df[monedas_df['MonedaId'] == selected_detail['monedaid']].index[0])
    except:
        current_moneda_index = 0
    
    with st.form("Edit_Detail", clear_on_submit=True):
        subcategoria = st.selectbox(
            "Subcategoría",
            options=subcategorias_df['nombresubcategoria'].tolist() if not subcategorias_df.empty else [],
            index=current_subcategoria_index,
            key="edit_subcategoria"
        )
        
        moneda = st.selectbox(
            "Moneda",
            options=monedas_df['Moneda'].tolist() if not monedas_df.empty else [],
            index=current_moneda_index,
            key="edit_moneda"
        )
        
        monto = st.number_input("Monto", min_value=0.0, format="%.2f", value=float(selected_detail.get('monto', 0.0)), key="edit_monto")
        
        # Two columns for buttons
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Update")
        with col2:
            cancelled = st.form_submit_button("Cancel")
        
        if submitted:
            if subcategorias_df.empty or monedas_df.empty:
                st.error("No hay subcategorías o monedas registradas.")
            else:
                # Get IDs from the dataframes
                subcategoria_id = subcategorias_df[subcategorias_df['nombresubcategoria'] == subcategoria]['subcategoriaid'].iloc[0]
                moneda_id = monedas_df[monedas_df['Moneda'] == moneda]['MonedaId'].iloc[0]
                
                # Update logic would go here - you'll need to create an update function in crud.py
                # For now, we'll delete and re-add (not ideal but functional)
                soft_delete_detalle_presupuesto(detail_id)
                
                new_detail_df = pd.DataFrame({
                    'CabeceraPresupuestoId': [budget_id],
                    'SubCategoriaId': [subcategoria_id],
                    'MonedaId': [moneda_id],
                    'Monto': [monto]
                })
                
                result = batch_load_detalle_presupuesto(new_detail_df, budget_id)
                if "Load complete!" == result:
                    st.success("Budget detail updated successfully!")
                    st.session_state['edit_detail_mode'] = False
                    st.rerun()
                else:
                    st.error("Failed to update budget detail.")
        
        if cancelled:
            st.session_state['edit_detail_mode'] = False
            st.rerun()

def cargar_presupuesto_detalle(budget_id:int, detalle_df: pd.DataFrame, skip_parsing: bool = False) -> bool:
        st.write(f"Cargar detalle de presupuesto para el Budget ID: {budget_id}")
        
        if detalle_df.empty:
            st.error("No valid data to load after removing empty rows.")
            return False
        
        # Skip parsing if data already has IDs (e.g., when cloning from existing budget)
        if skip_parsing:
            presupuesto_df = detalle_df
        else:
            presupuesto_df = parsear_detalle_presupuesto(raw_detalle_presupuesto_df=detalle_df)    

        print(presupuesto_df)

        if presupuesto_df['subcategoriaid'].isnull().any() or presupuesto_df['monedaid'].isnull().any():
            presupuesto_df['tieneerror'] = presupuesto_df['subcategoriaid'].isnull() | presupuesto_df['monedaid'].isnull()
            st.session_state.budget_details = presupuesto_df[["subcategoria", "moneda", "monto","tieneerror"]]
            warning_message='Algunas sub categorias o monedas no están registradas'
            st.error(warning_message)
            return False
        else:
            # Filter out any remaining NaN values before loading
            presupuesto_df_clean = presupuesto_df.dropna(subset=['subcategoriaid', 'monedaid', 'monto'])
            
            if presupuesto_df_clean.empty:
                st.error("No valid data after validation.")
                return False
                
            if "Load complete!" == batch_load_detalle_presupuesto(presupuesto_df_clean, budget_id):
                return True
            else:
                return False

def main() -> None:
    """
    Docstring for main
    """

    # need to validate if clone_mode is set to true if is set to true I want to show a dummy dataframe table from streamlit else I want to show the run manage_budgets function
    if 'clone_mode' in st.session_state and st.session_state['clone_mode']:
        st.write("Clone Mode Activated - Show Clone Budget Interface Here")

        selected_budget_id = st.session_state['budget_id']

        cabecera_presupuesto = get_presupuesto(selected_budget_id)
        
        # Extract scalar values from the DataFrame
        anio_value = int(cabecera_presupuesto['anio'].iloc[0])
        nombre_mes_value = str(cabecera_presupuesto['nombremes'].iloc[0])
        status_value = str(cabecera_presupuesto['status'].iloc[0])
        version_value = int(cabecera_presupuesto['version'].iloc[0])

        anio = st.number_input("Año", 
                            min_value=2020, 
                            max_value=datetime.now().year,
                            value=anio_value)
        
        try:
            mes_index = list(month_mapping.keys()).index(nombre_mes_value)
        except ValueError:
            mes_index = 0
            
        selected_month = st.selectbox("Mes", 
                                    list(month_mapping.keys()), 
                                    index=mes_index)
        num_mes = month_mapping[selected_month]

        try:
            status_index = list(status_options.keys()).index(status_value)
        except ValueError:
            status_index = 0
            
        status = st.selectbox("Estado del Presupuesto", 
                            list(status_options.keys()),
                            index=status_index)
        
        version = st.number_input("Versión", min_value=1, value=version_value)

        detalle_presupuesto_df = get_detalle_presupuesto(selected_budget_id)

        event = st.dataframe(detalle_presupuesto_df,               
                on_select="rerun",
                selection_mode=["single-row"],
                column_config={"id":None},
                hide_index=True, 
                use_container_width=True,  )

        if st.button("Guardar"):
                # Insert new budget header
                new_budget_id = insert_cabecera_presupuesto(anio, num_mes, selected_month, status, version)
                st.success(f"Budget header created with ID: {new_budget_id}")

                # Load budget details into the new budget (skip parsing since data already has IDs)
                load_success = cargar_presupuesto_detalle(new_budget_id, detalle_presupuesto_df, skip_parsing=True)

                if load_success:
                    st.success("Presupuesto clonado exitosamente!")
                    st.session_state['clone_mode'] = False
                    st.session_state['add_mode'] = False
                    st.session_state['update_mode'] = False
                    st.rerun()
                else:
                    st.error("Failed to load budget details. Please check the data.")

        if st.button("Cancelar"):
                st.session_state['clone_mode'] = False
                st.session_state['add_mode'] = False
                st.session_state['update_mode'] = False
                st.rerun() 

    else:           
        run_manage_budgets()

main()