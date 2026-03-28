import streamlit as st
import pandas as pd
from model.category_model import get_all_categories, batch_load_categoria, intert_categoria, update_categoria
from model.subcategory_model import get_subcategories_by_category, insert_subcategoria, update_subcategoria, soft_delete_subcategoria
                
st.session_state["show_add_form"] = st.session_state.get("show_add_form", False)
st.session_state["tc_update_mode"] = st.session_state.get("tc_update_mode", False)
st.session_state["show_add_sub_form"] = st.session_state.get("show_add_sub_form", False)

st.title("Gestión de Categorías")

# Formulario para actualizar categoría
def formulario_actualizar_categoria():
    id_seleccionado = st.session_state.get('id_seleccionado')
    
    if id_seleccionado is None:
        st.error("Ninguna categoría seleccionada.")
        if st.button("Volver"):
            st.session_state['tc_update_mode'] = False
            st.rerun()
        return

    id_seleccionado = int(id_seleccionado)
    categorias_df = get_all_categories()
    
    # Asegurar mayúsculas para el frontend
    if not categorias_df.empty and 'categoriaid' in categorias_df.columns:
        categorias_df = categorias_df.rename(columns={
            'categoriaid': 'CategoriaId', 
            'categoria': 'Categoria', 
            'agrupacionpresupuesto': 'AgrupacionPresupuesto'
        })

    selected_rows = categorias_df[categorias_df['CategoriaId'] == id_seleccionado]
    if not selected_rows.empty:
        selected_row = selected_rows.iloc[0]
    else:
        st.error("No se encontró la categoría seleccionada.")
        if st.button("Volver"):
            st.session_state['tc_update_mode'] = False
            st.rerun()
        return

    with st.form("Actualizar_Registro", clear_on_submit=False):
        st.subheader("Actualizar registro")
        categoria = st.text_input("Descripción", selected_row.get('Categoria', ''), disabled=True)
        agrupamiento = st.text_input("Agrupamiento", selected_row.get('AgrupacionPresupuesto', ''), disabled=False)

        col1, col2 = st.columns(2)
        submit = col1.form_submit_button("Actualizar registro")
        cancel = col2.form_submit_button("Cancelar")
        if submit:
            update_categoria(id_seleccionado, categoria, agrupamiento)
            st.success("Registro actualizado!")
            st.session_state['tc_update_mode'] = False
            st.rerun()
        if cancel:
            st.session_state['tc_update_mode'] = False
            st.rerun()

    # Subcategories section
    st.divider()
    st.subheader("Subcategorías")
    
    # Load and display subcategories for this category
    subcategorias_df = get_subcategories_by_category(id_seleccionado)
    
    # Asegurar mayúsculas para las subcategorías
    if not subcategorias_df.empty and 'subcategoriaid' in subcategorias_df.columns:
        subcategorias_df = subcategorias_df.rename(columns={
            'subcategoriaid': 'SubCategoriaId',
            'categoriaid': 'CategoriaId',
            'nombrecategoria': 'NombreCategoria',
            'nombresubcategoria': 'NombreSubCategoria'
        })
    
    if not subcategorias_df.empty:
        subcategorias_event = st.dataframe(
            subcategorias_df,
            on_select="rerun",
            selection_mode=["single-row"],
            column_config={"SubCategoriaId": None, "CategoriaId": None},
            use_container_width=True,
            hide_index=True
        )
        
        selection = subcategorias_event.selection
        id_subcategoria_seleccionado = subcategorias_df.iloc[0]['SubCategoriaId']
        
        if len(selection.rows) > 0:
            selected_row_sub = selection.rows[0]
            id_subcategoria_seleccionado = subcategorias_df.iloc[selected_row_sub]['SubCategoriaId']
    else:
        st.info("No hay subcategorías registradas para esta categoría.")
        id_subcategoria_seleccionado = None
    
    # Buttons for subcategory management
    sub_col1, sub_col2, sub_col3 = st.columns(3)
    with sub_col1:
        if st.button("Agregar Subcategoría"):
            st.session_state["show_add_sub_form"] = True
            st.session_state["tc_update_mode"] = False
            st.session_state["show_add_form"] = False
            st.rerun()
    with sub_col2:
        if st.button("Actualizar Subcategoría", disabled=id_subcategoria_seleccionado is None):
            if id_subcategoria_seleccionado is not None:
                st.session_state["show_update_sub_form"] = True
                st.session_state["tc_update_mode"] = False
                st.session_state["show_add_form"] = False
                st.session_state["show_add_sub_form"] = False
                st.session_state["id_subcategoria_seleccionado"] = id_subcategoria_seleccionado
                st.rerun()
    with sub_col3:
        if st.button(f"Eliminar Subcategoría", disabled=id_subcategoria_seleccionado is None):
            if id_subcategoria_seleccionado is not None:
                result = soft_delete_subcategoria(id_subcategoria_seleccionado)
                if result == "Soft delete complete!":
                    st.success("Subcategoría eliminada correctamente.")
                    st.rerun()
                else:
                    st.error(f"Error al eliminar la subcategoría: {result}")

def formulario_actualizar_subcategoria():
    id_categoria = st.session_state.get('id_seleccionado')
    subcategorias_df = get_subcategories_by_category(id_categoria)
    
    if not subcategorias_df.empty and 'subcategoriaid' in subcategorias_df.columns:
        subcategorias_df = subcategorias_df.rename(columns={
            'subcategoriaid': 'SubCategoriaId',
            'categoriaid': 'CategoriaId',
            'nombrecategoria': 'NombreCategoria',
            'nombresubcategoria': 'NombreSubCategoria'
        })

    if subcategorias_df.empty:
        st.info("No hay subcategorías para actualizar.")
        if st.button("Volver"):
            st.session_state["show_update_sub_form"] = False
            st.session_state["tc_update_mode"] = True
            st.rerun()
        return

    id_subcategoria_seleccionado = st.session_state.get('id_subcategoria_seleccionado', None)
    if id_subcategoria_seleccionado is None:
        id_subcategoria_seleccionado = subcategorias_df.iloc[0]['SubCategoriaId']
        
    subcat_row = subcategorias_df[subcategorias_df['SubCategoriaId'] == id_subcategoria_seleccionado]
    if subcat_row.empty:
        st.error("No se encontró la subcategoría seleccionada.")
        return
        
    subcat_row = subcat_row.iloc[0]
    st.title("Actualizar Subcategoría")
    
    with st.form("update_subcategory", clear_on_submit=True):
        nombre_subcategoria = st.text_input("Nombre de la Subcategoría", value=subcat_row['NombreSubCategoria'])
        submitted = st.form_submit_button("Actualizar")
        cancel = st.form_submit_button("Cancelar")
        
        if submitted:
            if nombre_subcategoria.strip():
                result = update_subcategoria(id_subcategoria_seleccionado, nombre_subcategoria)
                if result == "update_exitoso":
                    st.success(f"Subcategoría actualizada correctamente.")
                    st.session_state["show_update_sub_form"] = False
                    st.session_state["tc_update_mode"] = True
                    st.rerun()
                else:
                    st.error(f"Error al actualizar la subcategoría. Por favor, intente nuevamente.")
            else:
                st.error("El nombre de la subcategoría no puede estar vacío.")
        elif cancel:
            st.session_state["show_update_sub_form"] = False
            st.session_state["tc_update_mode"] = True
            st.rerun()

def formulario_agregar_subcategoria():
    id_categoria = st.session_state.get('id_seleccionado')
    st.title("Agregar Subcategoría")
    with st.form("register_subcategory", clear_on_submit=True):
        nombre_subcategoria = st.text_input("Nombre de la Subcategoría")
        submitted = st.form_submit_button("Grabar")
        cancel = st.form_submit_button("Cancelar")
        if submitted:
            if nombre_subcategoria.strip():
                result = insert_subcategoria(nombre_subcategoria, id_categoria)
                if result == "insert_exitoso":
                    st.success(f"Subcategoría '{nombre_subcategoria}' registrada correctamente.")
                    st.session_state["show_add_sub_form"] = False
                    st.session_state["tc_update_mode"] = True
                    st.rerun()
                else:
                    st.error(f"Error al registrar la subcategoría '{nombre_subcategoria}'. Por favor, intente nuevamente.")
            else:
                st.error("El nombre de la subcategoría no puede estar vacío.")
        elif cancel:
            st.session_state["show_add_sub_form"] = False
            st.session_state["tc_update_mode"] = True
            st.rerun()

def formulario_agregar_categoria():
    with st.form("register_category", clear_on_submit=True):
        categoria = st.text_input("Nombre de la Categoría")
        agrupamiento = st.text_input("Agrupamiento (opcional)")
        submitted = st.form_submit_button("Registrar")
        cancel = st.form_submit_button("Cancelar")
        if submitted:
            if categoria.strip():
                result = intert_categoria(categoria, agrupamiento)
                st.success(f"Categoría '{categoria}' registrada correctamente. {result}")
                st.session_state["show_add_form"] = False
                st.rerun() 
            else:
                st.error("El nombre de la categoría no puede estar vacío.")
        elif cancel:
            st.session_state["show_add_form"] = False
            st.rerun()  

def main():
    # Load and display categories
    categorias_df = get_all_categories()
    
    # Asegurar mayúsculas para el frontend
    if not categorias_df.empty and 'categoriaid' in categorias_df.columns:
        categorias_df = categorias_df.rename(columns={
            'categoriaid': 'CategoriaId', 
            'categoria': 'Categoria', 
            'agrupacionpresupuesto': 'AgrupacionPresupuesto'
        })
        
    st.subheader("Categorías registradas")
    
    if categorias_df.empty:
        st.info("No hay categorías registradas aún. ¡Agrega la primera para empezar!")
        id_seleccionado = None
    else:
        categorias_event = st.dataframe(categorias_df,
                        on_select="rerun",
                        selection_mode=["single-row"],
                        column_config={"CategoriaId":None},
                        use_container_width=True,
                        hide_index=True)
        
        selection = categorias_event.selection
        id_seleccionado = categorias_df.iloc[0]['CategoriaId']

        if len(selection.rows) > 0:
            selected_row = selection.rows[0]
            id_seleccionado = categorias_df.iloc[selected_row]['CategoriaId']

    st.session_state['id_seleccionado'] = id_seleccionado
    
    # Botones en tres columnas para eficiencia
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        if st.button("Agregar Categoría"):
            st.session_state["show_add_form"] = True
            st.rerun()
    with btn_col2:
        if st.button("Actualizar registro", disabled=id_seleccionado is None):
            st.session_state["tc_update_mode"] = True
            st.rerun()
    with btn_col3:
        if st.button("Eliminar registro", disabled=id_seleccionado is None):
            from model.category_model import soft_delete_categoria
            update_message = soft_delete_categoria(id_seleccionado)
            if update_message == "Soft delete complete!":
                st.success(update_message)
                st.rerun()
            else:
                st.error(update_message)

# Exclusive view logic: show only one form or the main view
if st.session_state.get("show_update_sub_form", False):
    formulario_actualizar_subcategoria()
elif st.session_state["show_add_sub_form"]:
    formulario_agregar_subcategoria()
elif st.session_state['tc_update_mode']:
    formulario_actualizar_categoria()
elif st.session_state["show_add_form"]:
    formulario_agregar_categoria()
else:
    main()