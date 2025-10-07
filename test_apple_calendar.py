#!/usr/bin/env python3
"""
Test de integración con Apple Calendar
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.calendar_integration import AppleCalendarIntegration, initialize_apple_calendar
from config.settings import Settings
from datetime import datetime, timedelta
import pytz

async def test_apple_calendar():
    """Probar conexión con Apple Calendar"""
    
    settings = Settings()
    
    print("🧪 Probando integración con Apple Calendar...")
    print(f"📧 Email: {settings.ICLOUD_EMAIL}")
    print(f"🔑 Password: {'*' * len(settings.ICLOUD_PASSWORD) if settings.ICLOUD_PASSWORD else 'No configurada'}")
    print()
    
    if not settings.ICLOUD_EMAIL or not settings.ICLOUD_PASSWORD:
        print("❌ Credenciales de iCloud no configuradas")
        return
    
    # Inicializar integración
    print("🔄 Inicializando Apple Calendar...")
    success = await initialize_apple_calendar(settings.ICLOUD_EMAIL, settings.ICLOUD_PASSWORD)
    
    if not success:
        print("❌ No se pudo inicializar Apple Calendar")
        return
    
    # Crear integración directa para testing
    calendar = AppleCalendarIntegration(settings.ICLOUD_EMAIL, settings.ICLOUD_PASSWORD)
    
    # Probar conexión
    print("🔄 Probando conexión...")
    calendar_info = await calendar.test_connection()
    
    if calendar_info.get("success", False):
        print("✅ Conexión exitosa!")
        print(f"📅 Calendario: {calendar_info.get('calendar_name', 'N/A')}")
        print(f"📊 Eventos: {calendar_info.get('events_count', 'N/A')}")
        print()
        
        # Probar crear evento de prueba
        print("🔄 Creando evento de prueba...")
        chile_tz = pytz.timezone('America/Santiago')
        test_date = datetime.now(chile_tz) + timedelta(hours=1)
        
        event_success = await calendar.create_event(
            title="Test OskarOS Bot - Examen",
            start_datetime=test_date.astimezone(pytz.UTC),
            description="Evento de prueba creado por OskarOS Assistant Bot",
            duration_hours=3
        )
        
        if event_success:
            print("✅ Evento de prueba creado exitosamente!")
            print(f"📅 Fecha: {test_date.strftime('%Y-%m-%d %H:%M')} (Chile)")
            print("📱 Revisa tu calendario en iPhone/iPad/Mac")
        else:
            print("❌ No se pudo crear evento de prueba")
        
    else:
        print("❌ Error en conexión:")
        print(f"Error: {calendar_info.get('error', 'Desconocido')}")
    
    print("\n🎯 Prueba completada!")

if __name__ == "__main__":
    asyncio.run(test_apple_calendar())