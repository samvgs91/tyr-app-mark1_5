"""
utilitaries/master_data.py
Functions to load master data tables for the application.
"""
from crud import get_all_subcategories, get_all_monedas, get_all_fuente_transaction

def load_default_subcategoria_id():
    """Returns the default subcategoria ID."""
    return 1  # ¡Actualizado al nuevo ID de Supabase!

def format_columns(df):
    """Estandariza las columnas de Postgres en min?sculas."""
    if not df.empty:
        col_map = {
            'id': 'id',
            'nombresubcategoria': 'nombresubcategoria',
            'categoriaid': 'categoriaid',
            'nombrecategoria': 'nombrecategoria',
            'ordenid': 'ordenid',
            'nombremoneda': 'moneda',
            'simbolomoneda': 'simbolomoneda',
            'nombrefuentetransaccion': 'tarjetaorigen',
            'fuentetransaccionid': 'fuentetransaccionid',
            'subcategoriaid': 'subcategoriaid',
        }
        return df.rename(columns=lambda x: col_map.get(str(x).lower(), str(x).lower()))
    return df

def load_subcategories_df():
    """Returns the subcategories DataFrame."""
    return format_columns(get_all_subcategories())

def load_monedas_df():
    """Returns the monedas DataFrame."""
    return format_columns(get_all_monedas())

def load_origenes_df():
    """Returns the origenes DataFrame."""
    return format_columns(get_all_fuente_transaction())

# Mantenemos estas funciones por si otros archivos las llaman directamente
# (Aunque ya aplicamos un escudo en credit_card_transformation, es mejor prevenir)
# Re-exportamos las funciones originales de crud por si se usan en otros lados
# get_all_subcategories = get_all_subcategories
# get_all_monedas = get_all_monedas
# get_all_fuente_transaction = get_all_fuente_transaction