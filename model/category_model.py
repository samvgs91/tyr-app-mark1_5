from db import get_connection
import pandas as pd
from psycopg2.extras import execute_values
from model.model_util import *

def update_categoria(categoria_id: int, categoria: str, agrupacion_presupuesto: str):
    update_sql = """
        UPDATE categoria
        SET nombrecategoria = %s,
            agrupacionpresupuesto = %s,
            fechamodificacion = CURRENT_TIMESTAMP,
            modificadopor = 'admin'
        WHERE id = %s
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Forzamos int para el categoria_id
        cursor.execute(update_sql, (categoria, agrupacion_presupuesto, int(categoria_id)))
        conn.commit()
        cursor.close()
        conn.close()

        print(update_categoria_message_success) 
        return update_categoria_message_success
    except Exception as e:
        print(f"An error occurred: {e}")
        return update_categoria_message_fail
    
def delete_categoria(categoria_id: int):
    # Forzamos int antes de mandarlo a la función genérica
    return soft_delete_generico(int(categoria_id), 'categoria', get_connection())

def intert_categoria(categoria: str, agrupacion_presupuesto: str):
    insert_sql = """
        INSERT INTO categoria (nombrecategoria, fechacreacion, fechamodificacion, modificadopor, eliminado, agrupacionpresupuesto)
        VALUES (%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin', false, %s)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(insert_sql, (categoria, agrupacion_presupuesto))
        conn.commit()
        cursor.close()
        conn.close()
        print(insert_message_success)
        return insert_message_success
    except Exception as e:
        print(f"An error occurred: {e}")
        return insert_message_fail

def get_all_categories():
    conn = get_connection()
    query = 'SELECT id as "CategoriaId", nombrecategoria as "Categoria", agrupacionpresupuesto as "AgrupacionPresupuesto" FROM categoria WHERE eliminado = false'
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def soft_delete_categoria(categoria_id: int):
    update_sql = """
        UPDATE categoria
        SET eliminado = true
        WHERE id = %s
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Forzamos int para el categoria_id
        cursor.execute(update_sql, (int(categoria_id),))
        conn.commit()
        cursor.close()
        conn.close()
        print(delete_message_success)
        return delete_message_success
    except Exception as e:
        print(f"An error occurred: {e}")
        return delete_message_fail
    
def batch_load_categoria(categorias: pd.DataFrame):
    data_to_insert = [
        (row.Categoria, row.Agrupamiento) for _, row in categorias.iterrows()
    ]

    upsert_sql = """
        INSERT INTO categoria (nombrecategoria, fechacreacion, fechamodificacion, modificadopor, eliminado, agrupacionpresupuesto)
        VALUES %s
        ON CONFLICT (nombrecategoria) 
        DO UPDATE SET 
            fechamodificacion = CURRENT_TIMESTAMP,
            modificadopor = EXCLUDED.modificadopor,
            eliminado = EXCLUDED.eliminado,
            agrupacionpresupuesto = EXCLUDED.agrupacionpresupuesto;
    """
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        execute_values(
            cursor, 
            upsert_sql, 
            data_to_insert, 
            template="(%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin', false, %s)"
        )
        conn.commit()
        cursor.close()
        conn.close()
        print("Merge (Upsert) completed successfully.")
        return "Load complete!"
    except Exception as e:
        print(f"An error occurred: {e}")
        return "something went wrong with loading..."