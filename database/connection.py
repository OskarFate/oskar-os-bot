"""
Gestor de conexión a MongoDB Atlas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from loguru import logger

from database.models import User, Reminder, Note, AIMemory, ReminderStatus


class DatabaseManager:
    """Gestor de base de datos MongoDB"""
    
    def __init__(self, connection_string: str, database_name: str):
        self.connection_string = connection_string
        self.database_name = database_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        
        # Colecciones
        self.users: Optional[AsyncIOMotorCollection] = None
        self.reminders: Optional[AsyncIOMotorCollection] = None
        self.notes: Optional[AsyncIOMotorCollection] = None
        self.ai_memory: Optional[AsyncIOMotorCollection] = None
    
    async def connect(self) -> bool:
        """Conectar a MongoDB Atlas"""
        try:
            self.client = AsyncIOMotorClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=10,
                retryWrites=True
            )
            
            # Verificar conexión
            await self.client.admin.command('ping')
            
            # Obtener base de datos
            self.db = self.client[self.database_name]
            
            # Configurar colecciones
            self.users = self.db.users
            self.reminders = self.db.reminders
            self.notes = self.db.notes
            self.ai_memory = self.db.ai_memory
            
            # Crear índices
            await self._create_indexes()
            
            logger.info(f"✅ Conectado a MongoDB: {self.database_name}")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ Error conectando a MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado en MongoDB: {e}")
            return False
    
    async def close(self):
        """Cerrar conexión"""
        if self.client:
            self.client.close()
            logger.info("🔌 Conexión a MongoDB cerrada")
    
    async def _create_indexes(self):
        """Crear índices para optimizar consultas"""
        try:
            # Índices para usuarios
            await self.users.create_index("user_id", unique=True)
            
            # Índices para recordatorios
            await self.reminders.create_index("user_id")
            await self.reminders.create_index("date")
            await self.reminders.create_index("status")
            await self.reminders.create_index([("user_id", 1), ("status", 1)])
            
            # Índices para notas
            await self.notes.create_index("user_id")
            await self.notes.create_index("created_at")
            await self.notes.create_index([("user_id", 1), ("created_at", -1)])
            
            # Índices para memoria de IA
            await self.ai_memory.create_index("user_id")
            await self.ai_memory.create_index("memory_type")
            
            logger.info("📋 Índices de MongoDB creados")
            
        except Exception as e:
            logger.error(f"❌ Error creando índices: {e}")
    
    # --- MÉTODOS PARA USUARIOS ---
    
    async def add_user(self, user_data: Dict[str, Any]) -> bool:
        """Registrar nuevo usuario"""
        try:
            user = User(**user_data)
            
            # Usar upsert para evitar duplicados
            result = await self.users.update_one(
                {"user_id": user.user_id},
                {"$set": user.dict()},
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                logger.info(f"👤 Usuario registrado/actualizado: {user.user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Error registrando usuario: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Obtener usuario por ID"""
        try:
            user_data = await self.users.find_one({"user_id": user_id})
            if user_data:
                return User(**user_data)
            return None
        except Exception as e:
            logger.error(f"❌ Error obteniendo usuario: {e}")
            return None
    
    # --- MÉTODOS PARA RECORDATORIOS ---
    
    async def add_reminder(self, reminder_data: Dict[str, Any]) -> bool:
        """Crear recordatorio"""
        try:
            reminder = Reminder(**reminder_data)
            result = await self.reminders.insert_one(reminder.dict())
            
            if result.inserted_id:
                logger.info(f"⏰ Recordatorio creado para usuario {reminder.user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Error creando recordatorio: {e}")
            return False
    
    async def get_pending_reminders(self, current_time: datetime, tolerance_seconds: int = 30) -> List[Reminder]:
        """Obtener recordatorios pendientes"""
        try:
            # Buscar recordatorios principales
            main_query = {
                "status": ReminderStatus.PENDING,
                "notified": False,
                "date": {
                    "$gte": datetime.fromtimestamp(current_time.timestamp() - tolerance_seconds),
                    "$lte": datetime.fromtimestamp(current_time.timestamp() + tolerance_seconds)
                }
            }
            
            # Buscar pre-recordatorios
            pre_query = {
                "status": ReminderStatus.PENDING,
                "pre_reminders": {
                    "$elemMatch": {
                        "$gte": datetime.fromtimestamp(current_time.timestamp() - tolerance_seconds),
                        "$lte": datetime.fromtimestamp(current_time.timestamp() + tolerance_seconds)
                    }
                }
            }
            
            pending_reminders = []
            
            # Obtener recordatorios principales
            cursor = self.reminders.find(main_query)
            async for reminder_data in cursor:
                pending_reminders.append(Reminder(**reminder_data))
            
            # Obtener pre-recordatorios
            cursor = self.reminders.find(pre_query)
            async for reminder_data in cursor:
                reminder = Reminder(**reminder_data)
                # Verificar cuáles pre-recordatorios están pendientes
                for pre_time in reminder.pre_reminders:
                    time_diff = abs((pre_time - current_time).total_seconds())
                    if time_diff <= tolerance_seconds:
                        pre_key = pre_time.isoformat()
                        if not reminder.pre_reminder_notified.get(pre_key, False):
                            pending_reminders.append(reminder)
                            break
            
            return pending_reminders
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo recordatorios pendientes: {e}")
            return []
    
    async def get_reminder_by_id(self, reminder_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtener recordatorio por ID"""
        try:
            from bson import ObjectId
            reminder = await self.reminders.find_one({
                "_id": ObjectId(reminder_id),
                "user_id": user_id
            })
            return reminder
        except Exception as e:
            logger.error(f"❌ Error obteniendo recordatorio por ID: {e}")
            return None
    
    async def delete_reminder(self, reminder_id: str, user_id: int) -> bool:
        """Eliminar recordatorio específico"""
        try:
            from bson import ObjectId
            result = await self.reminders.delete_one({
                "_id": ObjectId(reminder_id),
                "user_id": user_id
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"❌ Error eliminando recordatorio: {e}")
            return False
    
    async def search_reminders_by_text(self, user_id: int, text_pattern: str) -> List[Dict[str, Any]]:
        """Buscar recordatorios por patrón de texto"""
        try:
            query = {
                "user_id": user_id,
                "status": ReminderStatus.PENDING,
                "$or": [
                    {"text": {"$regex": text_pattern, "$options": "i"}},
                    {"original_input": {"$regex": text_pattern, "$options": "i"}}
                ]
            }
            
            reminders = []
            cursor = self.reminders.find(query)
            async for reminder in cursor:
                reminders.append(reminder)
            
            return reminders
        except Exception as e:
            logger.error(f"❌ Error buscando recordatorios por texto: {e}")
            return []
    
    async def get_reminders_by_date_and_pattern(self, user_id: int, target_date: datetime, text_pattern: str) -> List[Dict[str, Any]]:
        """Obtener recordatorios en fecha específica que coincidan con patrón"""
        try:
            # Buscar en un rango de ±12 horas para la fecha objetivo
            start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            query = {
                "user_id": user_id,
                "status": ReminderStatus.PENDING,
                "date": {
                    "$gte": start_date,
                    "$lte": end_date
                },
                "$or": [
                    {"text": {"$regex": text_pattern, "$options": "i"}},
                    {"original_input": {"$regex": text_pattern, "$options": "i"}}
                ]
            }
            
            reminders = []
            cursor = self.reminders.find(query)
            async for reminder in cursor:
                reminders.append(reminder)
            
            return reminders
        except Exception as e:
            logger.error(f"❌ Error obteniendo recordatorios por fecha y patrón: {e}")
            return []
    
    async def mark_as_notified(self, reminder_id: str, is_pre_reminder: bool = False, pre_reminder_time: Optional[datetime] = None) -> bool:
        """Marcar recordatorio como notificado"""
        try:
            if is_pre_reminder and pre_reminder_time:
                # Marcar pre-recordatorio específico
                update_data = {
                    f"pre_reminder_notified.{pre_reminder_time.isoformat()}": True
                }
            else:
                # Marcar recordatorio principal
                update_data = {"notified": True}
            
            result = await self.reminders.update_one(
                {"_id": ObjectId(reminder_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error marcando como notificado: {e}")
            return False
    
    async def get_user_reminders(self, user_id: int, status: Optional[ReminderStatus] = None, limit: int = 10) -> List[Reminder]:
        """Obtener recordatorios de usuario"""
        try:
            query = {"user_id": user_id}
            if status:
                query["status"] = status
            
            cursor = self.reminders.find(query).sort("date", 1).limit(limit)
            reminders = []
            
            async for reminder_data in cursor:
                reminders.append(Reminder(**reminder_data))
            
            return reminders
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo recordatorios de usuario: {e}")
            return []
    
    # --- MÉTODOS PARA NOTAS ---
    
    async def add_note(self, note_data: Dict[str, Any]) -> bool:
        """Guardar nota"""
        try:
            note = Note(**note_data)
            result = await self.notes.insert_one(note.dict())
            
            if result.inserted_id:
                logger.info(f"📝 Nota creada para usuario {note.user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Error creando nota: {e}")
            return False
    
    async def get_notes_by_keyword(self, user_id: int, keyword: str, limit: int = 10) -> List[Note]:
        """Buscar notas por palabra clave"""
        try:
            query = {
                "user_id": user_id,
                "$or": [
                    {"text": {"$regex": keyword, "$options": "i"}},
                    {"tags": {"$in": [keyword.lower()]}}
                ]
            }
            
            cursor = self.notes.find(query).sort("created_at", -1).limit(limit)
            notes = []
            
            async for note_data in cursor:
                notes.append(Note(**note_data))
            
            return notes
            
        except Exception as e:
            logger.error(f"❌ Error buscando notas: {e}")
            return []
    
    # --- MÉTODOS PARA MEMORIA DE IA ---
    
    async def add_ai_memory(self, memory_data: Dict[str, Any]) -> bool:
        """Guardar memoria de IA"""
        try:
            memory = AIMemory(**memory_data)
            result = await self.ai_memory.insert_one(memory.dict())
            
            if result.inserted_id:
                logger.info(f"🧠 Memoria IA guardada para usuario {memory.user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Error guardando memoria IA: {e}")
            return False
    
    async def get_user_context(self, user_id: int, limit: int = 5) -> List[AIMemory]:
        """Obtener contexto reciente del usuario"""
        try:
            cursor = self.ai_memory.find({"user_id": user_id}).sort("last_accessed", -1).limit(limit)
            memories = []
            
            async for memory_data in cursor:
                memories.append(AIMemory(**memory_data))
            
            return memories
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo contexto de usuario: {e}")
            return []
    
    async def delete_all_user_reminders(self, user_id: int) -> int:
        """Eliminar todos los recordatorios de un usuario"""
        try:
            result = await self.reminders.delete_many({"user_id": user_id})
            deleted_count = result.deleted_count
            
            if deleted_count > 0:
                logger.info(f"🗑️ Eliminados {deleted_count} recordatorios del usuario {user_id}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error eliminando recordatorios: {e}")
            return 0
    
    async def delete_all_user_notes(self, user_id: int) -> int:
        """Eliminar todas las notas de un usuario"""
        try:
            result = await self.notes.delete_many({"user_id": user_id})
            deleted_count = result.deleted_count
            
            if deleted_count > 0:
                logger.info(f"🗑️ Eliminadas {deleted_count} notas del usuario {user_id}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error eliminando notas: {e}")
            return 0
    
    async def update_reminder_text(self, reminder_id: str, new_text: str) -> bool:
        """
        Actualizar el texto de un recordatorio
        
        Args:
            reminder_id: ID del recordatorio
            new_text: Nuevo texto para el recordatorio
            
        Returns:
            bool: True si se actualizó exitosamente
        """
        try:
            result = await self.reminders.update_one(
                {"_id": ObjectId(reminder_id)},
                {
                    "$set": {
                        "text": new_text,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Texto de recordatorio actualizado: {reminder_id}")
                return True
            else:
                logger.warning(f"⚠️ No se encontró recordatorio para actualizar: {reminder_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error actualizando texto de recordatorio: {e}")
            return False