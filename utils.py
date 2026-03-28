import json
import openai
import re
from datetime import datetime,date

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
## listado de años
years_data = (2025,2024)

def get_month_range(year, month):
    start_date = date(year, month, 1)
    if month == 12:
        next_month_date = date(year + 1, 1, 1)
    else:
        next_month_date = date(year, month + 1, 1)
    
    # Convert to string format YYYY-MM-DD
    return start_date.strftime('%Y-%m-%d'), next_month_date.strftime('%Y-%m-%d')


def load_ai_config():
    with open("recursos/ai_configuration.json", "r", encoding="utf-8") as file:
        return json.load(file)

def get_system_columns(operation):
    now = datetime.now()
    return {
        'FechaCreacion': now if operation == 'create' else None,
        'FechaModificacion': now,
        'ModificadoPor': 'your_user',  # Adjust as necessary
        'Eliminado': 0  # Default value
    }

# Función para detectar la moneda en el texto
def detect_currency(description):
    description_lower = description.lower()
    
    if "usd" in description_lower or "dólares" in description_lower or "dolares" in description_lower:
        return "$"  # Dólares
    return "S/"  # Soles (por defecto)

def extract_amount(description):
    """
    Extrae el monto de un texto en diferentes formatos.
    Soporta S/, $, USD, y valores numéricos aislados.
    """
    patrones = [
        r"S/\.?\s?(\d+[,.]?\d*)",    # "S/ 50" o "S/.50"
        r"(\d+[,.]?\d*)\s?soles?",   # "50 soles"
        r"\$\s?(\d+[,.]?\d*)",       # "$50" o "$ 50"
        r"USD\s?(\d+[,.]?\d*)",      # "USD 20"
        r"(\d+[,.]?\d*)\s?(?:dólares|dolares)",  # "50 dólares"
        r"(\d+[,.]?\d*)"             # Cualquier número flotante aislado
    ]

    for patron in patrones:
        match = re.search(patron, description, re.IGNORECASE)
        if match:
            monto = match.group(1).replace(",", ".")  # Asegurar formato decimal con "."
            return float(monto) if monto else None

    return None  # No se encontró un monto