#!/usr/bin/env python3
"""
OskarOS Assistant Bot - Main Entry Point
Segundo Cerebro Personal con IA (Telegram + OpenRouter + MongoDB)
"""

import asyncio
import sys
import os
from loguru import logger

from config.settings import Settings
from bot.telegram_interface import TelegramBot
from bot.scheduler_service import SchedulerService
from bot.calendar_integration import initialize_apple_calendar
from database.connection import DatabaseManager
from utils.logger import setup_logger
from utils.health_server import HealthServer


async def main():
    """Punto de entrada principal del bot"""
    
    # Configurar logging
    setup_logger()
    logger.info("🚀 Iniciando OskarOS Assistant Bot...")
    
    try:
        # Cargar configuración
        settings = Settings()
        logger.info("⚙️ Configuración cargada")
        
        # Inicializar base de datos
        db_manager = DatabaseManager(settings.MONGODB_CONNECTION_STRING, settings.MONGODB_DATABASE_NAME)
        await db_manager.connect()
        logger.info("🗄️ Conexión a MongoDB establecida")
        
        # Inicializar Apple Calendar
        calendar_success = await initialize_apple_calendar(
            settings.ICLOUD_EMAIL, 
            settings.ICLOUD_PASSWORD
        )
        if calendar_success:
            logger.info("🍎 Apple Calendar integrado correctamente")
        else:
            logger.warning("⚠️ Apple Calendar no disponible (continuando sin integración)")
        
        # Inicializar health server para DigitalOcean
        health_port = int(os.getenv('PORT', '8080'))  # DigitalOcean usa PORT env var
        health_server = HealthServer(health_port)
        await health_server.start()
        
        # Inicializar servicios
        scheduler_service = SchedulerService(db_manager, settings.TELEGRAM_BOT_TOKEN)
        telegram_bot = TelegramBot(settings.TELEGRAM_BOT_TOKEN, db_manager, settings.OPENROUTER_API_KEY)
        
        # Iniciar scheduler en segundo plano
        scheduler_service.start()
        logger.info("⏰ Scheduler iniciado")
        
        # Iniciar bot de Telegram
        logger.info("📱 Iniciando bot de Telegram...")
        await telegram_bot.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 Deteniendo bot...")
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if 'scheduler_service' in locals():
            scheduler_service.stop()
        if 'health_server' in locals():
            await health_server.stop()
        if 'db_manager' in locals():
            await db_manager.close()
        logger.info("✅ Bot detenido correctamente")


if __name__ == "__main__":
    # Verificar versión de Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ requerido")
        sys.exit(1)
    
    # Ejecutar bot
    asyncio.run(main())