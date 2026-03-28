# utilitaries/month_mapping.py
"""
Month mapping dictionary for Spanish month names to numbers.
"""
from crud import get_all_fuente_transaction_gasto
from datetime import datetime, date
import pandas as pd

def get_fuente_transaction_gasto_dict():
    """
    Returns a dictionary mapping 'Descripcion' to the row (or to a specific value) from get_all_fuente_transaction DataFrame.
    """
    df = get_all_fuente_transaction_gasto()
    
    # ESCUDO DEFENSIVO: Manejo de minúsculas de Postgres y tablas vacías
    if df.empty:
        # Fallback seguro en caso de que la tabla en Supabase esté vacía
        return {
            "Gastos Tarjeta de Credito": 3,
            "Gastos Cuenta Bancaria": 1
        }
        
    col_map = {
        'tarjetaorigen': 'TarjetaOrigen', 
        'fuentetransaccionid': 'FuenteTransaccionId'
    }
    df = df.rename(columns=lambda x: col_map.get(x.lower(), x))
    
    # Map 'TarjetaOrigen' to 'FuenteTransaccionId' validando que existan
    if 'TarjetaOrigen' in df.columns and 'FuenteTransaccionId' in df.columns:
        return df.set_index('TarjetaOrigen')['FuenteTransaccionId'].to_dict()
    else:
        return {
            "Gastos Tarjeta de Credito": 3,
            "Gastos Cuenta Bancaria": 1
        }

years_data = (2026, 2025, 2024)

month_mapping = {
    "Enero": 1,
    "Febrero": 2,
    "Marzo": 3,
    "Abril": 4,
    "Mayo": 5,
    "Junio": 6,
    "Julio": 7,
    "Agosto": 8,
    "Septiembre": 9,
    "Octubre": 10,
    "Noviembre": 11,
    "Diciembre": 12,
}

## listado de meses
month_dic = {
    "Enero": 1,
    "Febrero": 2,
    "Marzo": 3,
    "Abril": 4,
    "Mayo": 5,
    "Junio": 6,
    "Julio": 7,
    "Agosto": 8,
    "Septiembre": 9,
    "Octubre": 10,
    "Noviembre": 11,
    "Diciembre": 12
}

expense_type_mapping = get_fuente_transaction_gasto_dict()

def get_month_range(year, month):
    start_date = date(year, month, 1)
    if month == 12:
        next_month_date = date(year + 1, 1, 1)
    else:
        next_month_date = date(year, month + 1, 1)
    
    # Convert to string format YYYY-MM-DD
    return start_date.strftime('%Y-%m-%d'), next_month_date.strftime('%Y-%m-%d')