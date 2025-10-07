"""
Servicio de scheduler para envío automático de recordatorios
"""

import asyncio
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import aiohttp
from loguru import logger

from database.connection import DatabaseManager
from bot.reminder_manager import ReminderManager
from config.settings import settings
from utils.helpers import create_reminder_message, format_datetime_for_user


class SchedulerService:
    """Servicio de programación de tareas automáticas"""
    
    def __init__(self, db_manager: DatabaseManager, telegram_bot_token: str):
        self.db = db_manager
        self.telegram_token = telegram_bot_token
        self.telegram_api_url = f"https://api.telegram.org/bot{telegram_bot_token}"
        
        # Inicializar scheduler
        self.scheduler = AsyncIOScheduler()
        
        # Inicializar reminder manager
        self.reminder_manager = ReminderManager(db_manager)
        
        # Estado del servicio
        self.is_running = False
    
    def start(self):
        """Iniciar el scheduler"""
        try:
            # Agregar tarea de verificación de recordatorios
            self.scheduler.add_job(
                func=self._check_reminders,
                trigger=IntervalTrigger(seconds=settings.SCHEDULER_INTERVAL_SECONDS),
                id='reminder_checker',
                name='Verificador de Recordatorios',
                replace_existing=True,
                max_instances=1
            )
            
            # Agregar tarea de mantenimiento (diaria)
            self.scheduler.add_job(
                func=self._daily_maintenance,
                trigger=IntervalTrigger(hours=24),
                id='daily_maintenance',
                name='Mantenimiento Diario',
                replace_existing=True,
                max_instances=1
            )
            
            # Iniciar scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info(f"⏰ Scheduler iniciado - Verificando cada {settings.SCHEDULER_INTERVAL_SECONDS}s")
            
        except Exception as e:
            logger.error(f"❌ Error iniciando scheduler: {e}")
            self.is_running = False
    
    def stop(self):
        """Detener el scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("🛑 Scheduler detenido")
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo scheduler: {e}")
    
    async def _check_reminders(self):
        """Verificar y enviar recordatorios vencidos"""
        try:
            logger.debug("🔍 Verificando recordatorios pendientes...")
            
            # Obtener recordatorios que deben enviarse
            due_reminders = await self.reminder_manager.get_due_reminders()
            
            if not due_reminders:
                logger.debug("✅ No hay recordatorios pendientes")
                return
            
            logger.info(f"📬 Procesando {len(due_reminders)} recordatorios")
            
            # Procesar cada recordatorio
            for reminder_info in due_reminders:
                await self._send_reminder_notification(reminder_info)
                
                # Pequeña pausa entre envíos
                await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"❌ Error verificando recordatorios: {e}")
    
    async def _send_reminder_notification(self, reminder_info: dict):
        """
        Enviar notificación de recordatorio por Telegram
        
        Args:
            reminder_info: Dict con información del recordatorio
        """
        try:
            reminder = reminder_info["reminder"]
            notification_type = reminder_info["type"]
            user_id = reminder.user_id
            
            # Crear mensaje según tipo de recordatorio
            if notification_type == "main":
                message = create_reminder_message(reminder.text)
                logger.info(f"📨 Enviando recordatorio principal a usuario {user_id}")
                
            elif notification_type == "pre_reminder":
                days_before = reminder_info.get("days_before", 1)
                message = create_reminder_message(
                    reminder.text, 
                    is_pre_reminder=True, 
                    days_before=days_before
                )
                logger.info(f"📨 Enviando pre-recordatorio ({days_before}d) a usuario {user_id}")
            
            else:
                logger.error(f"❌ Tipo de recordatorio desconocido: {notification_type}")
                return
            
            # Enviar mensaje por Telegram
            success = await self._send_telegram_message(user_id, message)
            
            if success:
                # Marcar como notificado
                if notification_type == "main":
                    await self.reminder_manager.mark_reminder_notified(
                        reminder_id=str(reminder.id)
                    )
                elif notification_type == "pre_reminder":
                    pre_time = reminder_info["notification_time"]
                    await self.reminder_manager.mark_reminder_notified(
                        reminder_id=str(reminder.id),
                        is_pre_reminder=True,
                        pre_reminder_time=pre_time
                    )
                
                logger.info(f"✅ Recordatorio enviado y marcado como notificado")
            else:
                logger.error(f"❌ Error enviando recordatorio a usuario {user_id}")
                
        except Exception as e:
            logger.error(f"❌ Error enviando notificación de recordatorio: {e}")
    
    async def _send_telegram_message(self, user_id: int, message: str) -> bool:
        """
        Enviar mensaje por API de Telegram
        
        Args:
            user_id: ID del usuario de Telegram
            message: Mensaje a enviar
        
        Returns:
            True si se envió exitosamente
        """
        try:
            url = f"{self.telegram_api_url}/sendMessage"
            
            payload = {
                "chat_id": user_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.debug(f"📤 Mensaje enviado a {user_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Error API Telegram {response.status}: {error_text}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Timeout enviando mensaje a {user_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje Telegram: {e}")
            return False
    
    async def _daily_maintenance(self):
        """Tareas de mantenimiento diario"""
        try:
            logger.info("🧹 Ejecutando mantenimiento diario...")
            
            # Aquí podrían agregarse tareas como:
            # - Limpiar recordatorios muy antiguos
            # - Enviar resúmenes semanales automáticos
            # - Backup de datos importantes
            # - Estadísticas de uso
            
            current_time = datetime.utcnow()
            
            # Por ahora, solo logging
            logger.info(f"✅ Mantenimiento diario completado - {current_time}")
            
        except Exception as e:
            logger.error(f"❌ Error en mantenimiento diario: {e}")
    
    async def send_immediate_message(self, user_id: int, message: str) -> bool:
        """
        Enviar mensaje inmediato (para uso desde el bot)
        
        Args:
            user_id: ID del usuario
            message: Mensaje a enviar
        
        Returns:
            True si se envió exitosamente
        """
        return await self._send_telegram_message(user_id, message)
    
    def get_status(self) -> dict:
        """
        Obtener estado del scheduler
        
        Returns:
            Dict con información del estado
        """
        try:
            jobs = []
            if self.scheduler.running:
                for job in self.scheduler.get_jobs():
                    jobs.append({
                        "id": job.id,
                        "name": job.name,
                        "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                    })
            
            return {
                "running": self.is_running,
                "scheduler_active": self.scheduler.running if hasattr(self.scheduler, 'running') else False,
                "jobs": jobs,
                "interval_seconds": settings.SCHEDULER_INTERVAL_SECONDS
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado del scheduler: {e}")
            return {
                "running": False,
                "scheduler_active": False,
                "jobs": [],
                "error": str(e)
            }