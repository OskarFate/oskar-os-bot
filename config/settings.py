"""
Configuración global del OskarOS Assistant Bot
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class Settings:
    """Configuración centralizada del bot"""
    
    def __init__(self):
        # Telegram Bot
        self.TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        
        # OpenRouter API (Llama 3.3 FREE)
        self.OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
        self.OPENROUTER_API_URL: str = "https://openrouter.ai/api/v1/chat/completions"
        self.LLAMA_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"
        
        # MongoDB Atlas
        self.MONGODB_URI: str = os.getenv("MONGODB_URI", "")
        self.MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "oskar_os_db")
        
        # Apple Calendar (iCloud CalDAV)
        self.ICLOUD_EMAIL: str = os.getenv("ICLOUD_EMAIL", "")
        self.ICLOUD_PASSWORD: str = os.getenv("ICLOUD_PASSWORD", "")
        self.ICLOUD_CALENDAR_URL: str = "https://caldav.icloud.com"
        
        # Scheduler
        self.SCHEDULER_INTERVAL_SECONDS: int = 60  # Revisar cada 60 segundos
        self.REMINDER_TOLERANCE_SECONDS: int = 30  # ±30 segundos de tolerancia
        
        # Pre-recordatorios automáticos
        self.PRE_REMINDER_DAYS: list = [7, 2, 1]  # 7 días, 2 días, 1 día antes
        
        # Configuración de IA
        self.AI_TEMPERATURE: float = 0.4
        self.AI_MAX_TOKENS: int = 500
        self.AI_TIMEOUT_SECONDS: int = 10
        
        # Timezone
        self.DEFAULT_TIMEZONE: str = os.getenv("DEFAULT_TIMEZONE", "UTC")
        
        # Logging
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        
        # Validar configuración requerida
        self._validate_required_vars()
    
    def _validate_required_vars(self):
        """Validar configuración requerida"""
        required_vars = [
            ("TELEGRAM_BOT_TOKEN", self.TELEGRAM_BOT_TOKEN),
            ("OPENROUTER_API_KEY", self.OPENROUTER_API_KEY),
            ("MONGODB_URI", self.MONGODB_URI),
        ]
        
        missing_vars = [var_name for var_name, var_value in required_vars if not var_value]
        
        if missing_vars:
            print(f"⚠️ Variables de entorno faltantes: {', '.join(missing_vars)}")
            print("📝 Edita el archivo .env con tus credenciales")
    
    @property
    def is_production(self) -> bool:
        """Verificar si está en producción"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Verificar si está en desarrollo"""
        return self.ENVIRONMENT.lower() == "development"


# Instancia global de configuración
settings = Settings()