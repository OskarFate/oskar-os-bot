"""
Índice de memoria para contexto y hábitos del usuario
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from loguru import logger

from database.connection import DatabaseManager
from database.models import AIMemory, MemoryType


class MemoryIndex:
    """Gestor de memoria contextual del usuario"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def add_preference(self, user_id: int, preference_text: str, source: str = "user_input") -> bool:
        """
        Agregar preferencia del usuario
        
        Args:
            user_id: ID del usuario
            preference_text: Descripción de la preferencia
            source: Origen de la información
        
        Returns:
            True si se guardó exitosamente
        """
        try:
            memory_data = {
                "user_id": user_id,
                "text": preference_text,
                "memory_type": MemoryType.PREFERENCE,
                "confidence": 0.8,
                "source": source,
                "created_at": datetime.utcnow(),
                "access_count": 0
            }
            
            success = await self.db.add_ai_memory(memory_data)
            
            if success:
                logger.info(f"💾 Preferencia guardada para usuario {user_id}: '{preference_text[:50]}...'")
                return True
            else:
                logger.error("❌ Error guardando preferencia")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error agregando preferencia: {e}")
            return False
    
    async def add_habit_pattern(self, user_id: int, pattern_text: str, confidence: float = 0.7) -> bool:
        """
        Agregar patrón de hábito detectado
        
        Args:
            user_id: ID del usuario
            pattern_text: Descripción del patrón
            confidence: Nivel de confianza (0.0-1.0)
        
        Returns:
            True si se guardó exitosamente
        """
        try:
            memory_data = {
                "user_id": user_id,
                "text": pattern_text,
                "memory_type": MemoryType.HABIT,
                "confidence": min(max(confidence, 0.0), 1.0),  # Clamp entre 0 y 1
                "source": "pattern_detection",
                "created_at": datetime.utcnow(),
                "access_count": 0
            }
            
            success = await self.db.add_ai_memory(memory_data)
            
            if success:
                logger.info(f"🔄 Hábito detectado para usuario {user_id}: '{pattern_text[:50]}...'")
                return True
            else:
                logger.error("❌ Error guardando hábito")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error agregando hábito: {e}")
            return False
    
    async def add_context(self, user_id: int, context_text: str, source: str = "conversation") -> bool:
        """
        Agregar contexto conversacional
        
        Args:
            user_id: ID del usuario
            context_text: Información contextual
            source: Origen del contexto
        
        Returns:
            True si se guardó exitosamente
        """
        try:
            memory_data = {
                "user_id": user_id,
                "text": context_text,
                "memory_type": MemoryType.CONTEXT,
                "confidence": 0.6,
                "source": source,
                "created_at": datetime.utcnow(),
                "access_count": 0
            }
            
            success = await self.db.add_ai_memory(memory_data)
            
            if success:
                logger.debug(f"💬 Contexto guardado para usuario {user_id}")
                return True
            else:
                logger.error("❌ Error guardando contexto")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error agregando contexto: {e}")
            return False
    
    async def get_user_context(self, user_id: int, memory_types: List[MemoryType] = None, limit: int = 10) -> List[str]:
        """
        Obtener contexto relevante del usuario
        
        Args:
            user_id: ID del usuario
            memory_types: Tipos de memoria a incluir (default: todos)
            limit: Número máximo de elementos
        
        Returns:
            Lista de strings con información contextual
        """
        try:
            # Obtener memorias de la base de datos
            memories = await self.db.get_user_context(user_id, limit)
            
            # Filtrar por tipo si se especifica
            if memory_types:
                memories = [m for m in memories if m.memory_type in memory_types]
            
            # Convertir a lista de strings
            context_list = []
            for memory in memories:
                memory_type_emoji = {
                    MemoryType.PREFERENCE: "⚙️",
                    MemoryType.HABIT: "🔄",
                    MemoryType.CONTEXT: "💬",
                    MemoryType.PATTERN: "📊"
                }.get(memory.memory_type, "🧠")
                
                context_item = f"{memory_type_emoji} {memory.text}"
                context_list.append(context_item)
                
                # Actualizar contador de accesos (implementar en el futuro)
                # await self._increment_access_count(memory.id)
            
            logger.debug(f"🧠 Obtenido contexto para usuario {user_id}: {len(context_list)} elementos")
            return context_list
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo contexto: {e}")
            return []
    
    async def get_preferences(self, user_id: int) -> List[str]:
        """
        Obtener solo las preferencias del usuario
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Lista de preferencias
        """
        return await self.get_user_context(user_id, [MemoryType.PREFERENCE], limit=5)
    
    async def get_habits(self, user_id: int) -> List[str]:
        """
        Obtener patrones de hábitos del usuario
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Lista de hábitos detectados
        """
        return await self.get_user_context(user_id, [MemoryType.HABIT], limit=5)
    
    async def analyze_reminder_patterns(self, user_id: int, recent_reminders: List[Dict]) -> Optional[str]:
        """
        Analizar patrones en los recordatorios del usuario
        
        Args:
            user_id: ID del usuario
            recent_reminders: Lista de recordatorios recientes
        
        Returns:
            Descripción del patrón detectado o None
        """
        try:
            if len(recent_reminders) < 3:
                return None
            
            # Análisis básico de patrones temporales
            hour_counts = {}
            day_counts = {}
            
            for reminder in recent_reminders:
                if 'date' in reminder:
                    date = reminder['date']
                    if isinstance(date, datetime):
                        hour = date.hour
                        day = date.weekday()  # 0=Monday, 6=Sunday
                        
                        hour_counts[hour] = hour_counts.get(hour, 0) + 1
                        day_counts[day] = day_counts.get(day, 0) + 1
            
            patterns_detected = []
            
            # Patrón de horario preferido
            if hour_counts:
                most_common_hour = max(hour_counts.items(), key=lambda x: x[1])
                if most_common_hour[1] >= 2:  # Al menos 2 recordatorios en esa hora
                    patterns_detected.append(f"Prefiere recordatorios a las {most_common_hour[0]:02d}:00")
            
            # Patrón de día de la semana
            if day_counts:
                most_common_day = max(day_counts.items(), key=lambda x: x[1])
                if most_common_day[1] >= 2:
                    day_names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
                    day_name = day_names[most_common_day[0]]
                    patterns_detected.append(f"Frecuentemente programa para {day_name}")
            
            # Combinar patrones
            if patterns_detected:
                pattern_text = "; ".join(patterns_detected)
                
                # Guardar patrón detectado
                await self.add_habit_pattern(user_id, pattern_text, confidence=0.7)
                
                logger.info(f"📊 Patrón detectado para usuario {user_id}: {pattern_text}")
                return pattern_text
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error analizando patrones: {e}")
            return None
    
    async def suggest_improvements(self, user_id: int) -> List[str]:
        """
        Sugerir mejoras basadas en la memoria del usuario
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Lista de sugerencias
        """
        try:
            suggestions = []
            
            # Obtener contexto del usuario
            preferences = await self.get_preferences(user_id)
            habits = await self.get_habits(user_id)
            
            # Sugerencias basadas en hábitos
            for habit in habits:
                if "prefiere recordatorios a las" in habit.lower():
                    suggestions.append("💡 Considera usar pre-recordatorios para tareas importantes")
                elif "frecuentemente programa" in habit.lower():
                    suggestions.append("📅 Podrías beneficiarte de recordatorios semanales recurrentes")
            
            # Sugerencias generales si no hay suficiente contexto
            if not suggestions:
                suggestions = [
                    "📝 Prueba usar notas para capturar ideas rápidas",
                    "⏰ Los pre-recordatorios te ayudan a no olvidar tareas importantes",
                    "🔍 Usa el comando /buscar para encontrar notas anteriores"
                ]
            
            logger.debug(f"💡 {len(suggestions)} sugerencias generadas para usuario {user_id}")
            return suggestions[:3]  # Máximo 3 sugerencias
            
        except Exception as e:
            logger.error(f"❌ Error generando sugerencias: {e}")
            return ["💡 Sigue usando el bot para mejorar tu productividad"]
    
    async def cleanup_old_context(self, user_id: int, days_old: int = 30) -> int:
        """
        Limpiar contexto antiguo (implementación futura)
        
        Args:
            user_id: ID del usuario
            days_old: Días de antigüedad para limpiar
        
        Returns:
            Número de elementos limpiados
        """
        try:
            # TODO: Implementar cleanup en DatabaseManager
            # Por ahora solo logging
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            logger.info(f"🧹 Cleanup de contexto anterior a {cutoff_date} para usuario {user_id}")
            
            # Retornar 0 como placeholder
            return 0
            
        except Exception as e:
            logger.error(f"❌ Error en cleanup de contexto: {e}")
            return 0