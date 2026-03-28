from db import get_connection
import pandas as pd
from psycopg2.extras import execute_values
from model.model_util import *

# Actualiza el nombre de una subcategoría y la fecha de modificación
def update_subcategoria(subcategoria_id, nuevo_nombre):
    print(f"update_subcategoria called with subcategoria_id={subcategoria_id}, nuevo_nombre={nuevo_nombre}")
    try:
        conn = get_connection()
        print("Connection established")
        with conn:
            with conn.cursor() as cursor:
                sql = '''
                    UPDATE subcategoria
                    SET nombresubcategoria = %s,
                        fechamodificacion = CURRENT_TIMESTAMP,
                        modificadopor = %s
                    WHERE id = %s
                '''
                print(f"Executing SQL: {sql}")
                print(f"With params: nuevo_nombre={nuevo_nombre}, modificado_por=admin, subcategoria_id={subcategoria_id}")
                # Forzamos int para el parámetro
                cursor.execute(sql, (nuevo_nombre, 'admin', int(subcategoria_id)))
                conn.commit()
                print("Update committed")
        return "update_exitoso"
    except Exception as e:
        print(f"Error in update_subcategoria: {e}")
        return "error"

# Inserta una nueva subcategoría con valores por defecto para los campos no requeridos
def insert_subcategoria(nombre_subcategoria, categoria_id):
    print(f"insert_subcategoria called with categoria_id={categoria_id}, nombre_subcategoria={nombre_subcategoria}")
    try:
        conn = get_connection()
        print("Connection established")
        with conn:
            with conn.cursor() as cursor:
                sql = '''
                    INSERT INTO subcategoria
                        (categoriaid, nombresubcategoria, fechacreacion, fechamodificacion, modificadopor, eliminado)
                    VALUES
                        (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s, false)
                '''
                # Forzamos a entero por seguridad
                categoria_id_int = int(categoria_id)
                print(f"Executing SQL: {sql}")
                print(f"With params: categoria_id={categoria_id_int}, nombre_subcategoria={nombre_subcategoria}, modificado_por=admin")
                cursor.execute(sql, (categoria_id_int, nombre_subcategoria, 'admin'))
                conn.commit()
                print("Insert committed")
        return "insert_exitoso"
    except Exception as e:
        print(f"Error in insert_subcategoria: {e}")
        return "error"

def get_all_subcategories():
    conn = get_connection()
    query = '''
            SELECT 
                sc.id AS subcategoriaid,
                c.nombrecategoria AS nombrecategoria,
                sc.nombresubcategoria AS nombresubcategoria,
                ROW_NUMBER() OVER(ORDER BY sc.id ) AS ordenid
            FROM subcategoria as sc 
            LEFT JOIN categoria as c ON sc.categoriaid = c.id
            WHERE sc.eliminado = false
    '''
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_subcategories_by_category(categoria_id: int):
    conn = get_connection()
    # Usamos parámetros seguros en read_sql para evitar inyección
    query = '''
            SELECT 
                sc.id AS SubCategoriaId,
                sc.categoriaid AS CategoriaId,
                c.nombrecategoria AS NombreCategoria,
                sc.nombresubcategoria AS NombreSubCategoria
            FROM subcategoria as sc 
            LEFT JOIN categoria as c ON sc.categoriaid = c.id
            WHERE sc.eliminado = false 
            AND sc.categoriaid = %s
    '''
    # Pandas permite pasar parámetros directamente a la consulta de forma segura
    # Forzamos int para el parámetro
    df = pd.read_sql(query, conn, params=(int(categoria_id),))
    conn.close()
    return df

def batch_load_subcategoria(subcategorias: pd.DataFrame, categorias: pd.DataFrame):
    merged_subcategorias = pd.merge(categorias, subcategorias, on='Categoria', how='inner')

    # Forzamos int para el ID en la carga por lotes
    data_to_insert = [
        (int(row.CategoriaId), row.SubCategoria) for _, row in merged_subcategorias.iterrows()
    ]

    # En Postgres usamos ON CONFLICT en lugar de MERGE
    upsert_sql = """
        INSERT INTO subcategoria (categoriaid, nombresubcategoria, fechacreacion, fechamodificacion, modificadopor, eliminado)
        VALUES %s
        ON CONFLICT (nombresubcategoria) 
        DO UPDATE SET 
            fechamodificacion = CURRENT_TIMESTAMP,
            modificadopor = EXCLUDED.modificadopor,
            eliminado = EXCLUDED.eliminado;
    """
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        execute_values(
            cursor, 
            upsert_sql, 
            data_to_insert, 
            template="(%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin', false)"
        )
        conn.commit()
        cursor.close()
        conn.close()
        print("Merge completed successfully.")
        return merge_message_success
    except Exception as e:
        print(f"An error occurred: {e}")
        return merge_message_fail

def soft_delete_subcategoria(subcategoria_id: int):
    conn = get_connection()
    # Actualizado a minúsculas para Postgres
    return soft_delete_generico(id=subcategoria_id, table_name='subcategoria', connection=conn)