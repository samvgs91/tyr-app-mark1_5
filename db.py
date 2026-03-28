import psycopg2
import pandas as pd
import os
import warnings
from dotenv import load_dotenv

# Silenciar el warning de Pandas para mantener la consola limpia
warnings.filterwarnings('ignore', message='.*pandas only supports SQLAlchemy.*')

load_dotenv()

def get_connection():
    """Establece la conexión a la base de datos de Supabase (PostgreSQL)"""
    conn = psycopg2.connect(
        host=os.getenv("SUPABASE_HOST"),
        database=os.getenv("SUPABASE_DB_NAME", "postgres"),
        user=os.getenv("SUPABASE_USER", "postgres"),
        password=os.getenv("SUPABASE_PASSWORD"),
        port=os.getenv("SUPABASE_PORT", "5432")
    )
    
    # FORZAR EL ESQUEMA: Obligamos a la sesión a buscar en app y rpt
    cursor = conn.cursor()
    cursor.execute("SET search_path TO app, rpt, public;")
    conn.commit()
    cursor.close()
    
    return conn

def fetch_table_data(table_name):
    """Obtiene todos los registros activos de una tabla"""
    conn = get_connection()
    
    query = f"SELECT * FROM {table_name.lower()} WHERE eliminado = false"
    
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def execute_query(sql, params=None):
    """Ejecuta consultas de inserción, actualización o eliminación"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
        
    conn.commit()
    cursor.close()
    conn.close()