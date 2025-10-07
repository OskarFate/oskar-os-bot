"""
Gestor de notas con clasificación automática por IA
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from loguru import logger

from database.connection import DatabaseManager
from database.models import Note, NoteType
from bot.ai_interpreter import AIInterpreter
from utils.helpers import extract_keywords_from_text


class NoteManager:
    """Gestor de notas con clasificación inteligente"""
    
    def __init__(self, db_manager: DatabaseManager, ai_interpreter: AIInterpreter):
        self.db = db_manager
        self.ai = ai_interpreter
    
    async def create_note(self, user_id: int, note_text: str, auto_classify: bool = True) -> bool:
        """
        Crear nota con clasificación automática
        
        Args:
            user_id: ID del usuario de Telegram
            note_text: Contenido de la nota
            auto_classify: Si debe clasificar automáticamente con IA
        
        Returns:
            True si se creó exitosamente
        """
        try:
            # Extraer palabras clave básicas
            basic_keywords = extract_keywords_from_text(note_text)
            
            # Clasificación por IA (opcional)
            classification = {}
            if auto_classify:
                try:
                    classification = await self.ai.classify_note(note_text)
                except Exception as e:
                    logger.warning(f"⚠️ Error en clasificación IA: {e}")
                    classification = {}
            
            # Preparar datos de la nota
            note_data = {
                "user_id": user_id,
                "text": note_text.strip(),
                "tags": classification.get("tags", basic_keywords),
                "note_type": NoteType(classification.get("category", "general")),
                "priority": classification.get("priority", "medium"),
                "sentiment": classification.get("sentiment", "neutral"),
                "created_at": datetime.utcnow()
            }
            
            # Guardar en base de datos
            success = await self.db.add_note(note_data)
            
            if success:
                logger.info(f"✅ Nota creada para usuario {user_id}: '{note_text[:50]}...'")
                if classification:
                    logger.info(f"🏷️ Clasificación: {classification}")
                return True
            else:
                logger.error("❌ Error guardando nota en BD")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error creando nota: {e}")
            return False
    
    async def search_notes(self, user_id: int, query: str, use_ai_search: bool = True, limit: int = 10) -> List[Note]:
        """
        Buscar notas por palabra clave o semánticamente
        
        Args:
            user_id: ID del usuario
            query: Término de búsqueda
            use_ai_search: Si usar búsqueda semántica con IA
            limit: Número máximo de resultados
        
        Returns:
            Lista de notas encontradas
        """
        try:
            # Búsqueda básica por palabra clave
            basic_results = await self.db.get_notes_by_keyword(user_id, query, limit)
            
            # Si no hay resultados básicos o se solicita IA, usar búsqueda semántica
            if (not basic_results or use_ai_search) and len(basic_results) < limit:
                try:
                    # Obtener más notas para análisis semántico
                    all_notes = await self.db.get_notes_by_keyword(user_id, "", limit=100)
                    
                    if all_notes:
                        # Convertir a dict para IA
                        notes_for_ai = [note.dict() for note in all_notes]
                        
                        # Búsqueda semántica
                        semantic_results = await self.ai.search_notes_semantically(query, notes_for_ai)
                        
                        # Convertir de vuelta a objetos Note
                        semantic_notes = []
                        for note_dict in semantic_results:
                            try:
                                semantic_notes.append(Note(**note_dict))
                            except Exception as e:
                                logger.warning(f"⚠️ Error convirtiendo nota: {e}")
                        
                        # Combinar resultados (básicos + semánticos) sin duplicados
                        combined_results = basic_results.copy()
                        basic_ids = {str(note.id) for note in basic_results}
                        
                        for semantic_note in semantic_notes:
                            if str(semantic_note.id) not in basic_ids:
                                combined_results.append(semantic_note)
                                if len(combined_results) >= limit:
                                    break
                        
                        logger.info(f"🔍 Búsqueda combinada: {len(basic_results)} básicos + {len(semantic_notes)} semánticos")
                        return combined_results[:limit]
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error en búsqueda semántica: {e}")
            
            logger.info(f"🔍 Búsqueda básica: {len(basic_results)} resultados para '{query}'")
            return basic_results
            
        except Exception as e:
            logger.error(f"❌ Error buscando notas: {e}")
            return []
    
    async def get_recent_notes(self, user_id: int, limit: int = 10) -> List[Note]:
        """
        Obtener notas recientes del usuario
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de notas
        
        Returns:
            Lista de notas recientes
        """
        try:
            # Usar búsqueda por palabra vacía para obtener todas las notas recientes
            notes = await self.db.get_notes_by_keyword(user_id, "", limit)
            
            logger.info(f"📚 Obtenidas {len(notes)} notas recientes para usuario {user_id}")
            return notes
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo notas recientes: {e}")
            return []
    
    async def get_notes_by_tag(self, user_id: int, tag: str, limit: int = 10) -> List[Note]:
        """
        Obtener notas por etiqueta específica
        
        Args:
            user_id: ID del usuario
            tag: Etiqueta a buscar
            limit: Número máximo de resultados
        
        Returns:
            Lista de notas con esa etiqueta
        """
        try:
            # Usar búsqueda por palabra clave que también busca en tags
            notes = await self.db.get_notes_by_keyword(user_id, tag, limit)
            
            # Filtrar solo las que realmente tienen la etiqueta
            tagged_notes = [
                note for note in notes 
                if tag.lower() in [t.lower() for t in note.tags]
            ]
            
            logger.info(f"🏷️ {len(tagged_notes)} notas encontradas con etiqueta '{tag}'")
            return tagged_notes
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo notas por etiqueta: {e}")
            return []
    
    async def get_notes_by_priority(self, user_id: int, priority: str, limit: int = 10) -> List[Note]:
        """
        Obtener notas por prioridad
        
        Args:
            user_id: ID del usuario
            priority: Prioridad (low, medium, high)
            limit: Número máximo de resultados
        
        Returns:
            Lista de notas con esa prioridad
        """
        try:
            # Obtener notas recientes y filtrar por prioridad
            all_notes = await self.get_recent_notes(user_id, limit=100)
            
            priority_notes = [
                note for note in all_notes 
                if note.priority and note.priority.lower() == priority.lower()
            ]
            
            logger.info(f"⭐ {len(priority_notes)} notas de prioridad '{priority}'")
            return priority_notes[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo notas por prioridad: {e}")
            return []
    
    async def get_weekly_notes_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Obtener resumen semanal de notas para un usuario
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Dict con estadísticas de la semana
        """
        try:
            # Obtener notas recientes (últimas 50)
            recent_notes = await self.get_recent_notes(user_id, limit=50)
            
            # Filtrar por última semana
            one_week_ago = datetime.utcnow().timestamp() - (7 * 24 * 60 * 60)
            weekly_notes = [
                note for note in recent_notes 
                if note.created_at.timestamp() >= one_week_ago
            ]
            
            # Calcular estadísticas
            total = len(weekly_notes)
            
            # Contar por tipo
            types_count = {}
            for note in weekly_notes:
                note_type = note.note_type.value if note.note_type else "general"
                types_count[note_type] = types_count.get(note_type, 0) + 1
            
            # Contar por prioridad
            priority_count = {}
            for note in weekly_notes:
                priority = note.priority or "medium"
                priority_count[priority] = priority_count.get(priority, 0) + 1
            
            # Tags más comunes
            all_tags = []
            for note in weekly_notes:
                all_tags.extend(note.tags)
            
            tag_count = {}
            for tag in all_tags:
                tag_count[tag] = tag_count.get(tag, 0) + 1
            
            # Top 5 tags
            top_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:5]
            
            summary = {
                "total": total,
                "types": types_count,
                "priorities": priority_count,
                "top_tags": top_tags,
                "notes": [note.dict() for note in weekly_notes]
            }
            
            logger.info(f"📊 Resumen semanal de notas para usuario {user_id}: {total} notas")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo resumen semanal de notas: {e}")
            return {
                "total": 0,
                "types": {},
                "priorities": {},
                "top_tags": [],
                "notes": []
            }
    
    async def get_all_user_tags(self, user_id: int) -> List[str]:
        """
        Obtener todas las etiquetas únicas del usuario
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Lista de etiquetas únicas
        """
        try:
            notes = await self.get_recent_notes(user_id, limit=200)
            
            all_tags = set()
            for note in notes:
                all_tags.update(note.tags)
            
            unique_tags = sorted(list(all_tags))
            
            logger.info(f"🏷️ {len(unique_tags)} etiquetas únicas para usuario {user_id}")
            return unique_tags
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo etiquetas: {e}")
            return []