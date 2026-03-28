"""
services/credit_card_transformation.py
Business logic and data transformation functions for credit card expense processing.
"""
import pandas as pd
from ai_module import parse_discrete_expense
from utilitaries.master_data import get_all_subcategories, get_all_monedas, get_all_fuente_transaction, load_default_subcategoria_id

# 1. ESCUDOS DEFENSIVOS
def shield_dataframe(df):
    """Protege contra minúsculas de Postgres en las tablas maestras"""
    if not df.empty:
        col_map = {
            'nombresubcategoria': 'SubCategoria',
            'subcategoriaid': 'SubCategoriaId',
            'moneda': 'Moneda',
            'monedaid': 'MonedaId',
            'tarjetaorigen': 'TarjetaOrigen',
            'fuentetransaccionid': 'FuenteTransaccionId'
        }
        return df.rename(columns=lambda x: col_map.get(str(x).lower(), x))
    return df

def normalize_expense_columns(df):
    """Estandariza las columnas del Excel (maneja tildes y mayúsculas)"""
    col_map = {
        'descripcion': 'Descripción',
        'descripción': 'Descripción',
        'monto': 'Monto',
        'fecha': 'Fecha'
    }
    return df.rename(columns=lambda x: col_map.get(str(x).lower().strip(), x))

# 2. CARGA Y PROTECCIÓN DE DATOS MAESTROS
SUBCATEGORIES_DF = shield_dataframe(get_all_subcategories())
monedas_df = shield_dataframe(get_all_monedas())
origenes_df = shield_dataframe(get_all_fuente_transaction())

# ==========================================
# SOLUCIÓN: AQUÍ ESTABA EL "1" PROBLEMÁTICO
# ==========================================
# OPCIÓN A (Recomendada): Usar la función dinámica que ya habías importado
DEFAULT_SUBCATEGORIA_ID = 20216

# OPCIÓN B: Si la función de arriba falla, comenta la línea de arriba y usa esta 
# cambiando el "1" por el ID real que viste en Supabase (ej. 150, 20, etc.)
# DEFAULT_SUBCATEGORIA_ID = TU_NUEVO_ID_AQUI  
# ==========================================


def rename_subcategoria_column(df):
    return df.rename(columns={'NombreSubCategoria': 'SubCategoria'})

def merge_on_column(left_df, right_df, column, how='left'):
    # Evita errores si la columna no existe en alguna tabla
    if column in left_df.columns and column in right_df.columns:
        return pd.merge(left_df, right_df, on=column, how=how)
    return left_df

def procesar_registros_tarjeta_credito(expenses_df: pd.DataFrame) -> pd.DataFrame:
    tmp_df = normalize_expense_columns(expenses_df.copy())
    
    tmp_df['Log'] = tmp_df['Descripción']
    tmp_df.drop(columns=['Descripción'], inplace=True)
    tmp_df['parsed_log'] = tmp_df['Log'].apply(parse_discrete_expense)
    tmp_df['SubCategoria'] = tmp_df['parsed_log']
    tmp_df['Descripción'] = tmp_df['Log']
    tmp_df.drop(columns=['parsed_log', 'Log'], inplace=True)
    tmp_df['TarjetaOrigen'] = 'Gastos Tarjeta de Credito BCP'
    
    detalle_df = parsear_detalle_gastos_tarjeta_credito(raw_detalle_gastos_tarjeta_credito_df=tmp_df)
    return detalle_df

def procesar_registros(expenses_df: pd.DataFrame, expense_type_code: int) -> pd.DataFrame:
    tmp_df = normalize_expense_columns(expenses_df.copy())
    
    tmp_df['Log'] = tmp_df['Descripción']
    tmp_df.drop(columns=['Descripción'], inplace=True)
    tmp_df['parsed_log'] = tmp_df['Log'].apply(parse_discrete_expense)
    tmp_df['SubCategoria'] = tmp_df['parsed_log']
    tmp_df['Descripción'] = tmp_df['Log']
    tmp_df.drop(columns=['parsed_log', 'Log'], inplace=True)
    tmp_df['FuenteTransaccionId'] = expense_type_code

    detalle_df = parsear_detalle_gastos(raw_detalle_gastos_df=tmp_df, expense_type_code=expense_type_code)
    return detalle_df

def parsear_detalle_gastos_tarjeta_credito(raw_detalle_gastos_tarjeta_credito_df:pd.DataFrame):
    subcategories_df = rename_subcategoria_column(SUBCATEGORIES_DF)

    add_subcategoria_id = merge_on_column(raw_detalle_gastos_tarjeta_credito_df, subcategories_df, 'SubCategoria')
    add_moneda_id = merge_on_column(add_subcategoria_id, monedas_df, 'Moneda')
    add_origen_id = merge_on_column(add_moneda_id, origenes_df, 'TarjetaOrigen')

    add_origen_id['TipoTransactionId'] = 1

    # SALVAVIDAS: Si la base de datos está vacía y no trajo los IDs, los creamos por defecto
    if 'FuenteTransaccionId' not in add_origen_id.columns:
        add_origen_id['FuenteTransaccionId'] = 3  # TC ID por defecto

    if 'SubCategoriaId' not in add_origen_id.columns:
        add_origen_id['SubCategoriaId'] = DEFAULT_SUBCATEGORIA_ID
        add_origen_id['SubCategoria'] = 'Sin asignar'
    elif add_origen_id['SubCategoriaId'].isnull().any():
        add_origen_id.loc[add_origen_id['SubCategoriaId'].isnull(), 'SubCategoria'] = 'Sin asignar'
        add_origen_id.loc[add_origen_id['SubCategoriaId'].isnull(), 'SubCategoriaId'] = DEFAULT_SUBCATEGORIA_ID

    if 'MonedaId' not in add_origen_id.columns:
        add_origen_id['MonedaId'] = 1  # PEN ID por defecto
    elif add_origen_id['MonedaId'].isnull().any():
        add_origen_id.loc[add_origen_id['MonedaId'].isnull(), 'MonedaId'] = 1

    expected_cols = ['Fecha','FuenteTransaccionId','TipoTransactionId','Descripción','SubCategoria','SubCategoriaId','MonedaId','Moneda','Monto']
    exist_cols = [c for c in expected_cols if c in add_origen_id.columns]
    
    detalle_gastos_tarjeta_credito_df = add_origen_id[exist_cols]
    return detalle_gastos_tarjeta_credito_df

def parsear_detalle_gastos(raw_detalle_gastos_df:pd.DataFrame, expense_type_code: int):
    subcategories_df = rename_subcategoria_column(SUBCATEGORIES_DF)

    add_subcategoria_id = merge_on_column(raw_detalle_gastos_df, subcategories_df, 'SubCategoria')
    add_moneda_id = merge_on_column(add_subcategoria_id, monedas_df, 'Moneda')
    
    add_origen_id = add_moneda_id
    add_origen_id['TipoTransactionId'] = 1
    add_origen_id['FuenteTransaccionId'] = expense_type_code

    # SALVAVIDAS: Si la base de datos está vacía y no trajo los IDs, los creamos por defecto
    if 'SubCategoriaId' not in add_origen_id.columns:
        add_origen_id['SubCategoriaId'] = DEFAULT_SUBCATEGORIA_ID
        add_origen_id['SubCategoria'] = 'Sin asignar'
    elif add_origen_id['SubCategoriaId'].isnull().any():
        add_origen_id.loc[add_origen_id['SubCategoriaId'].isnull(), 'SubCategoria'] = 'Sin asignar'
        add_origen_id.loc[add_origen_id['SubCategoriaId'].isnull(), 'SubCategoriaId'] = DEFAULT_SUBCATEGORIA_ID

    if 'MonedaId' not in add_origen_id.columns:
        add_origen_id['MonedaId'] = 1  # PEN ID por defecto
    elif add_origen_id['MonedaId'].isnull().any():
        add_origen_id.loc[add_origen_id['MonedaId'].isnull(), 'MonedaId'] = 1

    expected_cols = ['Fecha','FuenteTransaccionId','TipoTransactionId','Descripción','SubCategoria','SubCategoriaId','MonedaId','Moneda','Monto']
    exist_cols = [c for c in expected_cols if c in add_origen_id.columns]

    detalle_gastos_df = add_origen_id[exist_cols]
    return detalle_gastos_df