from psycopg2 import sql

insert_message_success = "Insert complete!"
insert_message_fail = "something went wrong with inserting..."

create_message_success = "Create complete!"
create_message_fail = "something went wrong with creating..."

update_categoria_message_success = "Update complete!"
update_categoria_message_fail = "something went wrong with updating..."

delete_message_success = "Soft delete complete!"
delete_message_fail = "something went wrong with deleting..."

merge_message_success = "Load complete!"
merge_message_fail = "something went wrong with loading..."

def soft_delete_generico(id: int, table_name: str, connection):
    try:
        query = sql.SQL("""
            UPDATE {table}
            SET eliminado = true
            WHERE id = %s
        """).format(table=sql.Identifier(table_name.lower()))
        
        cursor = connection.cursor()
        # Forzamos el id a entero nativo para evitar errores de numpy.int64
        cursor.execute(query, (int(id),))
        connection.commit()
        
        cursor.close()
        connection.close()
        
        print(delete_message_success)
        return delete_message_success
    except Exception as e:
        print(f"An error occurred: {e}")
        return delete_message_fail