# OskarOS Assistant Bot

Un bot de Telegram con IA que actúa como segundo cerebro personal, utilizando Llama 3.3 para interpretar lenguaje natural, MongoDB Atlas para persistencia y APScheduler para recordatorios automáticos.

## 🚀 Características

- **Interpretación de lenguaje natural**: Convierte frases como "en 3 horas" a fechas precisas
- **Recordatorios inteligentes**: Alertas automáticas (7d, 2d, 1d antes del evento)
- **Notas semánticas**: Clasificación automática por tema, prioridad y sentimiento
- **Resúmenes semanales**: Generados por IA
- **Búsqueda inteligente**: Busca por contenido o intención
- **Soporte para voz**: (Futuro) Transcripción y procesamiento de audio

## 🏗️ Arquitectura

```
oskaros_bot/
├── bot/
│   ├── telegram_interface.py    # Manejo de comandos y mensajes
│   ├── ai_interpreter.py        # Integración con OpenRouter/Llama 3.3
│   ├── reminder_manager.py      # Gestión de recordatorios
│   ├── note_manager.py          # Almacenamiento de notas
│   ├── scheduler_service.py     # Notificaciones automáticas
│   └── memory_index.py          # Contexto de usuario
├── database/
│   ├── models.py               # Esquemas de MongoDB
│   └── connection.py           # Configuración de base de datos
├── config/
│   └── settings.py             # Configuración general
├── utils/
│   ├── logger.py              # Sistema de logging
│   └── helpers.py             # Funciones auxiliares
├── main.py                    # Punto de entrada
└── requirements.txt
```

## 📋 Comandos del Bot

- `/start` - Mensaje de bienvenida
- `/recordar <texto>` - Crear recordatorio interpretando fecha
- `/nota <texto>` - Guardar una nota
- `/listar` - Mostrar próximos recordatorios
- `/buscar <palabra>` - Buscar notas o eventos
- `/resumen` - Generar resumen semanal con IA
- `/status` - Verificar uptime y latencia

## 🛠️ Instalación

1. **Clonar repositorio**:
   ```bash
   git clone <repository-url>
   cd conchetumare
   ```

2. **Configurar entorno virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # o venv\Scripts\activate  # Windows
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:
   ```bash
   cp .env.example .env
   # Editar .env con tus credenciales
   ```

5. **Ejecutar el bot**:
   ```bash
   python main.py
   ```

## ⚙️ Configuración

### Telegram Bot
1. Crear bot con [@BotFather](https://t.me/BotFather)
2. Obtener token y agregarlo a `.env`

### OpenRouter API
1. Registrarse en [OpenRouter](https://openrouter.ai/)
2. Obtener API key para Llama 3.3 70B Instruct
3. Agregar key a `.env`

### MongoDB Atlas
1. Crear cluster en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Configurar usuario y obtener connection string
3. Agregar string a `.env`

## 🗄️ Base de Datos

### Colecciones MongoDB

#### `users`
```json
{
  "user_id": 123456789,
  "username": "usuario",
  "language": "es",
  "timezone": "UTC",
  "created_at": "2025-10-06T00:00:00Z"
}
```

#### `reminders`
```json
{
  "user_id": 123456789,
  "text": "Entregar trabajo",
  "date": "2025-10-08T15:43:10Z",
  "pre_reminders": [
    "2025-10-01T15:43:10Z",
    "2025-10-06T15:43:10Z",
    "2025-10-07T15:43:10Z"
  ],
  "status": "pending",
  "created_at": "2025-10-06T15:43:00Z",
  "notified": false
}
```

#### `notes`
```json
{
  "user_id": 123456789,
  "text": "Idea para proyecto",
  "tags": ["trabajo", "importante"],
  "priority": "high",
  "sentiment": "positive",
  "created_at": "2025-10-06T15:43:00Z"
}
```

#### `ai_memory`
```json
{
  "user_id": 123456789,
  "text": "Usuario prefiere recordatorios por la mañana",
  "type": "preference",
  "created_at": "2025-10-06T15:43:00Z"
}
```

## 🚀 Despliegue

### Render
```bash
# Configurar en Render con Python environment
# Variables de entorno desde .env
```

### DigitalOcean
```bash
# Usar App Platform o Droplet
# Configurar variables de entorno
```

### Vercel (solo para cron jobs)
```bash
# Para tareas programadas complementarias
```

## 🧪 Pruebas

Escenarios de prueba recomendados:

```python
# Interpretación temporal
"en 10 segundos"           # → +10s desde ahora
"mañana a las 9"          # → próximo día 09:00
"el 25 de octubre a las 18:00"  # → fecha específica
"en 244 segundos"         # → +244s desde ahora
```

## 📊 Monitoring

- Logs con `loguru`
- Métricas de respuesta < 10s
- Status endpoint para healthchecks
- Error tracking y reinicio automático

## 🔒 Seguridad

- Variables sensibles en `.env`
- Conexiones TLS a MongoDB
- Usuarios con permisos mínimos
- No logging de datos personales
- Validación de entrada

## 📝 Licencia

MIT License

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request