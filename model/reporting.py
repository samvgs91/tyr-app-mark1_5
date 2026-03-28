from db import get_connection
import pandas as pd


def get_presupuesto_vs_gastos() -> pd.DataFrame:
    conn = get_connection()
    query = """
                select 
                    pvg.*,sub.subcategoria,dimanio.anio, cat.categoria,cat.agrupacionpresupuesto,tc.compra
                    , case when moneda = 'Soles' then pvg.gastomonto else tc.compra * pvg.gastomonto end as montosoles
                    , case when moneda = 'Dolar' then pvg.gastomonto else pvg.gastomonto/tc.compra end as montodolares
                    , case when moneda = 'Soles' then pvg.presupuestomonto else tc.compra * pvg.presupuestomonto end as presupuestosoles 
                    , case when moneda = 'Dolar' then pvg.presupuestomonto else pvg.presupuestomonto/tc.compra end as presupuestodolares
                from rpt.factpresupuestovsgastos as pvg 
                join rpt.dimsubcategoria as sub on pvg.subcategoriakey= sub.subcategoriakey
                join rpt.dimaniomes as dimanio on dimanio.aniomes = pvg.aniomes
                join rpt.dimcategoria as cat on cat.categoriakey = sub.categoriakey
                join rpt.dimtipocambio as tc on pvg.aniomes = tc.aniomes
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def get_detalle_gastos() -> pd.DataFrame:
    conn = get_connection()
    query = """
        SELECT fd.*, sub.subcategoria, cat.categoria,cat.agrupacionpresupuesto 
        FROM rpt.factdetallegastos as fd
        join rpt.dimsubcategoria as sub on fd.subcategoriakey= sub.subcategoriakey
        join rpt.dimcategoria as cat on cat.categoriakey = sub.categoriakey
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def get_detalle_ingresos() -> pd.DataFrame:
    conn = get_connection()
    query = """
        SELECT fd.*
        FROM rpt.factingresos as fd
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def get_totales_ingresos_presupuesto_gastos() -> pd.DataFrame:
    conn = get_connection()
    query = """
        SELECT
            aniomes,
            presupuestodolares,
            presupuestosoles,
            gastodolares,
            gastosoles,
            ingresosoles,
            ingresodolar,
            ingresosoles - presupuestosoles as ahorropresupuestosoles,
            ingresosoles - gastosoles as ahorrosoles
        FROM rpt.ingresos_vs_gastos
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df
