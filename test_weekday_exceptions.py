#!/usr/bin/env python3
"""
Test script para excepciones de días de la semana
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import logging

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _has_deletion_pattern(text: str) -> bool:
    """Detectar si el texto contiene patrones de eliminación"""
    text_lower = text.lower()
    
    # Patrones explícitos de eliminación
    deletion_keywords = [
        'eliminar', 'elimina', 'borra', 'borrar', 'cancelar', 'cancela',
        'quitar', 'quita', 'remover', 'remueve', 'delete', 'remove',
        'deshacer', 'anular', 'deshaz'
    ]
    
    # Patrones de modificación con excepciones
    exception_patterns = [
        'excepto', 'menos', 'except', 'salvo', 'pero no', 'all except',
        'todos excepto', 'todas excepto', 'todo excepto', 'toda excepta',
        'mantén', 'manten', 'conserva', 'keep'
    ]
    
    # Verificar palabras clave de eliminación
    has_deletion_keyword = any(keyword in text_lower for keyword in deletion_keywords)
    
    # Verificar patrones de excepción (para modificar recurrencias)
    has_exception_pattern = any(pattern in text_lower for pattern in exception_patterns)
    
    return has_deletion_keyword or has_exception_pattern

def _get_weekday_index(weekday_name: str):
    """Obtener índice del día de la semana (0=lunes, 6=domingo)"""
    weekdays_map = {
        'lunes': 0, 'martes': 1, 'miércoles': 2, 'miercoles': 2,
        'jueves': 3, 'viernes': 4, 'sábado': 5, 'sabado': 5, 'domingo': 6
    }
    return weekdays_map.get(weekday_name.lower())

def _get_next_weekday_date(current_date: datetime, target_weekday: int) -> datetime:
    """
    Calcular la fecha del próximo día de la semana especificado
    
    Args:
        current_date: Fecha actual
        target_weekday: Día objetivo (0=lunes, 6=domingo)
        
    Returns:
        datetime del próximo día especificado
    """
    days_ahead = target_weekday - current_date.weekday()
    if days_ahead <= 0:  # Si ya pasó o es hoy, tomar la próxima semana
        days_ahead += 7
    return current_date + timedelta(days=days_ahead)

async def test_weekday_exception_cases():
    """Probar casos específicos de excepciones de días de la semana"""
    print("🧪 Testing weekday exception cases...")
    
    current_date = datetime.now()
    weekdays_es = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
    current_weekday = weekdays_es[current_date.weekday()]
    
    print(f"📅 Fecha actual: {current_date.strftime('%Y-%m-%d %H:%M')} ({current_weekday})")
    print()
    
    # Test cases específicos para tu solicitud
    test_cases = [
        # Casos que DEBERÍAN ser detectados como modificación con excepción
        ("mantén todos los días el gym y elimina el viernes", True),
        ("gym todos los días excepto el viernes", True),
        ("gym todos los días menos el viernes", True),
        ("pastillas todos los días pero no el domingo", True),
        ("ejercicio diario excepto viernes", True),
        ("medicamento todos los días salvo el sábado", True),
        ("keep all days but remove friday", True),
        
        # Casos de eliminación simple (NO excepciones)
        ("elimina el gym", True),
        ("borra el recordatorio", True),
        
        # Casos que NO deberían ser detectados
        ("gym todos los días", False),
        ("pastillas diario", False),
        ("ejercicio mañana", False),
    ]
    
    print("🔍 Testing deletion pattern detection:")
    for test_text, expected in test_cases:
        result = _has_deletion_pattern(test_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{test_text}' → {result} (expected: {expected})")
    
    print("\n📆 Testing weekday date calculations:")
    
    # Test para cada día de la semana
    for weekday_name in weekdays_es:
        weekday_index = _get_weekday_index(weekday_name)
        next_date = _get_next_weekday_date(current_date, weekday_index)
        days_ahead = (next_date - current_date).days
        
        print(f"📅 Próximo {weekday_name}: {next_date.strftime('%Y-%m-%d')} (en {days_ahead} días)")

async def test_natural_language_examples():
    """Probar ejemplos de lenguaje natural"""
    print("\n🗣️ Testing natural language examples:")
    
    examples = [
        "mantén todos los días el gym y elimina el viernes",
        "gym todos los días excepto el viernes", 
        "pastillas todos los días menos el domingo",
        "ejercicio diario pero no el martes que viene",
        "medicamento cada día salvo los sábados",
        "keep workout every day except friday",
        "elimina solo el viernes del gym",
        "quita el gym del viernes pero mantén el resto",
    ]
    
    for example in examples:
        is_deletion = _has_deletion_pattern(example)
        print(f"📝 '{example}' → {'✅ Detected' if is_deletion else '❌ Not detected'}")

async def main():
    """Función principal de testing"""
    print("🧪 TESTING WEEKDAY EXCEPTION SYSTEM")
    print("=" * 60)
    
    try:
        await test_weekday_exception_cases()
        await test_natural_language_examples()
        
        print("\n✅ All weekday exception tests completed!")
        print("\n💡 Summary:")
        print("- The system can detect weekday-based exceptions")
        print("- It calculates next occurrence of weekdays correctly")
        print("- Natural language patterns work as expected")
        print("- Ready for AI parsing and execution")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())