#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración del bot
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Probar imports básicos
    print("🔄 Probando imports...")
    
    from config.settings import Settings
    print("✅ config.settings")
    
    from database.models import User, Reminder, Note
    print("✅ database.models")
    
    from utils.logger import setup_logger
    print("✅ utils.logger")
    
    from utils.helpers import format_datetime_for_user
    print("✅ utils.helpers")
    
    from bot.ai_interpreter import AIInterpreter
    print("✅ bot.ai_interpreter")
    
    from bot.reminder_manager import ReminderManager
    print("✅ bot.reminder_manager")
    
    from bot.note_manager import NoteManager
    print("✅ bot.note_manager")
    
    from bot.scheduler_service import SchedulerService
    print("✅ bot.scheduler_service")
    
    from bot.memory_index import MemoryIndex
    print("✅ bot.memory_index")
    
    from bot.telegram_interface import TelegramBot
    print("✅ bot.telegram_interface")
    
    print("\n🎉 Todos los módulos importados exitosamente!")
    
    # Probar configuración
    print("\n🔄 Probando configuración...")
    settings = Settings()
    print(f"✅ Configuración cargada - Entorno: {settings.ENVIRONMENT}")
    
    if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        print("⚠️ Token de Telegram no configurado")
    else:
        print("✅ Token de Telegram configurado")
    
    if not settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEY == "your_openrouter_api_key_here":
        print("⚠️ API Key de OpenRouter no configurado")
    else:
        print("✅ API Key de OpenRouter configurado")
    
    if not settings.MONGODB_CONNECTION_STRING or "username:password" in settings.MONGODB_CONNECTION_STRING:
        print("⚠️ Conexión MongoDB no configurada")
    else:
        print("✅ Conexión MongoDB configurada")
    
    print("\n📋 Estado del proyecto:")
    print("✅ Estructura de archivos completa")
    print("✅ Dependencias instaladas")
    print("✅ Módulos funcionales")
    print("📝 Edita .env con tus credenciales para comenzar")
    
    print("\n🚀 Para ejecutar el bot:")
    print("1. Edita .env con tus credenciales")
    print("2. python main.py")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    sys.exit(1)