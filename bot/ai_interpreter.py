"""
Intérprete de IA usando Llama 3.3 70B via OpenRouter
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import aiohttp
import asyncio
import pytz
from loguru import logger

from config.settings import settings
from utils.helpers import parse_simple_time_expressions


class AIInterpreter:
    """Intérprete de IA para procesar lenguaje natural"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = settings.OPENROUTER_API_URL
        self.model = settings.LLAMA_MODEL
        self.timeout = settings.AI_TIMEOUT_SECONDS
        
    async def _make_api_call(self, messages: List[Dict[str, str]], temperature: float = None) -> Optional[str]:
        """Hacer llamada a la API de OpenRouter"""
        if temperature is None:
            temperature = settings.AI_TEMPERATURE
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://oskaros-bot.com",
            "X-Title": "OskarOS Assistant Bot"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": settings.AI_MAX_TOKENS,
            "stream": False
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"].strip()
                    else:
                        error_text = await response.text()
                        logger.error(f"Error API OpenRouter {response.status}: {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("⏱️ Timeout en llamada a OpenRouter")
            return None
        except Exception as e:
            logger.error(f"❌ Error en llamada a OpenRouter: {e}")
            return None
    
    async def interpret_time_expression(self, user_input: str, current_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        Interpretar expresión temporal en lenguaje natural
        
        Args:
            user_input: Texto del usuario (ej: "en 3 horas", "mañana a las 9")
            current_time: Tiempo actual (en zona horaria de Chile)
        
        Returns:
            datetime en UTC o None si no se puede interpretar
        """
        if current_time is None:
            # Obtener hora actual de Chile y convertir a UTC para almacenamiento
            chile_tz = pytz.timezone('America/Santiago')
            current_time = datetime.now(chile_tz).astimezone(pytz.UTC).replace(tzinfo=None)
        
        # Intentar parser básico primero (más rápido)
        basic_result = parse_simple_time_expressions(user_input, current_time)
        if basic_result:
            logger.info(f"⚡ Interpretación básica exitosa: {user_input} -> {basic_result}")
            return basic_result
        
        # Usar IA para casos complejos - SISTEMA ULTRA COMPLETO
        system_prompt = f"""Eres un experto ULTRA-INTELIGENTE en interpretar expresiones temporales en español chileno, incluyendo lenguaje coloquial, académico, profesional, y casos extremos.

Fecha y hora actual: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')} (Chile: América/Santiago)

Tu tarea: Convertir CUALQUIER expresión temporal del usuario a formato ISO8601 UTC.

CASOS QUE DEBES MANEJAR (SÚPER COMPLETOS):

1. LENGUAJE NATURAL BÁSICO:
   - "en X segundos/minutos/horas/días/semanas/meses/años"
   - "mañana", "hoy", "pasado mañana", "ayer", "anteayer"
   - "esta tarde", "esta noche", "esta mañana", "esta madrugada"
   - "el lunes", "el próximo viernes", "la próxima semana", "el mes que viene"

2. LENGUAJE COLOQUIAL CHILENO EXTREMO:
   - "pasado mañana", "el otro lunes", "la otra semana", "el próximo año"
   - "al tiro" (inmediato, +30 seg), "al rato" (en 1-2 horas), "altiro", "altoque"
   - "lueguito" (30-60 min), "ratito" (15-30 min), "cachito" (5-15 min)
   - "tempranito" (07:00), "en la once" (17:00), "en la mañanita" (06:00)
   - "yapo" (ya), "bacán" (contexto positivo), "cachái"

3. HORARIOS ESPECÍFICOS Y FORMATOS INTERNACIONALES:
   - "a las 18:00", "a las 9", "al mediodía", "a medianoche", "al amanecer", "al atardecer"
   - "en la mañana" (09:00), "en la tarde" (15:00), "en la noche" (20:00), "en la madrugada" (03:00)
   - "7:30 am", "3:15 pm", "14h30", "15:45hs", "2 pm", "8:30AM", "22:00hrs"
   - "quarter past 3" (15:15), "half past 5" (17:30), "10 to 8" (19:50)
   - "o'clock", "sharp", "en punto", "exacto"

4. FECHAS ACADÉMICAS Y PROFESIONALES:
   - "FECHA DE ENTREGA: 5 OCTUBRE 2025", "DUE DATE: Oct 15"
   - "para el 15/10/2025", "el 25 de diciembre", "25-10-2025", "2025-10-25"
   - "antes del 30 de noviembre", "deadline: Nov 30", "cutoff: Friday"
   - "submission by Monday", "hand in before Tuesday"
   - "hasta el fin de mes", "end of month", "EOM", "Q1", "H1"

5. EXPRESIONES VAGAS PERO CONTEXTUALES:
   - "pronto" (en 1 hora), "más tarde" (en 2-3 horas), "después" (en 1-2 horas)
   - "luego" (en 30-60 min), "soon" (en 1 hora), "later" (en 2 horas)
   - "eventually" (en 1 día), "cuando pueda" (mañana 10:00)
   - "si tengo tiempo" (fin de semana), "algún día de estos" (en 3 días)
   - "esta semana" (próximo día laboral), "este mes" (próximo lunes)

6. FORMATOS DE FECHA MÚLTIPLES:
   - DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, MM/DD/YYYY, YYYY-MM-DD, YYYY/MM/DD
   - "Oct 15", "15 Oct", "October 15th", "15th of October", "15 de octubre"
   - "Q1 2025" (marzo 31), "H1 2025" (junio 30), "EOY" (diciembre 31)
   - "primer semestre", "segundo trimestre", "fin de año"

7. RANGOS Y PERÍODOS COMPLEJOS:
   - "entre las 2 y 3" (14:00), "de 9 a 11" (09:00), "from 2 to 4" (14:00)
   - "desde el lunes hasta el viernes" (lunes 09:00)
   - "toda esta semana" (lunes actual), "todo el mes" (día 1 del mes siguiente)
   - "durante el verano", "en invierno", "época de exámenes"

8. EVENTOS RECURRENTES Y FRECUENCIA:
   - "todos los lunes" (próximo lunes), "cada viernes" (próximo viernes)
   - "diariamente" (mañana misma hora), "semanalmente" (próxima semana)
   - "mensualmente" (próximo mes), "anualmente" (próximo año)
   - "every Monday", "daily", "weekly", "monthly"

9. EXPRESIONES ACADÉMICAS ESPECÍFICAS:
   - "mitad del semestre", "final de cuatrimestre", "inicio de clases"
   - "período de exámenes", "semana de pruebas", "vacaciones"
   - "inscripciones", "matrícula", "titulación", "graduación"
   - "semestre de otoño", "trimestre de primavera"

10. CONTEXTOS PROFESIONALES:
    - "fin de trimestre fiscal", "cierre contable", "audit time"
    - "revisión anual", "performance review", "appraisal"
    - "sprint review", "daily standup", "retrospective"
    - "release date", "go-live", "deployment", "launch"

11. DÍAS FESTIVOS Y ESPECIALES (CHILE):
    - "Fiestas Patrias" (18 septiembre), "Año Nuevo" (1 enero)
    - "Día del Trabajador" (1 mayo), "Navidad" (25 diciembre)
    - "Semana Santa" (abril variable), "día libre" (próximo feriado)
    - "Halloween" (31 octubre), "San Valentín" (14 febrero)

12. EXPRESIONES MÉDICAS Y PERSONALES:
    - "cada 8 horas" (medicamentos), "en ayunas" (mañana temprano)
    - "después de comer" (+1 hora de comida), "antes de dormir" (22:00)
    - "control mensual", "cita médica", "chequeo anual"

MESES EN ESPAÑOL Y ABREVIACIONES:
ENERO/ENE/JAN=01, FEBRERO/FEB=02, MARZO/MAR=03, ABRIL/ABR/APR=04, 
MAYO/MAY=05, JUNIO/JUN=06, JULIO/JUL=07, AGOSTO/AGO/AUG=08, 
SEPTIEMBRE/SEP/SEPT=09, OCTUBRE/OCT=10, NOVIEMBRE/NOV=11, DICIEMBRE/DIC/DEC=12

DÍAS DE LA SEMANA Y ABREVIACIONES:
LUNES/LUN/MON=Monday, MARTES/MAR/TUE=Tuesday, MIÉRCOLES/MIE/WED=Wednesday, 
JUEVES/JUE/THU=Thursday, VIERNES/VIE/FRI=Friday, SÁBADO/SAB/SAT=Saturday, 
DOMINGO/DOM/SUN=Sunday

REGLAS SÚPER ESPECÍFICAS:
1. Responde SOLO con la fecha en formato: YYYY-MM-DDTHH:MM:SSZ
2. Horarios lógicos por defecto ULTRA ESPECÍFICOS:
   - Trabajo/oficina/estudio/clases: 09:00
   - Entregas/deadlines académicos: 23:59
   - Llamadas/contacto/reuniones: 10:00
   - Ejercicio/gym/deporte: 07:00 (mañana) o 18:00 (tarde)
   - Compras/trámites/banco/supermercado: 10:00
   - Médico/dentista/consultas médicas: 10:00
   - Comidas: 08:00 (desayuno), 13:00 (almuerzo), 20:00 (cena)
   - Medicamentos: 08:00, 14:00, 20:00 (cada 8 horas)
   - Limpieza/casa/arreglos: 10:00 (días laborales), 14:00 (fin de semana)
   - Entretenimiento/social/fiestas: 19:00
   - Estudiar/leer/tareas: 16:00 (después del trabajo/clases)
   - Videoconferencias/calls: 15:00
   - Presentaciones/exposiciones: 11:00
   - Exámenes/pruebas: 09:00
   - Proyectos/informes: 16:00
   - Cumpleaños/celebraciones: 19:00
3. Siempre elige fechas FUTURAS (nunca en el pasado)
4. Para rangos, usa la fecha/hora de inicio o más temprana
5. Si la expresión es ambigua, usa el contexto más probable
6. Para expresiones inmediatas ("al tiro", "ya", "now"), usa +30 segundos
7. Si no puedes interpretar claramente, responde: ERROR

EJEMPLOS EXTREMOS Y SÚPER COMPLEJOS:
Usuario: "recuérdame en 5 segundos ir a dormir" → {(current_time + timedelta(seconds=5)).strftime('%Y-%m-%dT%H:%M:%SZ')}
Usuario: "mañana a las 8 ir al gym" → {(current_time + timedelta(days=1)).replace(hour=8, minute=0, second=0).strftime('%Y-%m-%dT%H:%M:%SZ')}
Usuario: "el viernes llamar a mamá" → [próximo viernes a las 10:00]
Usuario: "esta tarde revisar email" → [hoy a las 15:00]
Usuario: "en 2 horas y media estudiar" → {(current_time + timedelta(hours=2, minutes=30)).strftime('%Y-%m-%dT%H:%M:%SZ')}
Usuario: "pasado mañana hacer compras" → [dentro de 2 días a las 10:00]
Usuario: "al tiro comprar pan" → [en 30 segundos]
Usuario: "lueguito llamar al jefe" → [en 45 minutos a las XX:XX]
Usuario: "en la once tomar té" → [hoy a las 17:00]
Usuario: "quarter past 3 meeting" → [hoy a las 15:15]
Usuario: "deadline Oct 15th" → [15 octubre a las 23:59]
Usuario: "every monday standup" → [próximo lunes a las 10:00]
Usuario: "end of month report" → [último día del mes a las 23:59]
Usuario: "Q1 review meeting" → [31 marzo a las 09:00]
Usuario: "cumple de María 15 nov" → [15 noviembre a las 19:00]
Usuario: "between 2 and 3 pm call" → [hoy a las 14:00]
Usuario: "tempranito ejercitar" → [mañana a las 07:00]
Usuario: "cuando pueda arreglar esto" → [mañana a las 10:00]
Usuario: "fin de semana limpiar casa" → [sábado a las 14:00]
Usuario: "toda esta semana estudiar" → [lunes actual a las 16:00]
Usuario: "after lunch take pills" → [hoy a las 14:00]
Usuario: "first thing tomorrow morning" → [mañana a las 08:00]
Usuario: "end of business day Friday" → [viernes a las 18:00]
Usuario: "sometime next week" → [lunes próxima semana a las 09:00]
Usuario: "before the weekend" → [viernes a las 17:00]
Usuario: "early next month" → [día 3 del próximo mes a las 09:00]"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Expresión temporal: '{user_input}'"}
        ]
        
        try:
            result = await self._make_api_call(messages, temperature=0.3)
            
            if not result or result.strip() == "ERROR":
                logger.warning(f"⚠️ IA no pudo interpretar: {user_input}")
                return None
            
            # Parsear respuesta ISO8601
            result = result.strip()
            if result.endswith('Z'):
                parsed_time = datetime.fromisoformat(result[:-1])  # Remover Z
                logger.info(f"🤖 IA interpretó: {user_input} -> {parsed_time}")
                return parsed_time
            else:
                logger.error(f"❌ Formato inválido de IA: {result}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error interpretando tiempo con IA: {e}")
            return None
    
    async def parse_multiple_reminders(self, user_input: str, current_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Interpretar múltiples recordatorios en un solo mensaje
        
        Args:
            user_input: Texto del usuario con múltiples fechas y eventos
            current_time: Tiempo actual
        
        Returns:
            Lista de diccionarios con 'text' y 'date' para cada recordatorio
        """
        if current_time is None:
            chile_tz = pytz.timezone('America/Santiago')
            current_time = datetime.now(chile_tz).astimezone(pytz.UTC).replace(tzinfo=None)
        
        system_prompt = f"""Eres un experto en extraer múltiples recordatorios de un texto complejo.

Fecha y hora actual: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}

Tu tarea: Extraer cada recordatorio del texto del usuario y convertir las fechas a formato ISO8601 UTC.

CASOS QUE DEBES MANEJAR:
1. Fechas en español: "5 OCTUBRE 2025", "26 DE OCTUBRE 2025"
2. Formatos DD/MM/YYYY: "12/09/2025"
3. Texto descriptivo: "40% RA1-2-3: Informe Caso", "FECHA DE ENTREGA:"
4. Rangos de fechas: "A PARTIR DEL 10", "del 11 al 15"
5. Mayúsculas/minúsculas mezcladas
6. Códigos y porcentajes mezclados con texto

MESES EN ESPAÑOL:
ENERO=01, FEBRERO=02, MARZO=03, ABRIL=04, MAYO=05, JUNIO=06,
JULIO=07, AGOSTO=08, SEPTIEMBRE=09, OCTUBRE=10, NOVIEMBRE=11, DICIEMBRE=12

Formato de respuesta (JSON):
[
  {{"text": "descripción limpia del evento", "date": "YYYY-MM-DDTHH:MM:SSZ"}},
  {{"text": "otro evento", "date": "YYYY-MM-DDTHH:MM:SSZ"}}
]

Reglas:
1. Cada línea/párrafo puede contener uno o más recordatorios
2. Extrae la fecha más específica de cada línea
3. Para rangos de fechas, usa la fecha de inicio
4. Si no hay hora específica, usa 09:00 para entregas generales, 23:59 para fechas límite
5. **LIMPIA EL TEXTO**: elimina porcentajes, códigos, palabras innecesarias
6. **USA TÍTULOS CORTOS**: máximo 25 caracteres
7. Para evaluaciones: "Examen [materia]"
8. Para informes: "Informe [tema]"
9. Para presentaciones: "Presentación [tema]"
10. Si hay "FECHA DE ENTREGA" o similar, usa esa fecha
11. Si no puedes interpretar alguna fecha, omite ese recordatorio
12. Responde SOLO el JSON válido

Ejemplos:
Entrada: "40% RA1-2-3: Informe Caso Logística. FECHA DE ENTREGA: 5 OCTUBRE 2025"
Salida: [{{"text": "Examen Logística", "date": "2025-10-05T23:59:00Z"}}]

Entrada: "30% RA2: ejercicios + Informe Gestión. FECHA: 26 DE OCTUBRE 2025"
Salida: [{{"text": "Examen Gestión", "date": "2025-10-26T23:59:00Z"}}]

Entrada: "Presentación empresa productiva. FECHA: 10 NOVIEMBRE 2025"
Salida: [{{"text": "Presentación", "date": "2025-11-10T09:00:00Z"}}]"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Texto con múltiples recordatorios:\n{user_input}"}
        ]
        
        try:
            result = await self._make_api_call(messages, temperature=0.2)
            
            if not result:
                logger.warning(f"⚠️ IA no devolvió resultado para múltiples recordatorios")
                return []
            
            # Limpiar respuesta para obtener solo el JSON
            result = result.strip()
            if result.startswith('```json'):
                result = result[7:-3].strip()
            elif result.startswith('```'):
                result = result[3:-3].strip()
            
            # Parsear JSON
            reminders = json.loads(result)
            
            # Validar y convertir fechas
            valid_reminders = []
            for reminder in reminders:
                try:
                    if 'text' in reminder and 'date' in reminder:
                        date_str = reminder['date']
                        if date_str.endswith('Z'):
                            parsed_date = datetime.fromisoformat(date_str[:-1])
                            valid_reminders.append({
                                'text': reminder['text'],
                                'date': parsed_date
                            })
                except Exception as e:
                    logger.warning(f"⚠️ Error parseando recordatorio individual: {e}")
                    continue
            
            logger.info(f"🎯 Múltiples recordatorios extraídos: {len(valid_reminders)} válidos")
            return valid_reminders
            
        except Exception as e:
            logger.error(f"❌ Error parseando múltiples recordatorios: {e}")
            return []
    
    async def enhance_reminder_text(self, user_input: str, context: Optional[List[str]] = None) -> str:
        """
        Mejorar texto de recordatorio con contexto
        
        Args:
            user_input: Input original del usuario
            context: Contexto previo del usuario
        
        Returns:
            Texto mejorado del recordatorio
        """
        context_text = ""
        if context and len(context) > 0:
            context_text = f"\n\nContexto previo del usuario:\n" + "\n".join(context[-3:])
        
        system_prompt = f"""Mejora el texto del recordatorio para que sea más claro y específico.

Tu tarea: Crear un recordatorio claro y específico basado en el input del usuario.

REGLAS IMPORTANTES:
1. Mantén la esencia del mensaje original
2. Hazlo más específico y accionable
3. USA TÍTULOS CORTOS Y DIRECTOS (máximo 30 caracteres)
4. Para evaluaciones/exámenes, usa solo "Examen [número]" o "Evaluación [tipo]"
5. Para informes, usa solo "Informe [materia]"
6. Para presentaciones, usa solo "Presentación [tema]"
7. NO uses "Recordatorio:" al inicio
8. NO agregues texto descriptivo extra
9. NO cambies fechas ni horas mencionadas

Ejemplos:
Input: "40% RA1-2-3: Informe Caso Logística Completo"
Output: "Examen Logística"

Input: "Evaluación certificación Hubspot"
Output: "Examen Hubspot"

Input: "Presentación empresa productiva"
Output: "Presentación Empresa"

Input: "recordar comprar leche"
Output: "Comprar leche"

Input: "reunión con juan"
Output: "Reunión Juan"

Input: "enviar reporte marketing"
Output: "Reporte Marketing"{context_text}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Mejorar recordatorio: '{user_input}'"}
        ]
        
        try:
            result = await self._make_api_call(messages, temperature=0.4)
            
            if result and len(result.strip()) > 0:
                enhanced = result.strip()
                logger.info(f"✨ Recordatorio mejorado: '{user_input}' -> '{enhanced}'")
                return enhanced
            else:
                return f"Recordatorio: {user_input}"
                
        except Exception as e:
            logger.error(f"❌ Error mejorando texto: {e}")
            return f"Recordatorio: {user_input}"
    
    async def generate_weekly_summary(self, user_name: str, reminders: List[Dict], notes: List[Dict]) -> str:
        """
        Generar resumen semanal inteligente
        
        Args:
            user_name: Nombre del usuario
            reminders: Lista de recordatorios de la semana
            notes: Lista de notas de la semana
        
        Returns:
            Resumen markdown formateado
        """
        # Preparar datos para IA
        reminders_text = ""
        if reminders:
            reminders_text = "RECORDATORIOS COMPLETADOS:\n"
            for reminder in reminders[-10:]:  # Últimos 10
                reminders_text += f"- {reminder.get('text', 'Sin texto')}\n"
        
        notes_text = ""
        if notes:
            notes_text = "\nNOTAS GUARDADAS:\n"
            for note in notes[-10:]:  # Últimas 10
                notes_text += f"- {note.get('text', 'Sin texto')}\n"
        
        system_prompt = f"""Crea un resumen semanal personalizado y motivador para {user_name}.

DATOS DE LA SEMANA:
{reminders_text}
{notes_text}

Tu tarea: Crear un resumen en markdown que sea:
1. Personal y motivador
2. Destaque logros y patrones
3. Sugiera mejoras constructivas
4. Use emojis apropiados
5. Máximo 300 palabras

Estructura:
## Resumen de la semana

¡Hola {user_name}! 👋

[Análisis de logros y actividades]

### 📊 Números de la semana
- **Recordatorios**: [cantidad] completados
- **Notas**: [cantidad] guardadas

### 💡 Insights
[Patrones identificados y sugerencias]

¡Sigue así! 💪"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Genera el resumen semanal"}
        ]
        
        try:
            result = await self._make_api_call(messages, temperature=0.6)
            
            if result and len(result.strip()) > 0:
                logger.info(f"📈 Resumen semanal generado para {user_name}")
                return result.strip()
            else:
                return f"## Resumen de la semana\n\n¡Hola {user_name}! 👋\n\nEsta semana tuviste **{len(reminders)} recordatorios** y guardaste **{len(notes)} notas**.\n\n¡Sigue así! 💪"
                
        except Exception as e:
            logger.error(f"❌ Error generando resumen: {e}")
            return f"## Resumen de la semana\n\n¡Hola {user_name}! 👋\n\nEsta semana tuviste **{len(reminders)} recordatorios** y guardaste **{len(notes)} notas**.\n\n¡Sigue así! 💪"
    
    async def search_notes_semantically(self, query: str, notes: List[Dict]) -> List[Dict]:
        """
        Búsqueda semántica de notas usando IA
        
        Args:
            query: Consulta del usuario
            notes: Lista de notas disponibles
        
        Returns:
            Lista ordenada de notas relevantes
        """
        if not notes:
            return []
        
        # Preparar notas para análisis
        notes_text = ""
        for i, note in enumerate(notes):
            notes_text += f"{i}: {note.get('text', 'Sin texto')}\n"
        
        system_prompt = f"""Busca las notas más relevantes para la consulta del usuario.

NOTAS DISPONIBLES:
{notes_text}

Instrucciones:
1. Analiza semánticamente la consulta vs las notas
2. Responde SOLO con los números de las notas más relevantes
3. Ordena por relevancia (más relevante primero)
4. Máximo 5 resultados
5. Si no hay coincidencias, responde: NONE

Formato: 3,7,1,9,2"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Buscar: '{query}'"}
        ]
        
        try:
            result = await self._make_api_call(messages, temperature=0.3)
            
            if not result or result.strip() == "NONE":
                return []
            
            # Parsear índices
            indices = [int(x.strip()) for x in result.strip().split(',') if x.strip().isdigit()]
            
            # Retornar notas ordenadas por relevancia
            relevant_notes = []
            for idx in indices:
                if 0 <= idx < len(notes):
                    relevant_notes.append(notes[idx])
            
            logger.info(f"🔍 Búsqueda semántica: '{query}' -> {len(relevant_notes)} resultados")
            return relevant_notes
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda semántica: {e}")
            # Fallback a búsqueda simple
            query_lower = query.lower()
            simple_results = [
                note for note in notes 
                if query_lower in note.get('text', '').lower()
            ]
            return simple_results[:5]