"""
Integración con Apple Calendar (iCloud CalDAV)
Permite crear eventos automáticamente en el calendario del usuario
"""

import caldav
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from icalendar import Calendar, Event
import pytz
from loguru import logger

class AppleCalendarIntegration:
    """Maneja la integración con Apple Calendar vía CalDAV"""
    
    def __init__(self, email: str, password: str, calendar_url: str = "https://caldav.icloud.com"):
        """
        Inicializar conexión con iCloud Calendar
        
        Args:
            email: Email de iCloud (tu_email@icloud.com)
            password: Contraseña de aplicación generada
            calendar_url: URL del servidor CalDAV de iCloud
        """
        self.email = email
        self.password = password
        self.calendar_url = calendar_url
        self.client = None
        self.principal = None
        self.calendar = None
        
        # Zona horaria de Chile
        self.chile_tz = pytz.timezone('America/Santiago')
    
    async def connect(self) -> bool:
        """
        Establecer conexión con iCloud Calendar
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        try:
            # Crear cliente CalDAV
            self.client = caldav.DAVClient(
                url=self.calendar_url,
                username=self.email,
                password=self.password
            )
            
            # Obtener principal (usuario)
            self.principal = self.client.principal()
            
            # Obtener calendarios
            calendars = self.principal.calendars()
            
            if not calendars:
                logger.error("❌ No se encontraron calendarios en iCloud")
                return False
            
            # Usar el primer calendario disponible (generalmente es el principal)
            self.calendar = calendars[0]
            logger.info(f"✅ Conectado a Apple Calendar: {self.calendar.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando a Apple Calendar: {e}")
            return False
    
    async def create_event(self, 
                          title: str, 
                          start_datetime: datetime, 
                          description: str = "",
                          duration_hours: int = 1) -> bool:
        """
        Crear un evento en Apple Calendar
        
        Args:
            title: Título del evento
            start_datetime: Fecha y hora de inicio (UTC)
            description: Descripción del evento
            duration_hours: Duración en horas (default: 1)
        
        Returns:
            True si el evento se creó exitosamente
        """
        try:
            if not self.calendar:
                logger.error("❌ No hay conexión al calendario")
                return False
            
            # Convertir UTC a zona horaria de Chile
            chile_start = start_datetime.replace(tzinfo=pytz.UTC).astimezone(self.chile_tz)
            chile_end = chile_start + timedelta(hours=duration_hours)
            
            # Crear evento iCalendar
            cal = Calendar()
            cal.add('prodid', '-//OskarOS Assistant Bot//ES')
            cal.add('version', '2.0')
            
            event = Event()
            event.add('summary', title)
            event.add('description', description)
            event.add('dtstart', chile_start)
            event.add('dtend', chile_end)
            event.add('dtstamp', datetime.now(pytz.UTC))
            
            # Generar UID único
            import uuid
            event.add('uid', f"{uuid.uuid4()}@oskaros-bot")
            
            cal.add_component(event)
            
            # Crear evento en el calendario
            self.calendar.save_event(cal.to_ical().decode('utf-8'))
            
            logger.info(f"📅 Evento creado en Apple Calendar: {title} - {chile_start.strftime('%Y-%m-%d %H:%M')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando evento en Apple Calendar: {e}")
            return False
    
    async def create_reminder_event(self, reminder_data: Dict[str, Any]) -> bool:
        """
        Crear evento en calendario basado en datos del recordatorio
        
        Args:
            reminder_data: Datos del recordatorio con 'text', 'date', etc.
        
        Returns:
            True si el evento se creó exitosamente
        """
        try:
            title = reminder_data.get('text', 'Recordatorio')
            target_date = reminder_data.get('date')
            original_input = reminder_data.get('original_input', '')
            
            if not target_date:
                logger.warning("⚠️ No hay fecha válida para crear evento")
                return False
            
            # Descripción del evento
            description = f"Recordatorio creado por OskarOS Bot\n\nTexto original: {original_input}"
            
            # Determinar duración basada en el tipo de evento
            duration = self._get_event_duration(title.lower())
            
            return await self.create_event(
                title=title,
                start_datetime=target_date,
                description=description,
                duration_hours=duration
            )
            
        except Exception as e:
            logger.error(f"❌ Error creando evento de recordatorio: {e}")
            return False
    
    def _get_event_duration(self, event_text: str) -> int:
        """
        Determinar duración apropiada basada en el tipo de evento
        
        Args:
            event_text: Texto del evento en minúsculas
        
        Returns:
            Duración en horas
        """
        # Eventos de día completo o largos
        if any(word in event_text for word in ['examen', 'evaluación', 'prueba', 'certamen']):
            return 3  # 3 horas para exámenes
        
        # Reuniones y presentaciones
        elif any(word in event_text for word in ['reunión', 'meeting', 'presentación', 'junta']):
            return 1  # 1 hora para reuniones
        
        # Actividades médicas
        elif any(word in event_text for word in ['médico', 'doctor', 'dentista', 'consulta']):
            return 1  # 1 hora para citas médicas
        
        # Ejercicio
        elif any(word in event_text for word in ['gym', 'ejercitar', 'deporte', 'correr', 'nadar']):
            return 2  # 2 horas para ejercicio
        
        # Tareas rápidas
        elif any(word in event_text for word in ['llamar', 'contactar', 'enviar', 'revisar']):
            return 0.5  # 30 minutos para tareas rápidas
        
        # Actividades de estudio
        elif any(word in event_text for word in ['estudiar', 'leer', 'practicar', 'tarea']):
            return 2  # 2 horas para estudio
        
        # Default
        else:
            return 1  # 1 hora por defecto
    
    async def delete_event_by_title_and_date(self, title: str, target_date: datetime) -> bool:
        """
        Eliminar evento específico por título y fecha
        
        Args:
            title: Título del evento a eliminar
            target_date: Fecha específica del evento
        
        Returns:
            True si se eliminó exitosamente
        """
        try:
            if not self.calendar:
                logger.error("❌ No hay conexión al calendario")
                return False
            
            # Convertir a zona horaria de Chile para buscar
            chile_tz = pytz.timezone('America/Santiago')
            chile_date = target_date.replace(tzinfo=pytz.UTC).astimezone(chile_tz)
            
            # Buscar eventos en el día específico
            start_of_day = chile_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = chile_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Obtener eventos del día
            events = self.calendar.date_search(
                start_of_day.astimezone(pytz.UTC),
                end_of_day.astimezone(pytz.UTC)
            )
            
            deleted_count = 0
            for event in events:
                try:
                    # Obtener datos del evento
                    event_data = event.data
                    if hasattr(event_data, 'summary') and event_data.summary:
                        event_title = str(event_data.summary)
                        
                        # Comparar títulos (case insensitive y parcial)
                        if title.lower() in event_title.lower() or event_title.lower() in title.lower():
                            event.delete()
                            deleted_count += 1
                            logger.info(f"🗑️ Evento eliminado de Apple Calendar: {event_title}")
                            
                except Exception as e:
                    logger.warning(f"⚠️ Error procesando evento individual: {e}")
                    continue
            
            if deleted_count > 0:
                logger.info(f"✅ {deleted_count} eventos eliminados de Apple Calendar")
                return True
            else:
                logger.warning(f"⚠️ No se encontraron eventos para eliminar: {title}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error eliminando evento de Apple Calendar: {e}")
            return False
    
    async def delete_events_by_title_pattern(self, title_pattern: str, date_range_days: int = 365) -> int:
        """
        Eliminar múltiples eventos que coincidan con un patrón de título
        
        Args:
            title_pattern: Patrón del título a buscar
            date_range_days: Rango de días a buscar (default: 1 año)
        
        Returns:
            Número de eventos eliminados
        """
        try:
            if not self.calendar:
                logger.error("❌ No hay conexión al calendario")
                return 0
            
            # Rango de fechas para buscar
            start_date = datetime.now(pytz.UTC)
            end_date = start_date + timedelta(days=date_range_days)
            
            # Obtener eventos en el rango
            events = self.calendar.date_search(start_date, end_date)
            
            deleted_count = 0
            for event in events:
                try:
                    event_data = event.data
                    if hasattr(event_data, 'summary') and event_data.summary:
                        event_title = str(event_data.summary)
                        
                        # Comparar con patrón
                        if title_pattern.lower() in event_title.lower():
                            event.delete()
                            deleted_count += 1
                            logger.info(f"🗑️ Evento eliminado: {event_title}")
                            
                except Exception as e:
                    logger.warning(f"⚠️ Error eliminando evento: {e}")
                    continue
            
            logger.info(f"✅ {deleted_count} eventos eliminados de Apple Calendar")
            return deleted_count
                
        except Exception as e:
            logger.error(f"❌ Error eliminando eventos por patrón: {e}")
            return 0
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Probar la conexión y devolver información del calendario
        
        Returns:
            Diccionario con información de la conexión
        """
        try:
            connected = await self.connect()
            
            if not connected:
                return {
                    "success": False,
                    "error": "No se pudo conectar a Apple Calendar"
                }
            
            calendar_info = {
                "success": True,
                "calendar_name": self.calendar.name if self.calendar else "Desconocido",
                "email": self.email,
                "server": self.calendar_url
            }
            
            # Intentar obtener algunos eventos recientes para verificar acceso
            try:
                events = self.calendar.events()
                calendar_info["events_count"] = len(list(events))
            except:
                calendar_info["events_count"] = "No disponible"
            
            return calendar_info
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_event_title(self, old_title: str, new_title: str, date: datetime) -> bool:
        """
        Actualizar el título de un evento existente
        
        Args:
            old_title: Título actual del evento
            new_title: Nuevo título para el evento
            date: Fecha del evento para ayudar a localizarlo
        
        Returns:
            True si se actualizó exitosamente
        """
        try:
            if not self.calendar:
                logger.error("❌ No hay conexión al calendario")
                return False
            
            # Buscar evento en un rango de ±1 día
            search_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            search_end = search_start + timedelta(days=1)
            
            events = self.calendar.date_search(search_start, search_end)
            
            for event in events:
                try:
                    event_data = event.data
                    if hasattr(event_data, 'summary') and event_data.summary:
                        event_title = str(event_data.summary)
                        
                        # Verificar si coincide el título
                        if old_title.lower() in event_title.lower():
                            # Actualizar el título
                            event_data.summary = new_title
                            event.save()
                            
                            logger.info(f"✅ Evento actualizado en Apple Calendar: '{old_title}' → '{new_title}'")
                            return True
                            
                except Exception as e:
                    logger.warning(f"⚠️ Error procesando evento individual: {e}")
                    continue
            
            logger.warning(f"⚠️ No se encontró evento para actualizar: {old_title}")
            return False
                
        except Exception as e:
            logger.error(f"❌ Error actualizando evento en Apple Calendar: {e}")
            return False


# Instancia global (se inicializará en main.py)
apple_calendar: Optional[AppleCalendarIntegration] = None


async def initialize_apple_calendar(email: str, password: str) -> bool:
    """
    Inicializar la integración con Apple Calendar
    
    Args:
        email: Email de iCloud
        password: Contraseña de aplicación
    
    Returns:
        True si se inicializó correctamente
    """
    global apple_calendar
    
    if not email or not password:
        logger.warning("⚠️ Credenciales de Apple Calendar no configuradas")
        return False
    
    try:
        apple_calendar = AppleCalendarIntegration(email, password)
        connected = await apple_calendar.connect()
        
        if connected:
            logger.info("🍎 Apple Calendar integración inicializada correctamente")
            return True
        else:
            logger.error("❌ No se pudo conectar a Apple Calendar")
            apple_calendar = None
            return False
            
    except Exception as e:
        logger.error(f"❌ Error inicializando Apple Calendar: {e}")
        apple_calendar = None
        return False


async def delete_calendar_event(title: str, target_date: datetime) -> bool:
    """
    Eliminar evento específico de Apple Calendar (función de conveniencia)
    
    Args:
        title: Título del evento
        target_date: Fecha del evento
    
    Returns:
        True si se eliminó exitosamente
    """
    global apple_calendar
    
    if not apple_calendar:
        logger.warning("⚠️ Apple Calendar no inicializado")
        return False
    
    return await apple_calendar.delete_event_by_title_and_date(title, target_date)


async def delete_calendar_events_by_pattern(title_pattern: str) -> int:
    """
    Eliminar múltiples eventos de Apple Calendar por patrón
    
    Args:
        title_pattern: Patrón del título a buscar
    
    Returns:
        Número de eventos eliminados
    """
    global apple_calendar
    
    if not apple_calendar:
        logger.warning("⚠️ Apple Calendar no inicializado")
        return 0
    
    return await apple_calendar.delete_events_by_title_pattern(title_pattern)


async def create_calendar_event(reminder_data: Dict[str, Any]) -> bool:
    """
    Crear evento en Apple Calendar (función de conveniencia)
    
    Args:
        reminder_data: Datos del recordatorio
    
    Returns:
        True si el evento se creó exitosamente
    """
    global apple_calendar
    
    if not apple_calendar:
        logger.warning("⚠️ Apple Calendar no inicializado")
        return False
    
    return await apple_calendar.create_reminder_event(reminder_data)