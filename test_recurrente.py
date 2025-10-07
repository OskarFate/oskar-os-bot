#!/usr/bin/env python3
"""
Test del sistema de recordatorios recurrentes
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.ai_interpreter import AIInterpreter
from config.settings import Settings
from datetime import datetime
import json

async def test_recurring_reminders():
    """Probar diferentes casos de recordatorios recurrentes"""
    
    settings = Settings()
    if not settings.OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY no configurada")
        return
    
    ai = AIInterpreter(settings.OPENROUTER_API_KEY)
    current_time = datetime.utcnow()
    
    test_cases = [
        # Casos diarios
        "tomar pastilla todos los días a las 8",
        "ejercitar cada día",
        "revisar email every day",
        "daily backup",
        
        # Casos semanales específicos
        "reunión todos los lunes",
        "llamar mamá todos los domingos",
        "gym todos los miércoles",
        
        # Casos de frecuencia personalizada
        "día por medio revisar proyecto",
        "cada dos días regar plantas",
        "cada semana hacer compras",
        
        # Casos médicos
        "medicamento cada 8 horas",
        "pastillas cada 12 horas",
        
        # Casos laborales
        "lunes a viernes standups",
        "fin de semana limpieza",
        "cada mes hacer backup",
        
        # Casos que NO son recurrentes
        "mañana ir al médico",
        "en 2 horas llamar Juan",
        "el viernes presentación",
    ]
    
    print("🧪 Probando sistema de recordatorios recurrentes...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Caso {i}: '{test_case}'")
        
        try:
            result = await ai.parse_recurring_reminder(test_case, current_time)
            
            if result:
                print(f"✅ RECURRENTE detectado: {len(result)} recordatorios")
                for j, reminder in enumerate(result[:3], 1):  # Mostrar solo los primeros 3
                    print(f"   {j}. {reminder['text']} → {reminder['date'].strftime('%Y-%m-%d %H:%M')}")
                if len(result) > 3:
                    print(f"   ... y {len(result) - 3} más")
            else:
                print("❌ No recurrente")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("🎯 Prueba completada!")

if __name__ == "__main__":
    asyncio.run(test_recurring_reminders())