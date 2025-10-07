"""
Funciones auxiliares para el bot
"""

import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import pytz
from loguru import logger


def format_datetime_for_user(dt: datetime, timezone: str = "America/Santiago") -> str:
    """Formatear fecha y hora para mostrar al usuario"""
    try:
        # Convertir a zona horaria del usuario
        tz = pytz.timezone(timezone)
        local_dt = dt.replace(tzinfo=pytz.UTC).astimezone(tz)
        
        # Formato legible
        return local_dt.strftime("%d/%m/%Y a las %H:%M")
    except Exception as e:
        logger.error(f"Error formateando fecha: {e}")
        return dt.strftime("%d/%m/%Y a las %H:%M")


def parse_simple_time_expressions(text: str, current_time: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parser básico para expresiones temporales simples
    Fallback si la IA no responde
    """
    if current_time is None:
        # Usar hora de Chile
        chile_tz = pytz.timezone('America/Santiago')
        current_time = datetime.now(chile_tz).astimezone(pytz.UTC).replace(tzinfo=None)
    
    text = text.lower().strip()
    
    # Meses en español
    meses = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
        'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }
    
    # Patrones básicos
    patterns = [
        # "en X segundos"
        (r'en\s+(\d+)\s+segundos?', lambda m: current_time + timedelta(seconds=int(m.group(1)))),
        # "en X minutos"
        (r'en\s+(\d+)\s+minutos?', lambda m: current_time + timedelta(minutes=int(m.group(1)))),
        # "en X horas"
        (r'en\s+(\d+)\s+horas?', lambda m: current_time + timedelta(hours=int(m.group(1)))),
        # "en X días"
        (r'en\s+(\d+)\s+d[ií]as?', lambda m: current_time + timedelta(days=int(m.group(1)))),
        # "mañana"
        (r'mañana', lambda m: current_time + timedelta(days=1)),
        # "ahora"
        (r'ahora', lambda m: current_time),
        # "DD/MM/YYYY"
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', lambda m: datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)), 9, 0)),
        # "DD de MES de YYYY" o "DD MES YYYY"
        (r'(\d{1,2})\s+(?:de\s+)?(' + '|'.join(meses.keys()) + r')\s+(?:de\s+)?(\d{4})', 
         lambda m: datetime(int(m.group(3)), meses[m.group(2)], int(m.group(1)), 9, 0)),
    ]
    
    for pattern, func in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return func(match)
            except Exception as e:
                logger.error(f"Error parseando expresión '{text}': {e}")
                continue
    
    return None


def clean_reminder_text(text: str) -> str:
    """Limpiar texto de recordatorio removiendo expresiones temporales"""
    # Remover expresiones temporales comunes
    temporal_patterns = [
        r'\ben\s+\d+\s+(segundo|minuto|hora)s?\b',
        r'\bmañana\b',
        r'\bahora\b',
        r'\bel\s+\d{1,2}\s+de\s+\w+\b',
        r'\ba\s+las?\s+\d{1,2}(:\d{2})?\b',
    ]
    
    cleaned_text = text
    for pattern in temporal_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
    
    # Limpiar espacios extra
    cleaned_text = ' '.join(cleaned_text.split())
    
    return cleaned_text.strip()


def extract_keywords_from_text(text: str, min_length: int = 3) -> List[str]:
    """Extraer palabras clave de un texto"""
    # Palabras vacías en español
    stop_words = {
        'el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su',
        'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'este', 'esta', 'ese',
        'esa', 'esto', 'eso', 'mi', 'tu', 'sus', 'nos', 'me', 'si', 'ya', 'muy', 'más', 'pero',
        'cuando', 'donde', 'como', 'porque', 'hasta', 'sobre', 'todo', 'todos', 'estas', 'estos'
    }
    
    # Extraer palabras
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filtrar palabras clave
    keywords = [
        word for word in words 
        if len(word) >= min_length and word not in stop_words
    ]
    
    return list(set(keywords))  # Remover duplicados


def validate_telegram_user_id(user_id: Any) -> bool:
    """Validar ID de usuario de Telegram"""
    try:
        user_id = int(user_id)
        # Los IDs de Telegram son enteros positivos
        return user_id > 0
    except (ValueError, TypeError):
        return False


def truncate_text(text: str, max_length: int = 4000) -> str:
    """Truncar texto para evitar límites de Telegram"""
    if len(text) <= max_length:
        return text
    
    # Truncar y agregar indicador
    truncated = text[:max_length - 3]
    return truncated + "..."


def create_reminder_message(reminder_text: str, is_pre_reminder: bool = False, days_before: Optional[int] = None) -> str:
    """Crear mensaje de recordatorio formateado"""
    if is_pre_reminder and days_before:
        if days_before == 1:
            prefix = "🔔 Recordatorio para mañana:"
        else:
            prefix = f"⏰ Recordatorio en {days_before} días:"
    else:
        prefix = "🚨 ¡RECORDATORIO AHORA!:"
    
    return f"{prefix}\n\n📝 {reminder_text}"


def format_reminders_list(reminders: List[Dict[str, Any]]) -> str:
    """Formatear lista de recordatorios para mostrar"""
    if not reminders:
        return "📭 No tienes recordatorios pendientes."
    
    message_parts = ["📋 **Tus próximos recordatorios:**\n"]
    
    for i, reminder in enumerate(reminders, 1):
        date_str = format_datetime_for_user(reminder.get('date', datetime.utcnow()))
        text = reminder.get('text', 'Sin descripción')
        
        message_parts.append(f"{i}. 📅 {date_str}")
        message_parts.append(f"   📝 {text}\n")
    
    return "\n".join(message_parts)


def sanitize_input(text: str) -> str:
    """Sanitizar entrada del usuario"""
    # Remover caracteres especiales peligrosos
    sanitized = re.sub(r'[<>&]', '', text)
    
    # Limitar longitud
    sanitized = sanitized[:1000]
    
    return sanitized.strip()


def parse_natural_date(text: str) -> Optional[datetime]:
    """
    Parsear fechas en lenguaje natural español
    """
    from datetime import datetime, timedelta
    import pytz
    
    try:
        now = datetime.now(pytz.timezone('America/Mexico_City'))
        text_lower = text.lower().strip()
        
        # Patrones de fecha comunes
        if 'mañana' in text_lower:
            return now + timedelta(days=1)
        elif 'hoy' in text_lower:
            return now
        elif 'pasado mañana' in text_lower:
            return now + timedelta(days=2)
        elif 'la próxima semana' in text_lower or 'próxima semana' in text_lower:
            return now + timedelta(weeks=1)
        elif 'el próximo mes' in text_lower or 'próximo mes' in text_lower:
            return now + timedelta(days=30)
        
        # Días de la semana
        weekdays = {
            'lunes': 0, 'martes': 1, 'miércoles': 2, 'jueves': 3,
            'viernes': 4, 'sábado': 5, 'domingo': 6
        }
        
        for day_name, day_num in weekdays.items():
            if day_name in text_lower:
                days_ahead = day_num - now.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                return now + timedelta(days=days_ahead)
        
        # Patrones de hora
        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm|h)', text_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            period = time_match.group(3)
            
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Si no se puede parsear, devolver None
        return None
        
    except Exception:
        return None