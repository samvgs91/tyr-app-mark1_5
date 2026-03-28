from datetime import datetime
from db import get_connection
import pandas as pd
from model.category_model import *
from model.subcategory_model import *
from model.presupuesto_model import *
from model.transaction_model import *

def get_all_fuente_transaction():
    conn = get_connection()
    # Agregamos comillas dobles a los alias para forzar mayúsculas en Postgres
    query = 'SELECT id AS "FuenteTransaccionId", nombrefuentetransaccion AS "TarjetaOrigen" FROM fuentetransaction WHERE eliminado = false'
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_all_fuente_transaction_gasto():
    conn = get_connection()
    # Agregamos comillas dobles a los alias
    query = 'SELECT id AS "FuenteTransaccionId", nombrefuentetransaccion AS "TarjetaOrigen" FROM fuentetransaction WHERE eliminado = false AND id IN (1,2,3,4)'
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_all_budgets():
    conn = get_connection()
    # Cambiamos "Id" por "id" en minúscula para que coincida con la interfaz
    query = '''
        SELECT 
            id AS "id", 
            anio AS "Anio", 
            nummes AS "NumMes", 
            nombremes AS "NombreMes", 
            status AS "Status", 
            version AS "Version" 
        FROM cabecerapresupuesto 
        WHERE eliminado = false
    '''
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_all_monedas():
    conn = get_connection()
    # Agregamos comillas dobles a los alias
    query = 'SELECT id AS "MonedaId", simbolomoneda AS "Moneda" FROM moneda WHERE eliminado = false'
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_presupuesto(id):
    conn = get_connection()
    # Igual aquí, cambiamos "Id" por "id"
    query = '''
        SELECT 
            id AS "id", 
            anio AS "anio", 
            nummes AS "nummes", 
            nombremes AS "nombremes", 
            status AS "status", 
            version AS "version" 
        FROM cabecerapresupuesto 
        WHERE eliminado = false AND id = %s
    '''
    df = pd.read_sql(query, conn, params=(int(id),))
    conn.close()
    return df

def insert_categoria(nombre_agrupamiento, nombre_categoria):
    conn = get_connection()
    fecha_actual = datetime.now()
    query = """
        INSERT INTO categoria (nombrecategoria, fechacreacion, fechamodificacion, modificadopor, eliminado, agrupacionpresupuesto)
        VALUES (%s, %s, %s, 'admin', false, %s)
    """
    cursor = conn.cursor()
    cursor.execute(query, (nombre_categoria, fecha_actual, fecha_actual, nombre_agrupamiento))
    conn.commit()
    cursor.close()
    conn.close()

def insert_cabecera_presupuesto(anio, num_mes, nombre_mes, status, version) -> int:
    conn = get_connection()
    fecha_actual = datetime.now()
    query = """
        INSERT INTO app.cabecerapresupuesto (anio, nummes, nombremes, status, version, fechacreacion, fechamodificacion, modificadopor, eliminado)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'admin', false)
        RETURNING id
    """
    cursor = conn.cursor()
    cursor.execute(query, (anio, num_mes, nombre_mes, status, version, fecha_actual, fecha_actual))
    inserted_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return int(inserted_id)

def update_cabecera_presupuesto(id, anio, num_mes, nombre_mes, status, version):
    conn = get_connection()
    fecha_modificacion = datetime.now()
    query = """
        UPDATE app.cabecerapresupuesto
        SET anio = %s, nummes = %s, nombremes = %s, status = %s, version = %s, fechamodificacion = %s, modificadopor = 'admin'
        WHERE id = %s AND eliminado = false
    """
    cursor = conn.cursor()
    # Forzamos int() al final
    cursor.execute(query, (anio, num_mes, nombre_mes, status, version, fecha_modificacion, int(id)))
    conn.commit()
    cursor.close()
    conn.close()

def delete_cabecera_presupuesto(id):
    try:
        conn = get_connection()
        query = """
            UPDATE app.cabecerapresupuesto
            SET eliminado = true, fechamodificacion = %s, modificadopor = 'admin'
            WHERE id = %s
        """
        fecha_modificacion = datetime.now()
        cursor = conn.cursor()
        # Forzamos int()
        cursor.execute(query, (fecha_modificacion, int(id)))
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if rows_affected > 0:
            print(f"Budget {id} deleted successfully!")
            return "Budget deleted successfully!"
        else:
            print(f"Budget {id} not found.")
            return "Budget not found."
    except Exception as e:
        print(f"An error occurred while deleting budget: {e}")
        return f"Error deleting budget: {str(e)}"