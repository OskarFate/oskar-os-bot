#!/usr/bin/env python3
"""
Script para probar la zona horaria y tiempos
"""

import sys
from datetime import datetime
import pytz
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

from utils.helpers import parse_simple_time_expressions, format_datetime_for_user

def test_timezone():
    """Probar zona horaria de Chile"""
    
    print("🕐 Prueba de Zona Horaria - Chile")
    print("=" * 40)
    
    # Hora actual UTC
    utc_now = datetime.utcnow()
    print(f"⏰ UTC actual: {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Hora actual Chile
    chile_tz = pytz.timezone('America/Santiago')
    chile_now = datetime.now(chile_tz)
    print(f"🇨🇱 Chile actual: {chile_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Convertir Chile a UTC para almacenamiento
    chile_to_utc = chile_now.astimezone(pytz.UTC).replace(tzinfo=None)
    print(f"💾 Chile→UTC (storage): {chile_to_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Formato para usuario
    formatted = format_datetime_for_user(chile_to_utc, "America/Santiago")
    print(f"👤 Formato usuario: {formatted}")
    
    print("\n🧪 Pruebas de expresiones temporales:")
    print("-" * 40)
    
    test_expressions = [
        "en 10 segundos",
        "en 5 minutos", 
        "en 2 horas",
        "mañana"
    ]
    
    for expr in test_expressions:
        result = parse_simple_time_expressions(expr)
        if result:
            formatted_result = format_datetime_for_user(result, "America/Santiago")
            print(f"'{expr}' → {formatted_result}")
        else:
            print(f"'{expr}' → No interpretado")

if __name__ == "__main__":
    test_timezone()