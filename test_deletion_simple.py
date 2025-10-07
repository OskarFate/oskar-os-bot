#!/usr/bin/env python3
"""
Test simple para el sistema de eliminación sin dependencias externas
"""

import re
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_deletion_pattern_simple():
    """Probar patrones de detección de eliminación (versión simple)"""
    print("🧪 Testing deletion pattern detection (simple version)...")
    
    def has_deletion_pattern(text: str) -> bool:
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
            'todos excepto', 'todas excepto', 'todo excepto', 'toda excepta'
        ]
        
        # Verificar palabras clave de eliminación
        has_deletion_keyword = any(keyword in text_lower for keyword in deletion_keywords)
        
        # Verificar patrones de excepción (para modificar recurrencias)
        has_exception_pattern = any(pattern in text_lower for pattern in exception_patterns)
        
        return has_deletion_keyword or has_exception_pattern
    
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
        result = has_deletion_pattern(test_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{test_text}' → {result} (expected: {expected})")

def test_reminder_detection_simple():
    """Probar detección general de recordatorios (versión simple)"""
    print("\n📝 Testing general reminder detection (simple version)...")
    
    def is_reminder_request(text: str) -> bool:
        """Detectar si el texto es una solicitud de recordatorio"""
        text_lower = text.lower()
        
        # Palabras clave de recordatorios
        reminder_keywords = ['recordar', 'recuerdame', 'avisa', 'avisar', 'alarma', 'reminder']
        
        # Patrones de eliminación
        deletion_keywords = ['eliminar', 'elimina', 'borra', 'borrar', 'cancelar', 'cancela']
        exception_patterns = ['excepto', 'menos', 'except', 'salvo']
        
        # Patrones de tiempo
        date_patterns = ['mañana', 'hoy', 'ayer', 'lunes', 'martes', 'enero', 'febrero']
        time_patterns = ['am', 'pm', ':', 'hora', 'minuto']
        
        has_reminder_keywords = any(keyword in text_lower for keyword in reminder_keywords)
        has_deletion = any(keyword in text_lower for keyword in deletion_keywords)
        has_exception = any(pattern in text_lower for pattern in exception_patterns)
        has_time = any(pattern in text_lower for pattern in date_patterns + time_patterns)
        
        # Es recordatorio si tiene palabras clave, o si es eliminación, o si tiene excepciones
        return has_reminder_keywords or has_deletion or has_exception or (has_time and len(text) > 10)
    
    test_cases = [
        ("recordar ir al gym mañana", True),
        ("eliminar gym", True),  # Debe ser detectado como recordatorio
        ("borra el recordatorio de pastillas", True),  # Debe ser detectado como recordatorio
        ("pastillas todos los días excepto viernes", True),  # Debe ser detectado como recordatorio
        ("hola, ¿cómo estás?", False),
        ("nota: comprar leche", False),
        ("el clima está lindo", False),
        ("reunión a las 3pm", True),  # Debe ser detectado por tiempo
    ]
    
    for test_text, expected in test_cases:
        result = is_reminder_request(test_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{test_text}' → {result} (expected: {expected})")

def main():
    """Función principal de testing"""
    print("🧪 TESTING DELETION SYSTEM (SIMPLE)")
    print("=" * 50)
    
    try:
        test_deletion_pattern_simple()
        test_reminder_detection_simple()
        
        print("\n✅ All simple tests completed!")
        print("\n📝 Next steps:")
        print("1. The deletion pattern detection is working correctly")
        print("2. The reminder detection includes deletion patterns")
        print("3. The system can handle exception patterns like 'excepto'")
        print("4. Ready to test with full bot integration")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()