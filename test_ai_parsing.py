#!/usr/bin/env python3
"""
Test script para verificar el parsing de IA con mensajes académicos
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from bot.ai_interpreter import AIInterpreter
from config.settings import Settings

async def test_ai_parsing():
    """Probar el parsing de IA con diferentes mensajes académicos"""
    
    # Inicializar AI interpreter
    settings = Settings()
    ai = AIInterpreter(settings.OPENROUTER_API_KEY)
    
    # Casos de prueba
    test_cases = [
        "Evaluación escrita 12/09/2025",
        "40% RA1-2-3: Informe Caso Logística Completo. FECHA DE ENTREGA: 5 OCTUBRE 2025",
        "todo estos es marketing\n\n26% RA2-2-3: ejercicios EoQ + Informe Caso de Gestión de Abastecimiento. \nFECHA DE ENTREGA: 26 DE OCTUBRE 2025\n\n24% RA3-2-3: Presentación empresa productiva.\nFECHA DE ENTREGA: Del 11 al 15 de noviembre 2025 ( proximamente mas info)"
    ]
    
    for i, test_message in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"PRUEBA {i}")
        print(f"{'='*60}")
        print(f"Mensaje: {test_message[:80]}...")
        print("\nProcesando con IA...")
        
        try:
            reminders = await ai.parse_multiple_reminders(test_message)
            
            if reminders:
                print(f"\n✅ Se encontraron {len(reminders)} recordatorios:")
                for j, reminder in enumerate(reminders, 1):
                    print(f"  {j}. Texto: {reminder['text']}")
                    print(f"     Fecha: {reminder['date']}")
            else:
                print("❌ No se encontraron recordatorios")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("PRUEBAS COMPLETADAS")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(test_ai_parsing())