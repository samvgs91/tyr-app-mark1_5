import pandas as pd

def add_subcategoria_id(df1, df2):
    # Ensure 'SubCategoriaId' is an integer
    df2['SubCategoriaId'] = df2['SubCategoriaId'].astype(int)
    
    # Drop duplicates in df2 based on 'PalabraClave', keeping the first occurrence
    df2 = df2.drop_duplicates(subset='PalabraClave')

    # Create a dictionary for quick lookup
    palabra_to_subcategoria = df2.set_index('PalabraClave')['SubCategoriaId'].to_dict()
    
    # Function to find the SubCategoriaId for a given description
    def find_subcategoria_id(description):
        for palabra_clave, sub_categoria_id in palabra_to_subcategoria.items():
            if palabra_clave.lower() in description.lower():
                return sub_categoria_id
        return None
    
    # Apply the function to each row in df1 and create a new column 'SubCategoriaId'
    df1['SubCategoriaId'] = df1['Descripcion'].apply(find_subcategoria_id)
    
    return df1

# Example usage
df1 = pd.DataFrame({
    'Fecha': ['2024-01-01', '2024-01-02', '2024-01-03'],
    'Descripcion': ['Compra de equipo', 'Pago de servicios', 'Compra de equipo adicional'],
    'Tipo de moneda': ['USD', 'USD', 'USD'],
    'Monto': [1000, 200, 1500]
})

df2 = pd.DataFrame({
    'Id': [1, 2, 3],
    'PalabraClave': ['equipo', 'servicios', 'equipo adicional'],
    'SubCategoriaId': [10, 20, 30]
})

result_df = add_subcategoria_id(df1, df2)
print(result_df)
