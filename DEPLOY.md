# 🚀 Despliegue en DigitalOcean - Guía Paso a Paso

## Opción 1: DigitalOcean App Platform (Recomendado - Más fácil)

### Paso 1: Subir código a GitHub

1. **Crear repositorio en GitHub:**
   ```bash
   # En tu terminal
   cd /home/haerin/conchetumare
   git init
   git add .
   git commit -m "Initial commit: OskarOS Assistant Bot"
   
   # Crear repo en GitHub y luego:
   git remote add origin https://github.com/TU-USERNAME/oskaros-bot.git
   git branch -M main
   git push -u origin main
   ```

### Paso 2: Crear App en DigitalOcean

1. **Ve a DigitalOcean Console:**
   - Ir a https://cloud.digitalocean.com/
   - Hacer login en tu cuenta

2. **Crear nueva App:**
   - Click en "Create" → "Apps"
   - Seleccionar "GitHub" como source
   - Conectar tu repositorio `oskaros-bot`
   - Branch: `main`

3. **Configurar la App:**
   - **Name:** `oskaros-assistant-bot`
   - **Region:** Cerca de ti (ej: San Francisco)
   - **Plan:** Basic ($5/month) o Development ($0 por 3 meses)

### Paso 3: Configurar Variables de Entorno

En DigitalOcean App Platform, ir a Settings → Environment Variables:

```
TELEGRAM_BOT_TOKEN=8250992220:AAFz2KkoUjqsoizJjFaskQQblYcEDTRlMdQ
OPENROUTER_API_KEY=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
MONGODB_CONNECTION_STRING=mongodb+srv://oskarfate_db_user:PaKMLWbPO8wWX6RT@secondbraincluster.2twy2ae.mongodb.net/?retryWrites=true&w=majority&appName=secondbraincluster
MONGODB_DATABASE_NAME=second_brain
ENVIRONMENT=production
LOG_LEVEL=INFO
DEFAULT_TIMEZONE=America/Santiago
```

### Paso 4: Deploy

1. Click "Create Resource"
2. Esperar el build (3-5 minutos)
3. ¡Tu bot estará online 24/7!

---

## Opción 2: DigitalOcean Droplet (VPS)

### Paso 1: Crear Droplet

1. **Crear Droplet:**
   - Ir a "Create" → "Droplets"
   - **Image:** Ubuntu 22.04 LTS
   - **Size:** Basic $6/month (1GB RAM)
   - **Region:** Cerca de ti

### Paso 2: Configurar Servidor

```bash
# Conectar via SSH
ssh root@YOUR_DROPLET_IP

# Actualizar sistema
apt update && apt upgrade -y

# Instalar Python y herramientas
apt install -y python3 python3-pip python3-venv git nginx

# Crear usuario para el bot
adduser oskaros
usermod -aG sudo oskaros
su - oskaros

# Clonar repositorio
git clone https://github.com/TU-USERNAME/oskaros-bot.git
cd oskaros-bot

# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 3: Configurar Variables de Entorno

```bash
# Crear archivo .env
nano .env

# Pegar las variables:
TELEGRAM_BOT_TOKEN=tu_token_aqui
OPENROUTER_API_KEY=tu_api_key_aqui
MONGODB_CONNECTION_STRING=tu_mongodb_string_aqui
MONGODB_DATABASE_NAME=second_brain
ENVIRONMENT=production
LOG_LEVEL=INFO
DEFAULT_TIMEZONE=America/Santiago
```

### Paso 4: Crear Servicio Systemd

```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/oskaros-bot.service

# Contenido:
[Unit]
Description=OskarOS Assistant Bot
After=network.target

[Service]
Type=simple
User=oskaros
WorkingDirectory=/home/oskaros/oskaros-bot
Environment=PATH=/home/oskaros/oskaros-bot/.venv/bin
ExecStart=/home/oskaros/oskaros-bot/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Paso 5: Iniciar Servicio

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar y iniciar servicio
sudo systemctl enable oskaros-bot
sudo systemctl start oskaros-bot

# Verificar estado
sudo systemctl status oskaros-bot

# Ver logs
sudo journalctl -u oskaros-bot -f
```

---

## 🎯 Recomendación

**Para empezar:** Usa **App Platform** (Opción 1) - Es más fácil y automático.

**Para control total:** Usa **Droplet** (Opción 2) - Más configuración pero más control.

---

## 🔧 Comandos Útiles

```bash
# Ver logs del bot
sudo journalctl -u oskaros-bot -f

# Reiniciar bot
sudo systemctl restart oskaros-bot

# Actualizar código
cd /home/oskaros/oskaros-bot
git pull
sudo systemctl restart oskaros-bot

# Verificar recursos
htop
df -h
```

## 📊 Monitoreo

Tu bot tendrá:
- ✅ Health check en `/health`
- ✅ Logs automáticos
- ✅ Restart automático si falla
- ✅ Uptime 24/7

¡Listo para producción! 🚀