from db import get_connection
import pandas as pd
from psycopg2.extras import execute_values
from model.model_util import *

def soft_delete_detalle_presupuesto(detalle_presupuesto_id: int):
    update_sql = """
    UPDATE app.detallepresupuesto
    SET eliminado = true,
        fechamodificacion = CURRENT_TIMESTAMP,
        modificadopor = 'admin'
    WHERE id = %s
    """
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cursor:
                # Forzamos a entero por seguridad
                cursor.execute(update_sql, (int(detalle_presupuesto_id),))
                conn.commit()
        print(delete_message_success)
        return delete_message_success
    except Exception as e:
        print(f"An error occurred: {e}")
        return delete_message_fail

def soft_delete_all_detalle_por_presupuesto_id(budget_id: int):
    """Soft delete all budget details for a given budget header ID"""
    update_sql = """
    UPDATE app.detallepresupuesto
    SET eliminado = true,
        fechamodificacion = CURRENT_TIMESTAMP,
        modificadopor = 'admin'
    WHERE cabecerapresupuestoid = %s
    """
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(update_sql, (int(budget_id),))
                rows_affected = cursor.rowcount
                conn.commit()
        print(f"{delete_message_success} - {rows_affected} record(s) deleted.")
        return delete_message_success
    except Exception as e:
        print(f"An error occurred: {e}")
        return delete_message_fail

def get_detalle_presupuesto(budget_id: int):
    conn = get_connection()
    # Parámetros seguros para Pandas
    query = '''
        SELECT
            d.id,
            d.subcategoriaid AS subcategoriaid,
            sc.nombresubcategoria AS subcategoria,
            d.monedaid AS monedaid,
            m.simbolomoneda AS moneda,
            d.montopresupuesto AS monto
        FROM app.detallepresupuesto AS d
        LEFT JOIN app.moneda AS m ON d.monedaid = m.id
        LEFT JOIN app.subcategoria as sc ON d.subcategoriaid = sc.id
        WHERE d.cabecerapresupuestoid = %s AND d.eliminado = false
    '''
    df = pd.read_sql(query, conn, params=(int(budget_id),))
    conn.close()
    return df

def create_detalle_presupuesto(budget_id: int, subcategoria_id: int, moneda_id: int, monto: float):
    """Insert a single budget detail record"""
    budget_id = int(budget_id)
    subcategoria_id = int(subcategoria_id)
    moneda_id = int(moneda_id)
    monto = float(monto)
    
    insert_sql = """
    INSERT INTO app.detallepresupuesto 
        (cabecerapresupuestoid,
        subcategoriaid,
        monedaid,
        montopresupuesto,
        fechacreacion,
        fechamodificacion,
        modificadopor,
        eliminado)
    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin', false)
    """
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(insert_sql, (budget_id, subcategoria_id, moneda_id, monto))
                conn.commit()
        print(create_message_success)
        return create_message_success
    except Exception as e:
        print(f"An error occurred: {e}")
        return create_message_fail

def batch_load_detalle_presupuesto(detalle_presupuesto_df: pd.DataFrame, budget_id: int):
    normalized_df = detalle_presupuesto_df.rename(
        columns=lambda col: str(col).strip().lower()
    )

    # Extraemos los datos del DataFrame de forma limpia
    data_to_insert = [
        (
            int(budget_id), 
            int(row.subcategoriaid), 
            int(row.monedaid), 
            float(row.monto)
        ) for _, row in normalized_df.iterrows()
    ]

    # UPSERT para Postgres
    upsert_sql = """
        INSERT INTO app.detallepresupuesto (cabecerapresupuestoid, subcategoriaid, monedaid, montopresupuesto, fechacreacion, fechamodificacion, modificadopor, eliminado)
        VALUES %s
        ON CONFLICT (cabecerapresupuestoid, subcategoriaid)
        DO UPDATE SET 
            fechamodificacion = CURRENT_TIMESTAMP,
            modificadopor = EXCLUDED.modificadopor,
            montopresupuesto = EXCLUDED.montopresupuesto,
            eliminado = EXCLUDED.eliminado;
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        execute_values(
            cursor, 
            upsert_sql, 
            data_to_insert, 
            template="(%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin', false)"
        )
        conn.commit()
        cursor.close()
        conn.close()
        print("Merge completed successfully.")
        return merge_message_success
    except Exception as e:
        print(f"An error occurred: {e}")
        return merge_message_fail
