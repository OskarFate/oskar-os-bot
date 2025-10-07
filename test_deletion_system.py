#!/usr/bin/env python3
"""
Test script para el sistema de eliminación inteligente
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import logging

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.ai_interpreter import AIInterpreter
from bot.telegram_interface import TelegramInterface
from config.settings import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_deletion_patterns():
    """Probar patrones de detección de eliminación"""
    print("🧪 Testing deletion pattern detection...")
    
    # Crear instancia del interface (solo para acceder a los métodos)
    interface = TelegramInterface(None, None, None, None, None)
    
    # Test cases para detección de eliminación
    test_cases = [
        # Casos que DEBERÍAN ser detectados como eliminación
        ("eliminar gym", True),
        ("borra el recordatorio de pastillas", True),
        ("cancela todos los recordatorios del médico", True),
        ("quitar ejercicio", True),
        ("gym todos los días excepto viernes", True),  # Excepción
        ("pastillas todos los días menos el domingo", True),  # Excepción
        ("delete reminder", True),
        ("remove workout", True),
        ("anular cita médico", True),
        
        # Casos que NO deberían ser detectados como eliminación
        ("recordar ir al gym", False),
        ("pastillas todos los días", False),
        ("completar ejercicio mañana", False),
        ("nota sobre eliminar malos hábitos", False),
        ("tarea de programación", False),
    ]
    
    for test_text, expected in test_cases:
        result = interface._has_deletion_pattern(test_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{test_text}' → {result} (expected: {expected})")

async def test_ai_deletion_parsing():
    """Probar parseo de AI para eliminación"""
    print("\n🤖 Testing AI deletion parsing...")
    
    if not settings.OPENROUTER_API_KEY:
        print("⚠️ OPENROUTER_API_KEY no configurado, saltando test de AI")
        return
    
    ai = AIInterpreter()
    
    # Test cases para parseo de AI
    test_cases = [
        "eliminar gym",
        "borra todos los recordatorios de pastillas",
        "cancela la reunión de mañana",
        "gym todos los días excepto viernes",
        "pastillas todos los días menos el domingo",
        "remove all workout reminders",
        "delete reminder about doctor appointment"
    ]
    
    for test_text in test_cases:
        try:
            result = await ai.parse_deletion_request(test_text)
            print(f"📝 '{test_text}':")
            print(f"   Type: {result.get('type', 'unknown')}")
            print(f"   Target: {result.get('target', 'none')}")
            if 'exception_dates' in result:
                print(f"   Exceptions: {result['exception_dates']}")
            print()
        except Exception as e:
            print(f"❌ Error parsing '{test_text}': {e}")

async def test_reminder_detection():
    """Probar detección general de recordatorios incluyendo eliminación"""
    print("\n📝 Testing general reminder detection...")
    
    interface = TelegramInterface(None, None, None, None, None)
    
    test_cases = [
        ("recordar ir al gym mañana", True),
        ("eliminar gym", True),  # Debe ser detectado como recordatorio
        ("borra el recordatorio de pastillas", True),  # Debe ser detectado como recordatorio
        ("pastillas todos los días excepto viernes", True),  # Debe ser detectado como recordatorio
        ("hola, ¿cómo estás?", False),
        ("nota: comprar leche", False),
        ("el clima está lindo", False),
    ]
    
    for test_text, expected in test_cases:
        result = interface._is_reminder_request(test_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{test_text}' → {result} (expected: {expected})")

async def main():
    """Función principal de testing"""
    print("🧪 TESTING DELETION SYSTEM")
    print("=" * 50)
    
    try:
        await test_deletion_patterns()
        await test_reminder_detection()
        await test_ai_deletion_parsing()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())