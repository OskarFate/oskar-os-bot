#!/usr/bin/env python3
"""
Versión de prueba del bot sin dependencias externas
"""

import asyncio
import sys
from datetime import datetime
from typing import Dict, Any

# Mock classes para testing
class MockDatabaseManager:
    def __init__(self, *args, **kwargs):
        self.connected = False
    
    async def connect(self):
        print("🗄️ Mock Database conectada")
        self.connected = True
        return True
    
    async def close(self):
        print("🗄️ Mock Database cerrada")
    
    async def add_user(self, user_data):
        print(f"👤 Mock: Usuario agregado - {user_data.get('user_id')}")
        return True

class MockSchedulerService:
    def __init__(self, *args, **kwargs):
        pass
    
    def start(self):
        print("⏰ Mock Scheduler iniciado")
    
    def stop(self):
        print("🛑 Mock Scheduler detenido")

class MockTelegramBot:
    def __init__(self, token, *args, **kwargs):
        self.token = token
    
    async def start(self):
        if not self.token or self.token == "your_telegram_bot_token_here":
            print("❌ Token de Telegram no configurado")
            print("📝 Configura TELEGRAM_BOT_TOKEN en .env")
            return
        
        print(f"🤖 Mock Bot iniciado con token: {self.token[:10]}...")
        print("📱 Bot corriendo en modo de prueba")
        
        # Simular bot corriendo
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("🛑 Bot detenido por usuario")

async def main():
    """Punto de entrada para testing"""
    
    try:
        print("🚀 Iniciando OskarOS Assistant Bot (MODO TEST)...")
        
        # Cargar configuración
        from config.settings import Settings
        settings = Settings()
        print("⚙️ Configuración cargada")
        
        # Mock services
        db_manager = MockDatabaseManager()
        await db_manager.connect()
        
        scheduler_service = MockSchedulerService()
        telegram_bot = MockTelegramBot(settings.TELEGRAM_BOT_TOKEN)
        
        # Iniciar servicios
        scheduler_service.start()
        print("⏰ Scheduler iniciado")
        
        # Iniciar bot
        print("📱 Iniciando bot de Telegram...")
        await telegram_bot.start()
        
    except KeyboardInterrupt:
        print("🛑 Deteniendo bot...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Cleanup
        if 'scheduler_service' in locals():
            scheduler_service.stop()
        if 'db_manager' in locals():
            await db_manager.close()
        print("✅ Bot detenido correctamente")

if __name__ == "__main__":
    asyncio.run(main())