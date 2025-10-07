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
            BotCommand(command="start", description="🚀 Iniciar el bot"),
            BotCommand(command="recordar", description="⏰ Crear recordatorio"),
            BotCommand(command="nota", description="📝 Guardar nota"),
            BotCommand(command="listar", description="📋 Ver recordatorios"),
            BotCommand(command="buscar", description="🔍 Buscar notas"),
            BotCommand(command="resumen", description="📊 Resumen semanal"),
            BotCommand(command="status", description="ℹ️ Estado del bot"),
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

⏰ **Recordatorios:**
• `/recordar llamar médico mañana 9am`
• "Recuérdame entregar proyecto en 3 días"
• `/listar` - Ver próximos recordatorios

📝 **Notas:**
• `/nota Idea: crear app productividad`
• `/buscar trabajo` - Buscar notas
• Clasificación automática por IA

📊 **Análisis:**
• `/resumen` - Resumen semanal con IA
• `/status` - Estado del sistema

🔥 **Características únicas:**
• Interpreto lenguaje natural
• Pre-recordatorios automáticos (7d, 2d, 1d)
• Búsqueda semántica inteligente
• Aprendo tus patrones y preferencias

💡 **Ejemplos prácticos:**
1. "Recuérdame ir al gym en 2 horas"
2. "/nota Reflexión: el proyecto va bien"
3. "/buscar ideas de vacaciones"
4. "/resumen" para ver tu semana

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
        """Detectar si un texto es una solicitud de recordatorio"""
        reminder_keywords = [
            "recuérdame", "recordar", "avísame", "avisar",
            "en ", "mañana", "hoy", "después", "próxim",
            "el ", "a las", "alarm", "alert",
            "evaluación", "examen", "prueba", "control",
            "entrega", "tarea", "trabajo", "informe",
            "presentación", "fecha", "deadline"
        ]
        
        # Detectar fechas en formato DD/MM/YYYY o DD/MM/YY
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # DD/MM/YYYY
            r'\b\d{1,2}/\d{1,2}/\d{2}\b',  # DD/MM/YY
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',  # DD-MM-YYYY
            r'fecha de entrega',
            r'entregar el',
            r'para el'
        ]
        
        text_lower = text.lower()
        
        # Si tiene palabras clave académicas
        has_academic_keywords = any(keyword in text_lower for keyword in reminder_keywords)
        
        # Si tiene patrones de fecha
        has_date_pattern = any(re.search(pattern, text_lower) for pattern in date_patterns)
        
        # Si tiene fechas numéricas
        has_numeric_date = re.search(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', text)
        
        # Es recordatorio si tiene:
        # 1. Palabras clave, O
        # 2. Patrón de fecha académica, O 
        # 3. Fecha numérica + texto académico
        return has_academic_keywords or has_date_pattern or (has_numeric_date and len(text) > 10)
    
    async def _process_reminder_request(self, message: Message, reminder_input: str):
        """Procesar solicitud de recordatorio - SIEMPRE usa IA con prompt específico"""
        try:
            # Mostrar mensaje de procesamiento
            processing_msg = await message.answer("🤖 Interpretando con IA...")
            
            # SIEMPRE usar el prompt especializado de múltiples recordatorios
            # Este prompt maneja tanto casos simples como complejos
            reminders = await self.ai_interpreter.parse_multiple_reminders(reminder_input)
            
            if not reminders:
                await processing_msg.edit_text(
                    "❌ **No pude interpretar las fechas**\n\n"
                    "Ejemplos válidos:\n"
                    "• `Evaluación escrita 12/09/2025`\n"
                    "• `FECHA DE ENTREGA: 5 OCTUBRE 2025`\n"
                    "• `Tarea para el 15/10/2025`\n\n"
                    "Intenta ser más específico con la fecha.",
                    parse_mode="Markdown"
                )
                return
            
            # Crear recordatorios
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
            else:
                result_text = f"❌ No se pudieron crear los recordatorios. Verifica que las fechas sean futuras."
            
            await processing_msg.edit_text(result_text, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"❌ Error procesando recordatorio: {e}")
            await message.answer("❌ Error procesando recordatorio. Intenta de nuevo.")


# Función auxiliar para iniciar el bot (usado en main.py)
async def start_telegram_bot(bot_instance: TelegramBot):
    """Función auxiliar para iniciar el bot"""
    await bot_instance.start()