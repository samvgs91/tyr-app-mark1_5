from db import get_connection
import pandas as pd
from psycopg2.extras import execute_values
from model.model_util import *


def get_transacciones_by_month(year: int, month_id: int, trans_types: list[int]):
    conn = get_connection()
    trans_types_tuple = tuple(int(x) for x in trans_types)

    query = """
        SELECT
            t.id,
            t.fecha AS fecha,
            t.monedaid AS monedaid,
            m.simbolomoneda AS moneda,
            t.monto AS monto,
            t.descripcion AS descripcion,
            t.subcategoriaid AS subcategoriaid,
            sc.nombresubcategoria AS subcategoria,
            t.fecha AS Fecha,
            m.nombremoneda AS Moneda,
            t.monto AS Monto,
            t.descripcion AS Descripcion,
            sc.nombresubcategoria AS SubCategoria
        FROM transaccion AS t
        LEFT JOIN moneda AS m ON t.monedaid = m.id
        LEFT JOIN subcategoria AS sc ON t.subcategoriaid = sc.id
        WHERE t.eliminado = false
        AND EXTRACT(YEAR FROM t.fecha) = %s
        AND EXTRACT(MONTH FROM t.fecha) = %s
        AND t.fuentetransaccionid IN %s
        ORDER BY t.fecha DESC, t.id DESC
    """

    df = pd.read_sql(query, conn, params=(int(year), int(month_id), trans_types_tuple))
    conn.close()
    return df


def get_transaccion_by_id(transaccion_id: int):
    conn = get_connection()
    query = """
        SELECT
            t.id,
            t.tipotransactionid,
            t.fuentetransaccionid,
            t.fecha AS Fecha,
            t.monedaid AS MonedaId,
            m.simbolomoneda AS Moneda,
            t.monto AS Monto,
            t.descripcion AS Descripcion,
            t.subcategoriaid AS SubCategoriaId,
            sc.nombresubcategoria AS SubCategoria
        FROM transaccion AS t
        LEFT JOIN moneda AS m ON t.monedaid = m.id
        LEFT JOIN subcategoria AS sc ON t.subcategoriaid = sc.id
        WHERE t.id = %s
          AND t.eliminado = false
        LIMIT 1
    """

    df = pd.read_sql(query, conn, params=(int(transaccion_id),))
    conn.close()
    return df


def insert_transaccion(
    fecha,
    fuentetransaccionid: int,
    subcategoriaid: int,
    monedaid: int,
    monto: float,
    descripcion: str,
    tipotransactionid: int = 1,
    modificadopor: str = "admin",
):
    insert_sql = """
        INSERT INTO transaccion (
            tipotransactionid,
            fecha,
            fuentetransaccionid,
            subcategoriaid,
            monedaid,
            monto,
            fechacreacion,
            fechamodificacion,
            modificadopor,
            eliminado,
            descripcion
        )
        VALUES (%s, %s::date, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s, false, %s)
        RETURNING id
    """
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    insert_sql,
                    (
                        int(tipotransactionid),
                        fecha,
                        int(fuentetransaccionid),
                        int(subcategoriaid),
                        int(monedaid),
                        float(monto),
                        modificadopor,
                        descripcion,
                    ),
                )
                inserted_id = cursor.fetchone()[0]
                conn.commit()
        return int(inserted_id)
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def update_transaccion(
    transaccion_id: int,
    fecha,
    subcategoriaid: int,
    monedaid: int,
    monto: float,
    descripcion: str,
    modificadopor: str = "admin",
):
    update_sql = """
        UPDATE transaccion
        SET fecha = %s::date,
            subcategoriaid = %s,
            monedaid = %s,
            monto = %s,
            descripcion = %s,
            fechamodificacion = CURRENT_TIMESTAMP,
            modificadopor = %s
        WHERE id = %s
          AND eliminado = false
    """
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    update_sql,
                    (
                        fecha,
                        int(subcategoriaid),
                        int(monedaid),
                        float(monto),
                        descripcion,
                        modificadopor,
                        int(transaccion_id),
                    ),
                )
                conn.commit()
                return cursor.rowcount > 0
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def update_subcategoria_de_transaction(transacction_id, subcategoria_id):
    conn = get_connection()
    query = """
        UPDATE transaccion
        SET subcategoriaid = %s,
            fechamodificacion = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (int(subcategoria_id), int(transacction_id)))
        conn.commit()
        cursor.close()
        conn.close()
        print("Update subcategoria is complete!")
    except Exception as e:
        print(f"An error occurred: {e}")


def soft_delete_transaccion(id: int):
    update_sql = """
        UPDATE transaccion
        SET eliminado = true,
            fechamodificacion = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(update_sql, (int(id),))
                conn.commit()
        return "Soft delete complete!"
    except Exception as e:
        print(f"An error occurred: {e}")
        return "something went wrong when deleting expense..."


def soft_batch_delete_transacciones(year_id: int, month_id: int, trans_types: list[int]):
    print("Soft batch delete initiated.")
    trans_types_tuple = tuple(int(x) for x in trans_types)

    soft_update_script = """
        UPDATE transaccion
        SET eliminado = true,
            fechamodificacion = CURRENT_TIMESTAMP
        WHERE tipotransactionid = 1
        AND fuentetransaccionid IN %s
        AND EXTRACT(YEAR FROM fecha) = %s
        AND EXTRACT(MONTH FROM fecha) = %s
    """
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(soft_update_script, (trans_types_tuple, int(year_id), int(month_id)))
                conn.commit()
        return "Soft delete complete!"
    except Exception as e:
        print(f"An error occurred: {e}")
        return "something went wrong when deleting expense..."


def batch_load_transacciones(trans: pd.DataFrame):
    trans["Fecha"] = pd.to_datetime(trans["Fecha"], format="mixed", dayfirst=True).dt.strftime("%Y-%m-%d")
    descripcion_col = "Descripcion" if "Descripcion" in trans.columns else "Descripci\u00f3n"

    data_to_insert = [
        (
            int(row.TipoTransactionId),
            row.Fecha,
            int(row.FuenteTransaccionId),
            int(row.SubCategoriaId),
            int(row.MonedaId),
            float(row.Monto),
            getattr(row, descripcion_col),
        )
        for _, row in trans.iterrows()
    ]

    insert_sql = """
        INSERT INTO transaccion (
            tipotransactionid, fecha, fuentetransaccionid,
            subcategoriaid, monedaid, monto, fechacreacion,
            fechamodificacion, modificadopor, eliminado, descripcion
        )
        VALUES %s
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        execute_values(
            cursor,
            insert_sql,
            data_to_insert,
            template="(%s, %s::date, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'admin', false, %s)",
        )
        conn.commit()
        cursor.close()
        conn.close()
        print("Load complete!")
        return "Load complete!"
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Something went wrong when loading the transaction..."
