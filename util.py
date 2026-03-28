import pandas as pd

from crud import get_all_subcategories,get_all_monedas,get_all_fuente_transaction

DEFAULT_SUBCATEGORIA_ID = 20216

def rename_subcategoria_column(df):
    return df.rename(columns={'NombreSubCategoria': 'SubCategoria'})

def merge_on_column(left_df, right_df, column, how='left'):
    return pd.merge(left_df, right_df, on=column, how=how)

def parsear_detalle_gastos_tarjeta_credito(raw_detalle_gastos_tarjeta_credito_df:pd.DataFrame):
    ##load other tables for foreign keys
    subcategories_df = get_all_subcategories()
    monedas_df = get_all_monedas()
    origenes_df = get_all_fuente_transaction()

    subcategories_df = rename_subcategoria_column(subcategories_df)

    add_subcategoria_id = merge_on_column(raw_detalle_gastos_tarjeta_credito_df, subcategories_df, 'SubCategoria')

    add_moneda_id = merge_on_column(add_subcategoria_id, monedas_df, 'Moneda')

    add_origen_id = merge_on_column(add_moneda_id, origenes_df, 'TarjetaOrigen')

    add_origen_id['TipoTransactionId'] = 1

    if add_origen_id['SubCategoriaId'].isnull().any():
        add_origen_id.loc[add_origen_id['SubCategoriaId'].isnull(), 'SubCategoria'] = 'Sin asignar'
        add_origen_id.loc[add_origen_id['SubCategoriaId'].isnull(), 'SubCategoriaId'] = DEFAULT_SUBCATEGORIA_ID #harcoded default SubCategoriaId

    #final select
    detalle_gastos_tarjeta_credito_df = add_origen_id[['Fecha','FuenteTransaccionId','TipoTransactionId','Descripción','SubCategoria','SubCategoriaId','MonedaId','Moneda','Monto']]

    print(detalle_gastos_tarjeta_credito_df)

    return detalle_gastos_tarjeta_credito_df

def parsear_detalle_presupuesto(raw_detalle_presupuesto_df:pd.DataFrame):
    ##load other tables for foreign keys
    subcategories_df = get_all_subcategories()
    monedas_df = get_all_monedas()

    subcategories_df = rename_subcategoria_column(subcategories_df)

    add_subcategoria_id = merge_on_column(raw_detalle_presupuesto_df, subcategories_df, 'SubCategoria')

    add_moneda_id = merge_on_column(add_subcategoria_id, monedas_df, 'Moneda')

    #final select
    detalle_presupuesto_df = add_moneda_id[['SubCategoria','SubCategoriaId','MonedaId','Moneda','Monto']]

    return detalle_presupuesto_df


def validar_subcategoria(expenses_df):
    ##load other tables for foreign keys
    subcategories_df = get_all_subcategories()

    subcategories_df = rename_subcategoria_column(subcategories_df)


    validation_df = merge_on_column(expenses_df, subcategories_df, 'SubCategoria')

    validation_df = validation_df[["Fecha","Moneda", "Monto", "Descripción", "SubCategoria","SubCategoriaId"]]

    if validation_df['SubCategoriaId'].isnull().any():
        validation_df.loc[validation_df['SubCategoriaId'].isnull(), 'SubCategoria'] = 'Sin asignar'
        validation_df.loc[validation_df['SubCategoriaId'].isnull(), 'SubCategoriaId'] = DEFAULT_SUBCATEGORIA_ID #harcoded default SubCategoriaId
        validation_df = validation_df[["Fecha","Moneda", "Monto", "Descripción", "SubCategoria"]]
    
    return validation_df

def parsear_registro_gasto(expenses_df):
    ##load other tables for foreign keys
    subcategories_df = get_all_subcategories()
    monedas_df = get_all_monedas()

    subcategories_df = rename_subcategoria_column(subcategories_df)

    expenses_df['TipoTransactionId'] = 1
    expenses_df['FuenteTransaccionId'] = 1

    #merge with moneda
    join_with_moneda_df = pd.merge(expenses_df, monedas_df, on='Moneda', how='left')

    #merge with subcategoria
    join_with_subcategoria_df = pd.merge(join_with_moneda_df, subcategories_df, on='SubCategoria', how='left')

    #final select
    transaciones_df = join_with_subcategoria_df[['TipoTransactionId','Fecha','FuenteTransaccionId','SubCategoriaId','MonedaId','Monto','Descripción']]

    if transaciones_df['SubCategoriaId'].isnull().any():
        print("validating subcategoria..")
        transaciones_df.loc[transaciones_df['SubCategoriaId'].isnull(), 'SubCategoria'] = 'Sin asignar'
        transaciones_df.loc[transaciones_df['SubCategoriaId'].isnull(), 'SubCategoriaId'] = DEFAULT_SUBCATEGORIA_ID #harcoded default SubCategoriaId
        transaciones_df = transaciones_df[['TipoTransactionId','Fecha','FuenteTransaccionId','SubCategoriaId','MonedaId','Monto','Descripción']]


    return transaciones_df
