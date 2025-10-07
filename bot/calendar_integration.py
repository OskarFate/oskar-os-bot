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
            email: Email de iCloud (oskarpardo@proton.me)
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