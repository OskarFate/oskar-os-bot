"""
Interfaz principal del bot de Telegram con aiogram
"""

import asyncio
import re
from datetime import datetime
from typing import Optional
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, BotCommand
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from database.connection import DatabaseManager
from bot.ai_interpreter import AIInterpreter
from bot.reminder_manager import ReminderManager
from bot.note_manager import NoteManager
from bot.memory_index import MemoryIndex
from config.settings import settings
from utils.helpers import (
    format_reminders_list, 
    sanitize_input, 
    validate_telegram_user_id,
    truncate_text,
    format_datetime_for_user
)


class TelegramBot:
    """Bot principal de Telegram"""
    
    def __init__(self, token: str, db_manager: DatabaseManager, openrouter_api_key: str):
        self.token = token
        self.db = db_manager
        
        # Inicializar bot y dispatcher
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        
        # Inicializar componentes
        self.ai_interpreter = AIInterpreter(openrouter_api_key)
        self.reminder_manager = ReminderManager(db_manager)
        self.note_manager = NoteManager(db_manager, self.ai_interpreter)
        self.memory_index = MemoryIndex(db_manager)
        
        # Registrar handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Registrar manejadores de comandos y mensajes"""
        
        # Comandos
        self.dp.message.register(self._cmd_start, CommandStart())
        self.dp.message.register(self._cmd_recordar, Command("recordar"))
        self.dp.message.register(self._cmd_nota, Command("nota"))
        self.dp.message.register(self._cmd_listar, Command("listar"))
        self.dp.message.register(self._cmd_buscar, Command("buscar"))
        self.dp.message.register(self._cmd_resumen, Command("resumen"))
        self.dp.message.register(self._cmd_calendar, Command("calendar"))
        self.dp.message.register(self._cmd_status, Command("status"))
        self.dp.message.register(self._cmd_help, Command("help", "ayuda"))
        
        # Mensajes de texto general
        self.dp.message.register(self._handle_text_message)
    
    async def start(self):
        """Iniciar el bot"""
        try:
            # Configurar comandos del bot
            await self._set_bot_commands()
            
            # Obtener información del bot
            bot_info = await self.bot.get_me()
            logger.info(f"🤖 Bot iniciado: @{bot_info.username}")
            
            # Iniciar polling
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.error(f"❌ Error iniciando bot: {e}")
            raise
    
    async def _set_bot_commands(self):
        """Configurar comandos del bot para el menú"""
        commands = [
            BotCommand(command="start", description="🤖 Inicializar bot"),
            BotCommand(command="recordar", description="⏰ Crear recordatorio"),
            BotCommand(command="nota", description="📝 Guardar nota"),
            BotCommand(command="listar", description="📋 Ver recordatorios"),
            BotCommand(command="buscar", description="🔍 Buscar notas"),
            BotCommand(command="resumen", description="📊 Resumen semanal"),
            BotCommand(command="calendar", description="🍎 Estado Apple Calendar"),
            BotCommand(command="status", description="⚙️ Estado del sistema"),
            BotCommand(command="help", description="❓ Ayuda"),
        ]
        
        await self.bot.set_my_commands(commands)
        logger.info("📋 Comandos del bot configurados")
    
    async def _register_user(self, user: types.User) -> bool:
        """Registrar o actualizar usuario en base de datos"""
        try:
            if not validate_telegram_user_id(user.id):
                logger.error(f"❌ ID de usuario inválido: {user.id}")
                return False
            
            user_data = {
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "language": user.language_code or "es",
                "timezone": settings.DEFAULT_TIMEZONE,
                "last_activity": datetime.utcnow(),
                "is_active": True
            }
            
            success = await self.db.add_user(user_data)
            
            if success:
                logger.info(f"👤 Usuario registrado/actualizado: {user.id} (@{user.username})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error registrando usuario: {e}")
            return False
    
    # --- COMANDOS ---
    
    async def _cmd_start(self, message: Message):
        """Comando /start - Bienvenida"""
        try:
            await self._register_user(message.from_user)
            
            welcome_text = """🧠 **¡Bienvenido a OskarOS Assistant Bot!**

Soy tu segundo cerebro personal con IA. Puedo ayudarte con:

⏰ **Recordatorios inteligentes**
- Interpreto lenguaje natural: "recuérdame en 3 horas"
- Pre-alertas automáticas (7d, 2d, 1d antes)

📝 **Notas semánticas**
- Clasificación automática por tema y prioridad
- Búsqueda inteligente

📊 **Resúmenes con IA**
- Análisis semanal de tu productividad

**Comandos principales:**
/recordar - Crear recordatorio
/nota - Guardar nota  
/listar - Ver recordatorios pendientes
/buscar - Buscar en tus notas
/resumen - Resumen semanal
/status - Estado del sistema

**¿Cómo empezar?**
Simplemente escribe algo como:
• "Recuérdame llamar al médico mañana a las 9"
• "/nota Idea: crear app de productividad"

¡Empecemos! 🚀"""

            await message.answer(welcome_text, parse_mode="Markdown")
            
            # Agregar contexto de bienvenida
            await self.memory_index.add_context(
                message.from_user.id,
                "Usuario nuevo, mostró mensaje de bienvenida",
                "bot_interaction"
            )
            
        except Exception as e:
            logger.error(f"❌ Error en comando start: {e}")
            await message.answer("❌ Error iniciando el bot. Intenta de nuevo.")
    
    async def _cmd_recordar(self, message: Message):
        """Comando /recordar - Crear recordatorio"""
        try:
            await self._register_user(message.from_user)
            
            # Extraer texto del comando
            command_text = message.text
            if not command_text or len(command_text.split()) < 2:
                await message.answer(
                    "⏰ **Crear recordatorio**\n\n"
                    "Uso: `/recordar <descripción con tiempo>`\n\n"
                    "Ejemplos:\n"
                    "• `/recordar llamar al médico mañana a las 9`\n"
                    "• `/recordar entregar proyecto en 3 días`\n"
                    "• `/recordar reunión el 25 de octubre a las 15:00`",
                    parse_mode="Markdown"
                )
                return
            
            # Remover comando y obtener contenido
            reminder_input = command_text[9:].strip()  # Remover "/recordar "
            
            await self._process_reminder_request(message, reminder_input)
            
        except Exception as e:
            logger.error(f"❌ Error en comando recordar: {e}")
            await message.answer("❌ Error creando recordatorio. Intenta de nuevo.")
    
    async def _cmd_nota(self, message: Message):
        """Comando /nota - Guardar nota"""
        try:
            await self._register_user(message.from_user)
            
            # Extraer texto del comando
            command_text = message.text
            if not command_text or len(command_text.split()) < 2:
                await message.answer(
                    "📝 **Guardar nota**\n\n"
                    "Uso: `/nota <contenido>`\n\n"
                    "Ejemplos:\n"
                    "• `/nota Idea: crear app de productividad`\n"
                    "• `/nota Recordar comprar leche y pan`\n"
                    "• `/nota Reflexión sobre la reunión de hoy`",
                    parse_mode="Markdown"
                )
                return
            
            # Remover comando y obtener contenido
            note_text = command_text[6:].strip()  # Remover "/nota "
            note_text = sanitize_input(note_text)
            
            if not note_text:
                await message.answer("❌ El contenido de la nota no puede estar vacío.")
                return
            
            # Guardar nota
            success = await self.note_manager.create_note(
                user_id=message.from_user.id,
                note_text=note_text,
                auto_classify=True
            )
            
            if success:
                await message.answer(
                    f"✅ **Nota guardada**\n\n📝 {note_text[:100]}{'...' if len(note_text) > 100 else ''}",
                    parse_mode="Markdown"
                )
                
                # Agregar contexto
                await self.memory_index.add_context(
                    message.from_user.id,
                    f"Guardó nota sobre: {note_text[:50]}",
                    "note_creation"
                )
            else:
                await message.answer("❌ Error guardando la nota. Intenta de nuevo.")
                
        except Exception as e:
            logger.error(f"❌ Error en comando nota: {e}")
            await message.answer("❌ Error guardando nota. Intenta de nuevo.")
    
    async def _cmd_listar(self, message: Message):
        """Comando /listar - Mostrar recordatorios pendientes"""
        try:
            await self._register_user(message.from_user)
            
            # Limpiar recordatorios pasados automáticamente
            cleaned_count = await self.reminder_manager.cleanup_past_reminders(message.from_user.id)
            
            # Obtener recordatorios pendientes (solo futuros)
            reminders = await self.reminder_manager.get_pending_reminders_for_user(
                message.from_user.id,
                limit=10
            )
            
            if not reminders:
                cleanup_msg = f"\n\n🧹 Se limpiaron {cleaned_count} recordatorios pasados." if cleaned_count > 0 else ""
                await message.answer(
                    f"📭 **No tienes recordatorios pendientes**\n\n"
                    f"¡Perfecto! Tu agenda está limpia.{cleanup_msg}\n\n"
                    "Usa `/recordar` para crear nuevos recordatorios.",
                    parse_mode="Markdown"
                )
                return
            
            # Formatear lista
            message_text = "📋 **Tus próximos recordatorios:**\n\n"
            
            for i, reminder in enumerate(reminders, 1):
                date_str = format_datetime_for_user(reminder.date)
                text = reminder.text[:60] + "..." if len(reminder.text) > 60 else reminder.text
                
                message_text += f"{i}. 📅 {date_str}\n"
                message_text += f"   📝 {text}\n\n"
            
            # Truncar si es muy largo
            message_text = truncate_text(message_text)
            
            await message.answer(message_text, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"❌ Error en comando listar: {e}")
            await message.answer("❌ Error obteniendo recordatorios. Intenta de nuevo.")
    
    async def _cmd_buscar(self, message: Message):
        """Comando /buscar - Buscar notas"""
        try:
            await self._register_user(message.from_user)
            
            # Extraer término de búsqueda
            command_text = message.text
            if not command_text or len(command_text.split()) < 2:
                await message.answer(
                    "🔍 **Buscar en tus notas**\n\n"
                    "Uso: `/buscar <término>`\n\n"
                    "Ejemplos:\n"
                    "• `/buscar trabajo`\n"
                    "• `/buscar ideas de proyecto`\n"
                    "• `/buscar reunión`",
                    parse_mode="Markdown"
                )
                return
            
            # Remover comando y obtener término
            search_query = command_text[8:].strip()  # Remover "/buscar "
            search_query = sanitize_input(search_query)
            
            if not search_query:
                await message.answer("❌ El término de búsqueda no puede estar vacío.")
                return
            
            # Buscar notas
            notes = await self.note_manager.search_notes(
                user_id=message.from_user.id,
                query=search_query,
                use_ai_search=True,
                limit=8
            )
            
            if not notes:
                await message.answer(
                    f"🔍 **Sin resultados para '{search_query}'**\n\n"
                    "No encontré notas que coincidan.\n\n"
                    "Intenta con otros términos o usa `/nota` para crear nuevas notas.",
                    parse_mode="Markdown"
                )
                return
            
            # Formatear resultados
            message_text = f"🔍 **Resultados para '{search_query}':**\n\n"
            
            for i, note in enumerate(notes, 1):
                note_preview = note.text[:80] + "..." if len(note.text) > 80 else note.text
                date_str = note.created_at.strftime("%d/%m")
                
                message_text += f"{i}. 📝 {note_preview}\n"
                message_text += f"   📅 {date_str}"
                
                if note.tags:
                    tags_str = ", ".join(note.tags[:3])
                    message_text += f" | 🏷️ {tags_str}"
                
                message_text += "\n\n"
            
            # Truncar si es muy largo
            message_text = truncate_text(message_text)
            
            await message.answer(message_text, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"❌ Error en comando buscar: {e}")
            await message.answer("❌ Error buscando notas. Intenta de nuevo.")
    
    async def _cmd_resumen(self, message: Message):
        """Comando /resumen - Generar resumen semanal"""
        try:
            await self._register_user(message.from_user)
            
            # Mostrar mensaje de procesamiento
            processing_msg = await message.answer("📊 Generando tu resumen semanal con IA...")
            
            # Obtener datos de la semana
            reminders_summary = await self.reminder_manager.get_weekly_reminder_summary(
                message.from_user.id
            )
            notes_summary = await self.note_manager.get_weekly_notes_summary(
                message.from_user.id
            )
            
            # Generar resumen con IA
            user_name = message.from_user.first_name or "Usuario"
            summary = await self.ai_interpreter.generate_weekly_summary(
                reminders=reminders_summary.get("reminders", []),
                notes=notes_summary.get("notes", []),
                user_name=user_name
            )
            
            # Agregar estadísticas
            stats_text = f"\n\n📊 **Estadísticas de la semana:**\n"
            stats_text += f"⏰ Recordatorios: {reminders_summary['total']}\n"
            stats_text += f"📝 Notas: {notes_summary['total']}\n"
            
            full_summary = summary + stats_text
            
            # Editar mensaje de procesamiento
            await processing_msg.edit_text(
                truncate_text(full_summary),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"❌ Error en comando resumen: {e}")
            await message.answer("❌ Error generando resumen. Intenta de nuevo.")
    
    async def _cmd_calendar(self, message: Message):
        """Comando /calendar - Estado de Apple Calendar"""
        try:
            await self._register_user(message.from_user)
            
            # Importar aquí para evitar ciclos
            from bot.calendar_integration import apple_calendar
            
            if not apple_calendar:
                await message.answer(
                    "❌ **Apple Calendar no configurado**\n\n"
                    "La integración con Apple Calendar no está disponible.\n"
                    "Los recordatorios se crean solo en el bot.",
                    parse_mode="Markdown"
                )
                return
            
            # Probar conexión
            processing_msg = await message.answer("🔄 Verificando conexión con Apple Calendar...")
            
            try:
                calendar_info = await apple_calendar.test_connection()
                
                if calendar_info.get("success", False):
                    status_text = f"""🍎 **Apple Calendar - Estado**

✅ **Conectado exitosamente**

📧 **Email:** {calendar_info.get('email', 'N/A')}
📅 **Calendario:** {calendar_info.get('calendar_name', 'N/A')}
🌐 **Servidor:** {calendar_info.get('server', 'N/A')}
📊 **Eventos:** {calendar_info.get('events_count', 'N/A')}

🎯 **Funcionalidad:**
• Los recordatorios se crean automáticamente en tu calendario
• Duración inteligente según el tipo de evento
• Sincronización con todos tus dispositivos Apple

💡 **Próximo recordatorio se sincronizará automáticamente**"""
                else:
                    error_msg = calendar_info.get('error', 'Error desconocido')
                    status_text = f"""❌ **Error en Apple Calendar**

🔴 **No conectado**

⚠️ **Error:** {error_msg}

💡 **Posibles soluciones:**
• Verificar credenciales de iCloud
• Comprobar contraseña de aplicación
• Revisar conexión a internet

📝 **Los recordatorios se siguen creando en el bot**"""
                
                await processing_msg.edit_text(status_text, parse_mode="Markdown")
                
            except Exception as e:
                await processing_msg.edit_text(
                    f"❌ **Error verificando Apple Calendar**\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Los recordatorios funcionan normalmente en el bot.",
                    parse_mode="Markdown"
                )
                
        except Exception as e:
            logger.error(f"❌ Error en comando calendar: {e}")
            await message.answer("❌ Error verificando estado del calendario.")

    async def _cmd_status(self, message: Message):
        """Comando /status - Estado del sistema"""
        try:
            await self._register_user(message.from_user)
            
            # Información básica
            uptime = datetime.utcnow()
            
            status_text = f"""ℹ️ **Estado del Sistema**

🤖 **Bot:** Activo
🗄️ **Base de datos:** Conectada
🧠 **IA:** OpenRouter (Llama 3.3)
⏰ **Scheduler:** Activo

📊 **Información:**
• Verificación: cada {settings.SCHEDULER_INTERVAL_SECONDS}s
• Zona horaria: {settings.DEFAULT_TIMEZONE}
• Versión: 1.0.0

⚡ **Tu actividad:**
• Usuario ID: `{message.from_user.id}`
• Última consulta: {uptime.strftime('%H:%M:%S UTC')}

🔗 **APIs:**
• Telegram: ✅ Conectado
• OpenRouter: ✅ Conectado  
• MongoDB: ✅ Conectado"""

            await message.answer(status_text, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"❌ Error en comando status: {e}")
            await message.answer("❌ Error obteniendo estado del sistema.")
    
    async def _cmd_help(self, message: Message):
        """Comando /help - Ayuda"""
        try:
            help_text = """❓ **Ayuda - OskarOS Assistant Bot**

🧠 **¿Qué puedo hacer?**
Soy tu asistente personal con IA para recordatorios y notas.

⏰ **Recordatorios simples:**
• `/recordar llamar médico mañana 9am`
• "Recuérdame entregar proyecto en 3 días"
• "mañana a las 8 ir al gym"

🔄 **Recordatorios recurrentes (¡NUEVO!):**
• "tomar pastilla todos los días a las 8"
• "ejercitar todos los lunes"
• "reunión cada semana"
• "día por medio revisar email"
• "medicamento cada 8 horas"
• "backup cada mes"
• "llamar mamá todos los domingos"

� **Apple Calendar (¡INTEGRADO!):**
• Los recordatorios se crean automáticamente en tu calendario
• Sincronización con iPhone, iPad, Mac
• `/calendar` - Ver estado de la integración
• Duración inteligente según el tipo de evento

�📝 **Notas:**
• `/nota Idea: crear app productividad`
• `/buscar trabajo` - Buscar notas
• Clasificación automática por IA

📊 **Análisis:**
• `/listar` - Ver próximos recordatorios
• `/resumen` - Resumen semanal con IA
• `/status` - Estado del sistema

🔥 **Características únicas:**
• Interpreto lenguaje natural y modismos chilenos
• Recordatorios recurrentes automáticos
• Pre-recordatorios (7d, 2d, 1d)
• Búsqueda semántica inteligente
• Aprendo tus patrones y preferencias
• Integración completa con Apple Calendar

🇨🇱 **Lenguaje chileno:**
• "al tiro comprar pan"
• "lueguito llamar jefe"
• "tempranito ejercitar"

💡 **Ejemplos prácticos:**
1. "Recuérdame ir al gym en 2 horas"
2. "pastillas todos los días 8am"
3. "examen el 5 de noviembre" → ¡Se crea en tu calendario!
4. "/nota Reflexión: el proyecto va bien"
5. "/buscar ideas de vacaciones"
6. "/resumen" para ver tu semana

¿Necesitas algo específico? ¡Solo pregúntame! 😊"""

            await message.answer(help_text, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"❌ Error en comando help: {e}")
            await message.answer("❌ Error mostrando ayuda.")
    
    # --- MANEJO DE MENSAJES ---
    
    async def _handle_text_message(self, message: Message):
        """Manejar mensajes de texto general"""
        try:
            await self._register_user(message.from_user)
            
            text = sanitize_input(message.text)
            
            # Detectar si es una solicitud de recordatorio
            if self._is_reminder_request(text):
                await self._process_reminder_request(message, text)
            else:
                # Mensaje general - dar sugerencia amigable
                suggestions = await self.memory_index.suggest_improvements(message.from_user.id)
                
                response = "👋 ¡Hola! Puedo ayudarte con recordatorios y notas.\n\n"
                response += "💡 **Sugerencias:**\n"
                response += "\n".join(f"• {suggestion}" for suggestion in suggestions[:2])
                response += "\n\n📋 Usa `/help` para ver todos los comandos."
                
                await message.answer(response, parse_mode="Markdown")
                
                # Guardar contexto
                await self.memory_index.add_context(
                    message.from_user.id,
                    f"Mensaje general: {text[:50]}",
                    "general_message"
                )
                
        except Exception as e:
            logger.error(f"❌ Error manejando mensaje de texto: {e}")
            await message.answer("❌ Error procesando mensaje. Usa `/help` para ver comandos disponibles.")
    
    def _is_reminder_request(self, text: str) -> bool:
        """Detectar si un texto es una solicitud de recordatorio - VERSIÓN ULTRA COMPLETA"""
        
        # Palabras clave para recordatorios en español
        reminder_keywords = [
            # Comandos directos
            "recuérdame", "recordar", "avísame", "avisar", "alerta", "alarma",
            "notifícame", "notificar", "alertar", "programar", "agendar",
            
            # Expresiones temporales básicas
            "en ", "dentro de", "después de", "antes de", "desde", "hasta",
            "mañana", "hoy", "ayer", "pasado mañana", "anteayer",
            "próxim", "siguiente", "que viene", "entrante", "venidero",
            "esta semana", "la próxima", "el otro", "la otra",
            
            # Expresiones de tiempo chilenas/coloquiales
            "al tiro", "al rato", "lueguito", "ratito", "un cachito",
            "altiro", "altoque", "yapo", "cachái", "bacán",
            "en la once", "en la mañanita", "tempranito",
            
            # Días específicos (español e inglés)
            "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
            "mon", "tue", "wed", "thu", "fri", "sat", "sun",
            
            # Meses (español e inglés)
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
            "jan", "feb", "mar", "apr", "may", "jun",
            "jul", "aug", "sep", "oct", "nov", "dec",
            
            # Palabras académicas y profesionales
            "evaluación", "examen", "prueba", "control", "test", "quiz", "certamen",
            "entrega", "tarea", "trabajo", "informe", "proyecto", "ensayo", "reporte",
            "presentación", "exposición", "defensa", "seminario", "conferencia",
            "reunión", "junta", "meeting", "call", "videoconferencia",
            "fecha", "deadline", "vencimiento", "plazo", "límite", "cutoff",
            "due date", "submission", "delivery", "handout",
            
            # Expresiones de tiempo específicas
            "a las", "al mediodía", "a medianoche", "al amanecer", "al atardecer",
            "en la mañana", "en la tarde", "en la noche", "en la madrugada",
            "por la mañana", "por la tarde", "por la noche", "por la madrugada",
            "de mañana", "de tarde", "de noche", "de madrugada",
            "am", "pm", "hrs", "horas", "minutos", "segundos", "mins", "segs",
            "h", "min", "sec", "o'clock",
            
            # Eventos y ocasiones
            "cumpleaños", "cumple", "aniversario", "graduación", "boda", "matrimonio",
            "fiesta", "celebración", "evento", "cita", "appointment", "date",
            "viaje", "vacaciones", "feriado", "holiday", "trip", "travel",
            
            # Actividades cotidianas
            "hacer", "ir", "venir", "llegar", "salir", "partir", "volver", "regresar",
            "llamar", "telefonear", "contactar", "escribir", "enviar", "mandar",
            "comprar", "pagar", "cobrar", "depositar", "transferir",
            "estudiar", "leer", "practicar", "ejercitar", "entrenar", "gym",
            "comer", "almorzar", "cenar", "desayunar", "tomar", "beber",
            "limpiar", "ordenar", "arreglar", "reparar", "revisar", "chequear",
            "trabajar", "terminar", "finalizar", "completar", "enviar",
            
            # Actividades médicas y personales
            "médico", "doctor", "dentista", "cita médica", "consulta", "control",
            "medicamento", "pastilla", "medicina", "tratamiento", "terapia",
            "ejercicio", "deporte", "correr", "caminar", "nadar", "yoga",
            "dieta", "régimen", "peso", "dormir", "despertar", "levantarse",
            
            # Expresiones de urgencia/importancia
            "urgente", "importante", "crítico", "vital", "esencial", "necesario",
            "imperdible", "fundamental", "clave", "priority", "asap", "ya",
            "emergency", "emergencia", "crisis", "problema",
            
            # Frecuencia y repetición
            "diario", "semanal", "mensual", "anual", "cada", "todos los",
            "siempre", "nunca", "a veces", "ocasional", "regular",
            "daily", "weekly", "monthly", "yearly", "every",
            
            # Expresiones vagas que podrían ser recordatorios
            "no olvides", "no te olvides", "acuérdate", "recuerda",
            "don't forget", "remember", "remind", "note", "memo",
            "tengo que", "debo", "necesito", "hay que", "toca",
            "i need to", "i have to", "i must", "should"
        ]
        
        # Patrones de fecha numérica (más completos)
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',          # DD/MM/YYYY
            r'\b\d{1,2}/\d{1,2}/\d{2}\b',          # DD/MM/YY
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',          # DD-MM-YYYY
            r'\b\d{1,2}\.\d{1,2}\.\d{4}\b',        # DD.MM.YYYY
            r'\b\d{4}/\d{1,2}/\d{1,2}\b',          # YYYY/MM/DD
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',          # YYYY-MM-DD (ISO)
            r'\b\d{1,2}:\d{2}\b',                  # HH:MM
            r'\b\d{1,2}h\d{2}\b',                  # 14h30
            r'\b\d{1,2}:\d{2}(am|pm)\b',           # 2:30pm
            r'\b\d{1,2}\s?(am|pm)\b',              # 3pm, 8 am
            r'\b\d{1,2}hs?\b',                     # 15hs, 8h
            r'\b\d{1,2}:\d{2}:\d{2}\b',            # HH:MM:SS
        ]
        
        # Patrones académicos específicos (expandidos)
        academic_patterns = [
            r'fecha de entrega',
            r'fecha limite',
            r'fecha tope',
            r'entregar el',
            r'entrega el',
            r'para el',
            r'hasta el',
            r'deadline',
            r'due date',
            r'vence el',
            r'vencimiento',
            r'antes del',
            r'submission',
            r'hand\s?in',
            r'turn\s?in',
            r'\b\d+%\s+\w+',                      # 25% RA1-2-3
            r'ra\d+-\d+-\d+',                     # RA1-2-3
            r'evaluaci[óo]n\s+\w+',               # evaluación escrita
            r'examen\s+\w+',                      # examen final
            r'prueba\s+\w+',                      # prueba parcial
            r'control\s+\w+',                     # control de lectura
            r'certamen\s+\w+',                    # certamen 1
            r'tarea\s+\d+',                       # tarea 3
            r'tp\s+\d+',                          # TP 2 (trabajo práctico)
            r'lab\s+\d+',                         # lab 4 (laboratorio)
            r'quiz\s+\d+',                        # quiz 1
        ]
        
        # Patrones de tiempo relativo (muy expandidos)
        time_relative_patterns = [
            # Tiempo específico
            r'en\s+\d+\s+(segundo|minuto|hora|día|semana|mes|año)s?',
            r'dentro\s+de\s+\d+',
            r'después\s+de\s+\d+',
            r'hace\s+\d+',
            r'en\s+\d+h\d+',                      # en 2h30
            r'en\s+\d+:\d+',                      # en 1:30
            
            # Expresiones relativas
            r'el\s+(próximo|siguiente|otro)',
            r'la\s+(próxima|siguiente|otra)',
            r'este\s+(lunes|martes|miércoles|jueves|viernes|sábado|domingo)',
            r'esta\s+(semana|tarde|mañana|noche)',
            r'next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'this\s+(week|afternoon|morning|evening)',
            
            # Expresiones chilenas
            r'el\s+otro\s+(lunes|martes|miércoles|jueves|viernes)',
            r'la\s+otra\s+semana',
            r'pasado\s+mañana',
            r'antes\s+de\s+ayer',
            r'al\s+rato',
            r'al\s+tiro',
            r'lueguito',
            
            # Expresiones vagas pero útiles
            r'pronto',
            r'más\s+tarde',
            r'después',
            r'luego',
            r'soon',
            r'later',
            r'eventually',
            
            # Rangos de tiempo
            r'entre\s+las?\s+\d+',
            r'desde\s+las?\s+\d+',
            r'hasta\s+las?\s+\d+',
            r'de\s+\d+\s+a\s+\d+',
            r'from\s+\d+\s+to\s+\d+',
            
            # PATRONES RECURRENTES (NUEVOS)
            r'cada\s+\d+\s+(minutos?|horas?|días?|semanas?|meses?)',
            r'todos?\s+los?\s+(días?|lunes|martes|miércoles|jueves|viernes|sábados?|domingos?)',
            r'todas?\s+las?\s+(mañanas?|tardes?|noches?|semanas?)',
            r'every\s+\d+\s+(minutes?|hours?|days?|weeks?|months?)',
            r'every\s+(day|monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'daily|weekly|monthly|yearly',
            r'diario|semanal|mensual|anual',
            r'día\s+por\s+medio',
            r'día\s+sí\s+día\s+no',
            r'inter\s?diario',
            r'cada\s+dos\s+días',
            r'cada\s+tercer\s+día',
            r'cada\s+otra\s+semana',
            r'cada\s+dos\s+semanas',
            r'fin\s+de\s+semana',
            r'días?\s+laborables?',
            r'días?\s+hábiles?',
            r'entre\s+semana',
            r'lunes\s+a\s+viernes',
            r'monday\s+to\s+friday',
            r'weekdays?',
            r'weekends?',
        ]
        
        # Patrones de contexto de actividad (nuevo)
        activity_patterns = [
            # Trabajo/estudio
            r'(trabajo|office|oficina|estudio|universidad|colegio)',
            r'(meeting|reunión|junta|conferencia|videoconferencia)',
            r'(proyecto|informe|reporte|presentación|tarea)',
            
            # Personal/salud
            r'(médico|doctor|dentista|cita|consulta|control)',
            r'(medicamento|pastilla|medicina|tratamiento)',
            r'(ejercicio|gym|deporte|correr|caminar)',
            
            # Finanzas
            r'(pagar|cobrar|banco|cuenta|tarjeta|transferencia)',
            r'(factura|boleta|recibo|impuesto|dividendo)',
            
            # Social/familia
            r'(cumpleaños|cumple|aniversario|fiesta|celebración)',
            r'(llamar|contactar|escribir|visitar|ver)',
            r'(mamá|papá|familia|amigo|novia|polola)',
            
            # Casa/compras
            r'(comprar|super|supermercado|tienda|mall)',
            r'(limpiar|ordenar|arreglar|reparar|mantener)',
            r'(cocinar|comer|almorzar|cenar|desayunar)',
        ]
        
        text_lower = text.lower()
        
        # 1. Verificar palabras clave de recordatorio
        has_reminder_keywords = any(keyword in text_lower for keyword in reminder_keywords)
        
        # 2. Verificar patrones de fecha numérica
        has_date_pattern = any(re.search(pattern, text_lower) for pattern in date_patterns)
        
        # 3. Verificar patrones académicos
        has_academic_pattern = any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in academic_patterns)
        
        # 4. Verificar patrones de tiempo relativo
        has_time_relative = any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in time_relative_patterns)
        
        # 5. Verificar contexto de actividad
        has_activity_context = any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in activity_patterns)
        
        # 6. Verificar si tiene estructura de recordatorio (longitud mínima y contexto)
        has_context = len(text.split()) >= 2 and len(text) > 5
        
        # 7. Detectar fechas numéricas con contexto de acción
        has_numeric_date = re.search(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', text)
        has_action_context = any(word in text_lower for word in [
            "hacer", "ir", "venir", "llamar", "revisar", "estudiar", "pagar", 
            "comprar", "trabajar", "terminar", "enviar", "completar", "ejercitar"
        ])
        
        # 8. Detectar expresiones imperativas o de planificación
        has_imperative = any(phrase in text_lower for phrase in [
            "tengo que", "debo", "necesito", "hay que", "toca", "me toca",
            "i need to", "i have to", "i must", "should", "gonna", "going to",
            "voy a", "vamos a", "plan to", "planear", "planifico"
        ])
        
        # 9. Detectar formato de lista o múltiples tareas
        has_list_format = (
            text.count('\n') > 1 or  # Múltiples líneas
            text.count('-') > 1 or   # Lista con guiones
            text.count('•') > 0 or   # Lista con bullets
            text.count('*') > 1 or   # Lista con asteriscos
            len(re.findall(r'\d+\.', text)) > 1  # Lista numerada
        )
        
        # 10. Detectar preguntas sobre tiempo (potenciales recordatorios)
        has_time_question = any(phrase in text_lower for phrase in [
            "cuándo", "when", "qué hora", "what time", "a qué hora", "at what time"
        ]) and len(text.split()) > 2
        
        # 11. NUEVO: Detectar patrones recurrentes específicos
        has_recurring_pattern = any(phrase in text_lower for phrase in [
            "todos los días", "every day", "daily", "diario", "diariamente",
            "cada día", "cada mañana", "cada tarde", "cada noche",
            "todos los lunes", "todos los martes", "todos los miércoles", 
            "todos los jueves", "todos los viernes", "todos los sábados", "todos los domingos",
            "every monday", "every tuesday", "every wednesday", "every thursday", 
            "every friday", "every saturday", "every sunday",
            "día por medio", "día sí día no", "cada dos días", "cada tercer día",
            "cada semana", "weekly", "semanal", "semanalmente",
            "cada mes", "monthly", "mensual", "mensualmente",
            "fin de semana", "weekends", "entre semana", "días laborables",
            "lunes a viernes", "monday to friday", "weekdays",
            "cada otra semana", "cada dos semanas", "bi-weekly"
        ])
        
        # 12. Detectar frecuencia numérica (cada X tiempo)
        has_numeric_frequency = any(re.search(pattern, text_lower) for pattern in [
            r'cada\s+\d+\s+(minutos?|horas?|días?|semanas?|meses?)',
            r'every\s+\d+\s+(minutes?|hours?|days?|weeks?|months?)',
            r'cada\s+\d+h',  # cada 8h
            r'cada\s+\d+hrs?',  # cada 12hrs
        ])
        
        # Es recordatorio si cumple cualquiera de estos criterios:
        is_reminder = (
            has_reminder_keywords or
            (has_date_pattern and has_action_context) or
            has_academic_pattern or
            (has_time_relative and has_context) or
            (has_numeric_date and len(text) > 15) or
            (has_activity_context and (has_date_pattern or has_time_relative)) or
            (has_imperative and (has_date_pattern or has_time_relative or len(text) > 20)) or
            (has_list_format and (has_date_pattern or has_academic_pattern)) or
            (has_time_question and has_activity_context) or
            has_recurring_pattern or  # NUEVO: Patrones recurrentes
            (has_numeric_frequency and has_activity_context)  # NUEVO: Frecuencia numérica con contexto
        )
        
        # Log para debugging (más detallado)
        if is_reminder:
            logger.info(f"📝 Detectado como recordatorio: "
                       f"keywords={has_reminder_keywords}, date={has_date_pattern}, "
                       f"academic={has_academic_pattern}, relative={has_time_relative}, "
                       f"activity={has_activity_context}, imperative={has_imperative}, "
                       f"list={has_list_format}, question={has_time_question}, "
                       f"recurring={has_recurring_pattern}, frequency={has_numeric_frequency}")
        
        return is_reminder
    
    async def _process_reminder_request(self, message: Message, reminder_input: str):
        """Procesar solicitud de recordatorio - Sistema inteligente con recurrencia"""
        try:
            # Mostrar mensaje de procesamiento
            processing_msg = await message.answer("🤖 Interpretando con IA...")
            
            # PRIMERO: Verificar si es un recordatorio recurrente
            recurring_reminders = await self.ai_interpreter.parse_recurring_reminder(reminder_input)
            
            if recurring_reminders:
                # Procesar recordatorios recurrentes
                created_count = 0
                failed_count = 0
                
                for reminder_data in recurring_reminders:
                    try:
                        # Mejorar texto del recordatorio individual
                        context = await self.memory_index.get_user_context(message.from_user.id, limit=3)
                        enhanced_text = await self.ai_interpreter.enhance_reminder_text(reminder_data['text'], context)
                        
                        # Crear recordatorio
                        success = await self.reminder_manager.create_reminder(
                            user_id=message.from_user.id,
                            original_input=reminder_data['text'],
                            reminder_text=enhanced_text,
                            target_date=reminder_data['date']
                        )
                        
                        if success:
                            created_count += 1
                        else:
                            failed_count += 1
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error creando recordatorio recurrente: {e}")
                        failed_count += 1
                
                # Respuesta para recordatorios recurrentes
                if created_count > 0:
                    result_text = f"🔄 **{created_count} recordatorios recurrentes creados**\n\n"
                    
                    # Mostrar algunos ejemplos
                    for i, reminder_data in enumerate(recurring_reminders[:3], 1):
                        date_str = format_datetime_for_user(reminder_data['date'])
                        result_text += f"{i}. {reminder_data['text']}\n   📅 {date_str}\n"
                    
                    if len(recurring_reminders) > 3:
                        result_text += f"   ... y {len(recurring_reminders) - 3} más\n"
                    
                    result_text += "\n🔔 Todos incluyen pre-recordatorios automáticos"
                    
                    if failed_count > 0:
                        result_text += f"\n\n⚠️ {failed_count} recordatorios fallaron"
                    
                    # Agregar a memoria
                    await self.memory_index.add_context(
                        message.from_user.id,
                        f"Creó {created_count} recordatorios recurrentes: {reminder_input[:50]}",
                        "recurring_reminder"
                    )
                    
                    await processing_msg.edit_text(result_text, parse_mode="Markdown")
                    return
                else:
                    # Si falló todo, continuar con método normal
                    pass
            
            # SEGUNDO: Intentar con prompt académico (múltiples recordatorios)
            reminders = await self.ai_interpreter.parse_multiple_reminders(reminder_input)
            
            if reminders:
                # Crear recordatorios usando el método múltiple
                created_count = 0
                failed_count = 0
                
                for reminder_data in reminders:
                    try:
                        # Mejorar texto del recordatorio individual
                        context = await self.memory_index.get_user_context(message.from_user.id, limit=3)
                        enhanced_text = await self.ai_interpreter.enhance_reminder_text(reminder_data['text'], context)
                        
                        # Crear recordatorio
                        success = await self.reminder_manager.create_reminder(
                            user_id=message.from_user.id,
                            original_input=reminder_data['text'],
                            reminder_text=enhanced_text,
                            target_date=reminder_data['date']
                        )
                        
                        if success:
                            created_count += 1
                            # Agregar a memoria
                            await self.memory_index.add_context(
                                message.from_user.id,
                                f"Creó recordatorio: {enhanced_text[:50]}",
                                "reminder_creation"
                            )
                        else:
                            # Verificar si fue rechazado por fecha pasada
                            from datetime import datetime
                            if reminder_data['date'] <= datetime.utcnow():
                                logger.warning(f"⚠️ Recordatorio rechazado por fecha pasada: {reminder_data['text']}")
                            failed_count += 1
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error creando recordatorio individual: {e}")
                        failed_count += 1
                
                # Respuesta final
                if created_count > 0:
                    if created_count == 1:
                        # Un solo recordatorio
                        reminder_data = reminders[0]
                        date_str = format_datetime_for_user(reminder_data['date'])
                        result_text = f"✅ **Recordatorio creado**\n\n📝 {reminder_data['text']}\n📅 {date_str}\n\n⏰ Incluye pre-recordatorios automáticos"
                    else:
                        # Múltiples recordatorios
                        result_text = f"✅ **{created_count} recordatorios creados**\n\n"
                        for i, reminder_data in enumerate(reminders[:created_count], 1):
                            date_str = format_datetime_for_user(reminder_data['date'])
                            result_text += f"{i}. {reminder_data['text']}\n   📅 {date_str}\n\n"
                        result_text += "⏰ Todos incluyen pre-recordatorios automáticos"
                    
                    if failed_count > 0:
                        result_text += f"\n\n⚠️ {failed_count} recordatorios no se pudieron crear (fechas pasadas o errores)"
                
                    await processing_msg.edit_text(result_text, parse_mode="Markdown")
                    return
                else:
                    # Si no se creó ninguno con método múltiple, intentar método simple
                    pass
            
            # SEGUNDO: Si el método académico falló, usar método de lenguaje natural
            logger.info("🔄 Método académico falló, intentando con lenguaje natural...")
            target_date = await self.ai_interpreter.interpret_time_expression(reminder_input)
            
            if not target_date:
                await processing_msg.edit_text(
                    "❌ **No pude interpretar el tiempo**\n\n"
                    "Ejemplos válidos:\n"
                    "• 'recuérdame en 30 minutos'\n" 
                    "• 'mañana a las 9'\n"
                    "• 'el 25 de octubre a las 15:00'\n"
                    "• 'Evaluación escrita 12/09/2025'\n\n"
                    "Intenta ser más específico con la fecha y hora.",
                    parse_mode="Markdown"
                )
                return
            
            # Mejorar texto del recordatorio
            context = await self.memory_index.get_user_context(message.from_user.id, limit=3)
            enhanced_text = await self.ai_interpreter.enhance_reminder_text(reminder_input, context)
            
            # Crear recordatorio único
            success = await self.reminder_manager.create_reminder(
                user_id=message.from_user.id,
                original_input=reminder_input,
                reminder_text=enhanced_text,
                target_date=target_date
            )
            
            if success:
                date_str = format_datetime_for_user(target_date)
                
                await processing_msg.edit_text(
                    f"✅ **Recordatorio creado**\n\n"
                    f"📝 {enhanced_text}\n"
                    f"📅 {date_str}\n\n"
                    f"⏰ Incluye pre-recordatorios automáticos",
                    parse_mode="Markdown"
                )
                
                # Agregar a memoria
                await self.memory_index.add_context(
                    message.from_user.id,
                    f"Creó recordatorio: {enhanced_text[:50]}",
                    "reminder_creation"
                )
            else:
                # Verificar si fue rechazado por fecha pasada
                from datetime import datetime
                if target_date <= datetime.utcnow():
                    await processing_msg.edit_text(
                        "❌ **La fecha ya pasó**\n\n"
                        f"📅 La fecha {format_datetime_for_user(target_date)} ya pasó.\n\n"
                        "Por favor, elige una fecha en el futuro.",
                        parse_mode="Markdown"
                    )
                else:
                    await processing_msg.edit_text("❌ Error creando recordatorio. Intenta de nuevo.")
            
        except Exception as e:
            logger.error(f"❌ Error procesando recordatorio: {e}")
            await message.answer("❌ Error procesando recordatorio. Intenta de nuevo.")


# Función auxiliar para iniciar el bot (usado en main.py)
async def start_telegram_bot(bot_instance: TelegramBot):
    """Función auxiliar para iniciar el bot"""
    await bot_instance.start()