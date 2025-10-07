"""
Modelos de datos para MongoDB
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Annotated
from enum import Enum
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId


def validate_object_id(v: Any) -> ObjectId:
    """Validador para ObjectId"""
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


# Tipo ObjectId para Pydantic v2
PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class ReminderStatus(str, Enum):
    """Estados de recordatorios"""
    PENDING = "pending"
    COMPLETED = "completed"
    MISSED = "missed"
    CANCELLED = "cancelled"


class NoteType(str, Enum):
    """Tipos de notas"""
    GENERAL = "general"
    IDEA = "idea"
    TASK = "task"
    THOUGHT = "thought"


class MemoryType(str, Enum):
    """Tipos de memoria de IA"""
    PREFERENCE = "preference"
    HABIT = "habit"
    CONTEXT = "context"
    PATTERN = "pattern"


class User(BaseModel):
    """Modelo de usuario"""
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    user_id: int = Field(..., description="ID único de Telegram")
    username: Optional[str] = Field(None, description="Username de Telegram")
    first_name: Optional[str] = Field(None, description="Nombre")
    last_name: Optional[str] = Field(None, description="Apellido")
    language: str = Field(default="es", description="Idioma preferido")
    timezone: str = Field(default="America/Santiago", description="Zona horaria")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: Optional[datetime] = Field(None)
    is_active: bool = Field(default=True)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class Reminder(BaseModel):
    """Modelo de recordatorio"""
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    user_id: int = Field(..., description="ID del usuario")
    text: str = Field(..., description="Texto del recordatorio")
    original_input: str = Field(..., description="Input original del usuario")
    date: datetime = Field(..., description="Fecha y hora del recordatorio")
    recurring: bool = Field(default=False, description="Si es un recordatorio recurrente")
    frequency: Optional[str] = Field(None, description="Frecuencia de recurrencia (daily, weekly, monthly)")
    pre_reminders: List[datetime] = Field(default_factory=list, description="Recordatorios previos")
    status: ReminderStatus = Field(default=ReminderStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notified: bool = Field(default=False, description="Si ya se notificó")
    pre_reminder_notified: Dict[str, bool] = Field(default_factory=dict, description="Notificaciones previas enviadas")
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class Note(BaseModel):
    """Modelo de nota"""
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    user_id: int = Field(..., description="ID del usuario")
    text: str = Field(..., description="Contenido de la nota")
    tags: List[str] = Field(default_factory=list, description="Etiquetas automáticas")
    note_type: NoteType = Field(default=NoteType.GENERAL)
    priority: Optional[str] = Field(None, description="Prioridad (low, medium, high)")
    sentiment: Optional[str] = Field(None, description="Sentimiento (positive, negative, neutral)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(None)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class UserMemory(BaseModel):
    """Modelo para la memoria contextual del usuario"""
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    user_id: int = Field(..., description="ID del usuario")
    habits: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    context_history: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class AIMemory(BaseModel):
    """Modelo de memoria de IA"""
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    user_id: int = Field(..., description="ID del usuario")
    text: str = Field(..., description="Información aprendida")
    memory_type: MemoryType = Field(..., description="Tipo de memoria")
    confidence: float = Field(default=1.0, description="Confianza en la información (0.0-1.0)")
    source: str = Field(..., description="Origen de la información")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = Field(None)
    access_count: int = Field(default=0)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }