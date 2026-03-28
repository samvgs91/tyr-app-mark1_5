import pandas as pd
import re
from openai import OpenAI
from datetime import datetime
from crud import get_all_subcategories,get_all_monedas,batch_load_transacciones
from ai_configuration import AI_CONFIGURATION
from utils import detect_currency,extract_amount
import json
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set in environment or .env file.")
client = OpenAI(api_key=OPENAI_API_KEY)

subcategories_df = get_all_subcategories()
monedas_df = get_all_monedas()

# ESCUDO 1: Manejar las columnas en minúsculas de Postgres dinámicamente
if not subcategories_df.empty:
    col_map = {'nombresubcategoria': 'SubCategoria'}
    subcategories_df = subcategories_df.rename(columns=lambda x: col_map.get(x.lower(), x))

if 'SubCategoria' in subcategories_df.columns:
    subcategories_names_list = subcategories_df['SubCategoria'].tolist()
else:
    subcategories_names_list = []

subcategories = subcategories_names_list

config = AI_CONFIGURATION

# Función para determinar la subcategoría basada en palabras clave
def determine_subcategory(description):
    description_lower = description.lower()

    # ESCUDO 2: Usar .get() por si el archivo JSON no existe y devuelve una lista vacía
    for scenario in config.get("scenarios", []):
        if any(keyword.lower() in description_lower for keyword in scenario.get("keywords", [])):
            return scenario.get("subcategoria")

    # Si no coincide con ninguna regla, asignar la categoría por defecto
    return None

def structure_expense(parsed_result):
        if parsed_result:
            # Map Subcategory
            new_expense = pd.DataFrame([parsed_result])
            return new_expense
        else:
            return None

def extract_date(input_text):
    match = re.search(r'Fecha:\s*(\d{2}/\d{2}/\d{4})', input_text)
    if match:
        date_str = match.group(1)
        try:
            # Validate the date format
            datetime.strptime(date_str, "%d/%m/%Y")
            return date_str
        except ValueError:
            return None  # Invalid date format
    return None

def parse_expense(input_text):
    try:
        # Obtener la fecha actual
        fecha_actual = datetime.now()

        moneda_detectada = detect_currency(input_text)

        # Intentar asignar la subcategoría con reglas definidas
        subcategoria_asignada = determine_subcategory(input_text)
        print(f"descripcion '{input_text}' a sido asignada con categoria detectada:{subcategoria_asignada}")

        monto_detectado = extract_amount(input_text) or 0 
        print(f"de la descripcion '{input_text}' se ha detectado el monto: {monto_detectado}")

        if subcategoria_asignada is not None and subcategoria_asignada != 'Sin asignar':
            # Si encontramos una subcategoría, retornamos sin llamar a OpenAI
            return {
                "Moneda": moneda_detectada,
                "Monto": monto_detectado,  
                "Descripción": input_text,
                "SubCategoria": subcategoria_asignada
            }
        else:
            system_message = f"""
            Eres un asistente que asigna categorías de gastos según la entrada del usuario.
            La moneda por defecto es {moneda_detectada}.
            Usa las siguientes subcategorías: {', '.join(subcategories)}.
            Considera que Lucas y Maja son los hijos y se les reconoce como peques.
            Zapamedias y medias de polar Lucas y Maja es de la Subcategoria 'Gastos Ocasionales - Ropa Peques'.
            No asignar ninguna subcategoria que no sea la lista que se proporcionó.
            La subcategoría por defecto es 'Sin asignar'.
            Retorna el resultado en formato JSON con las claves:  Moneda, Monto, Descripción y SubCategoria.
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message },
                    {"role": "user", "content": f"Analizar esta entrada de gastos: {input_text}"}
                ]
            )

            result = response.choices[0].message.content
        
            # ESCUDO 3: Intentar json.loads primero (seguro), si falla usar eval (el original de tu hermano)
            try:
                parsed_data = json.loads(result)
            except Exception:
                parsed_data = eval(result) 

            if parsed_data is not None:
                llm_subcategoria = parsed_data.get("SubCategoria")
                llm_descripcion = parsed_data.get("Descripción")
                print(f"El servicio openai detecto la descripción '{llm_descripcion}' en la subcategoria '{llm_subcategoria}'")
    
            return parsed_data
    except Exception as e:
        print(f"Error parsing input: {e}")
        return None
    
def parse_discrete_expense(input_text):
    try:
        # Intentar asignar la subcategoría con reglas definidas
        sub_categoria_asignada = determine_subcategory(input_text)

        if sub_categoria_asignada is not None:
            # Si encontramos una subcategoría, retornamos sin llamar a OpenAI
            print(f"para input '{input_text}' asignada de custom function es :{sub_categoria_asignada}")
            return sub_categoria_asignada
        else:
            # Generar ejemplos dinámicamente desde config["scenarios"]
            ejemplos = []
            for scenario in config.get("scenarios", []):
                for keyword in scenario.get("keywords", []):
                    ejemplo_desc = keyword
                    ejemplo_cat = scenario["subcategoria"]
                    ejemplos.append(f'"{ejemplo_desc}" -> {ejemplo_cat}')
            
            # ESCUDO 4: Sintaxis correcta de enumerate
            ejemplos_str = "\n".join([f"{i+1}. {ejemplo}" for i, ejemplo in enumerate(ejemplos)])

            prompt = f"""
                Eres un asistente financiero que categoriza gastos.

                Tarea:
                Dada una descripción de gasto, devuelve solamente la categoría correspondiente de la siguiente lista. Si no hay coincidencia clara o no estás seguro, devuelve: "{config.get('default_category', 'Sin asignar')}".

                Categorías: {', '.join(subcategories)}

                Instrucciones:
                - Elige solo una categoría que mejor se ajuste a la descripción del gasto.
                - Si no puedes determinar una categoría con claridad, responde únicamente: "{config.get('default_category', 'Sin asignar')}".
                - No des ninguna explicación, solo devuelve el nombre de la categoría como texto plano.
                - Retorna el resultado en formato JSON con las claves: Descripción y SubCategoria.

                Ejemplos:
                {ejemplos_str}

                Ahora categoriza el siguiente gasto: {input_text}
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente útil de categorización de gastos de tarjeta de crédito de Perú" },
                    {"role": "user", "content": prompt}
                ]
            )

            result = response.choices[0].message.content
        
            try:
                parsed_data = json.loads(result)
            except Exception:
                parsed_data = {"SubCategoria": result.strip(), "Descripción": input_text}

            sub_categoria_asignada = parsed_data.get("SubCategoria")
            if sub_categoria_asignada is not None:
                llm_descripcion = parsed_data.get("Descripción", input_text)
                print(f"El servicio openai detecto la descripción '{input_text}' en la subcategoria '{sub_categoria_asignada}'")
            else:
                sub_categoria_asignada = 'Sin asignar'
                # ESCUDO 5: Evitar el error de variable no definida (llm_descripcion no existía aquí antes)
                print(f"El servicio openai no pudo determinar la subcategoria para la descripción: {input_text}")

            return sub_categoria_asignada

    except Exception as e:
        print(f"Error parsing input: {e}")
        return None
