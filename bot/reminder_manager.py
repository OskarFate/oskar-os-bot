"""
Gestor de recordatorios con lógica de pre-alertas
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from loguru import logger

from database.connection import DatabaseManager
from database.models import Reminder, ReminderStatus
from config.settings import settings
from utils.helpers import clean_reminder_text


class ReminderManager:
    """Gestor de recordatorios y pre-alertas"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.pre_reminder_days = settings.PRE_REMINDER_DAYS
    
    def _calculate_pre_reminders(self, target_date: datetime) -> List[datetime]:
        """
        Calcular fechas de pre-recordatorios
        
        Args:
            target_date: Fecha objetivo del recordatorio
        
        Returns:
            Lista de fechas para pre-recordatorios (7d, 2d, 1d antes)
        """
        current_time = datetime.utcnow()
        pre_reminders = []
        
        for days_before in self.pre_reminder_days:
            pre_date = target_date - timedelta(days=days_before)
            
            # Solo agregar si la fecha es en el futuro
            if pre_date > current_time:
                pre_reminders.append(pre_date)
        
        # Ordenar cronológicamente
        pre_reminders.sort()
        
        logger.info(f"📅 Pre-recordatorios calculados: {len(pre_reminders)} alertas")
        return pre_reminders
    
    async def create_reminder(
        self, 
        user_id: int, 
        original_input: str, 
        reminder_text: str, 
        target_date: datetime
    ) -> bool:
        """
        Crear recordatorio con pre-alertas automáticas
        
        Args:
            user_id: ID del usuario de Telegram
            original_input: Input original del usuario
            reminder_text: Texto limpio del recordatorio
            target_date: Fecha y hora objetivo (UTC)
        
        Returns:
            True si se creó exitosamente
        """
        try:
            # Validar que la fecha no sea en el pasado
            current_time = datetime.utcnow()
            if target_date <= current_time:
                logger.warning(f"⚠️ Fecha en el pasado rechazada: {target_date} (actual: {current_time})")
                return False
            
            # Calcular pre-recordatorios
            pre_reminders = self._calculate_pre_reminders(target_date)
            
            # Limpiar texto del recordatorio
            clean_text = clean_reminder_text(reminder_text)
            
            # Crear datos del recordatorio
            reminder_data = {
                "user_id": user_id,
                "text": clean_text,
                "original_input": original_input,
                "date": target_date,
                "pre_reminders": pre_reminders,
                "status": ReminderStatus.PENDING,
                "notified": False,
                "pre_reminder_notified": {}  # Inicializar como dict vacío
            }
            
            # Guardar en base de datos
            success = await self.db.add_reminder(reminder_data)
            
            if success:
                logger.info(f"✅ Recordatorio creado para usuario {user_id}: '{clean_text}' en {target_date}")
                logger.info(f"⏰ {len(pre_reminders)} pre-recordatorios programados")
                return True
            else:
                logger.error(f"❌ Error guardando recordatorio en BD")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error creando recordatorio: {e}")
            return False
    
    async def get_pending_reminders_for_user(self, user_id: int, limit: int = 10) -> List[Reminder]:
        """
        Obtener recordatorios pendientes de un usuario (solo futuros)
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de recordatorios
        
        Returns:
            Lista de recordatorios pendientes ordenados por fecha (solo futuros)
        """
        try:
            reminders = await self.db.get_user_reminders(
                user_id=user_id,
                status=ReminderStatus.PENDING,
                limit=limit * 2  # Obtener más para filtrar
            )
            
            # Filtrar solo recordatorios futuros
            current_time = datetime.utcnow()
            future_reminders = [
                reminder for reminder in reminders 
                if reminder.date > current_time
            ]
            
            # Limitar al número solicitado
            future_reminders = future_reminders[:limit]
            
            logger.info(f"📋 Obtenidos {len(future_reminders)} recordatorios futuros para usuario {user_id}")
            return future_reminders
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo recordatorios pendientes: {e}")
            return []
    
    async def cleanup_past_reminders(self, user_id: Optional[int] = None) -> int:
        """
        Limpiar recordatorios pasados automáticamente
        
        Args:
            user_id: ID del usuario específico, o None para todos
        
        Returns:
            Número de recordatorios eliminados
        """
        try:
            current_time = datetime.utcnow()
            
            # Obtener recordatorios pasados
            if user_id:
                all_reminders = await self.db.get_user_reminders(user_id, limit=100)
            else:
                # TODO: Implementar get_all_reminders en la base de datos
                logger.info("⚠️ Limpieza global no implementada aún")
                return 0
            
            # Filtrar recordatorios pasados
            past_reminders = [
                reminder for reminder in all_reminders 
                if reminder.date <= current_time and reminder.status == ReminderStatus.PENDING
            ]
            
            # Marcar como completados (no eliminar, para historial)
            cleaned_count = 0
            for reminder in past_reminders:
                success = await self.update_reminder_status(
                    str(reminder.id), 
                    ReminderStatus.COMPLETED
                )
                if success:
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"🧹 Limpiados {cleaned_count} recordatorios pasados para usuario {user_id}")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"❌ Error limpiando recordatorios pasados: {e}")
            return 0
    
    async def get_due_reminders(self, tolerance_seconds: int = None) -> List[Dict[str, Any]]:
        """
        Obtener recordatorios que deben enviarse ahora
        
        Args:
            tolerance_seconds: Tolerancia en segundos (default de config)
        
        Returns:
            Lista de recordatorios con información adicional de tipo
        """
        if tolerance_seconds is None:
            tolerance_seconds = settings.REMINDER_TOLERANCE_SECONDS
        
        try:
            current_time = datetime.utcnow()
            pending_reminders = await self.db.get_pending_reminders(current_time, tolerance_seconds)
            
            due_reminders = []
            
            for reminder in pending_reminders:
                # Verificar recordatorio principal
                if not reminder.notified:
                    time_diff = abs((reminder.date - current_time).total_seconds())
                    if time_diff <= tolerance_seconds:
                        due_reminders.append({
                            "reminder": reminder,
                            "type": "main",
                            "notification_time": reminder.date
                        })
                
                # Verificar pre-recordatorios
                for pre_time in reminder.pre_reminders:
                    time_diff = abs((pre_time - current_time).total_seconds())
                    if time_diff <= tolerance_seconds:
                        pre_key = pre_time.isoformat()
                        if not reminder.pre_reminder_notified.get(pre_key, False):
                            # Calcular días antes
                            days_before = (reminder.date - pre_time).days
                            
                            due_reminders.append({
                                "reminder": reminder,
                                "type": "pre_reminder",
                                "notification_time": pre_time,
                                "days_before": days_before
                            })
            
            logger.info(f"⏰ {len(due_reminders)} recordatorios listos para enviar")
            return due_reminders
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo recordatorios vencidos: {e}")
            return []
    
    async def mark_reminder_notified(
        self, 
        reminder_id: str, 
        is_pre_reminder: bool = False, 
        pre_reminder_time: Optional[datetime] = None
    ) -> bool:
        """
        Marcar recordatorio como notificado
        
        Args:
            reminder_id: ID del recordatorio
            is_pre_reminder: Si es un pre-recordatorio
            pre_reminder_time: Tiempo del pre-recordatorio (si aplica)
        
        Returns:
            True si se marcó exitosamente
        """
        try:
            success = await self.db.mark_as_notified(
                reminder_id=reminder_id,
                is_pre_reminder=is_pre_reminder,
                pre_reminder_time=pre_reminder_time
            )
            
            if success:
                notification_type = "pre-recordatorio" if is_pre_reminder else "recordatorio principal"
                logger.info(f"✅ {notification_type} marcado como notificado: {reminder_id}")
                return True
            else:
                logger.error(f"❌ Error marcando recordatorio como notificado: {reminder_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error marcando recordatorio: {e}")
            return False
    
    async def update_reminder_status(self, reminder_id: str, new_status: ReminderStatus) -> bool:
        """
        Actualizar estado de recordatorio
        
        Args:
            reminder_id: ID del recordatorio
            new_status: Nuevo estado
        
        Returns:
            True si se actualizó exitosamente
        """
        try:
            # Nota: Esto requeriría un método adicional en DatabaseManager
            # Por ahora, solo logging
            logger.info(f"📝 Actualizar estado de recordatorio {reminder_id} a {new_status}")
            
            # TODO: Implementar update_reminder_status en DatabaseManager
            # success = await self.db.update_reminder_status(reminder_id, new_status)
            # return success
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error actualizando estado de recordatorio: {e}")
            return False
    
    async def get_weekly_reminder_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Obtener resumen semanal de recordatorios para un usuario
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Dict con estadísticas de la semana
        """
        try:
            # Obtener recordatorios de la última semana
            # Nota: Esto requeriría filtros de fecha en get_user_reminders
            # Por simplicidad, obtenemos todos los recordatorios recientes
            
            all_reminders = await self.db.get_user_reminders(user_id, limit=50)
            
            # Filtrar por última semana
            one_week_ago = datetime.utcnow() - timedelta(days=7)
            weekly_reminders = [
                r for r in all_reminders 
                if r.created_at >= one_week_ago
            ]
            
            # Calcular estadísticas
            total = len(weekly_reminders)
            completed = len([r for r in weekly_reminders if r.status == ReminderStatus.COMPLETED])
            pending = len([r for r in weekly_reminders if r.status == ReminderStatus.PENDING])
            missed = len([r for r in weekly_reminders if r.status == ReminderStatus.MISSED])
            
            summary = {
                "total": total,
                "completed": completed,
                "pending": pending,
                "missed": missed,
                "reminders": [r.dict() for r in weekly_reminders]
            }
            
            logger.info(f"📊 Resumen semanal para usuario {user_id}: {total} recordatorios")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo resumen semanal: {e}")
            return {
                "total": 0,
                "completed": 0,
                "pending": 0,
                "missed": 0,
                "reminders": []
            }