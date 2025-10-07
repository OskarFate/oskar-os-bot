# 🤖 Setup Instructions - OskarOS Assistant Bot

## 📋 Prerequisites

1. **Python 3.8+** (project uses 3.13)
2. **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
3. **OpenRouter API Key** from [OpenRouter](https://openrouter.ai/)
4. **MongoDB Atlas** cluster from [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)

## 🚀 Quick Start

### 1. Clone and Setup Environment

```bash
# Navigate to project directory
cd /home/haerin/conchetumare

# The virtual environment is already configured
# Dependencies are already installed
```

### 2. Configure Environment Variables

Edit the `.env` file with your credentials:

```bash
# Edit .env file
nano .env
```

**Required variables:**
```env
# Get from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCDEF1234567890abcdef1234567890ABC

# Get from https://openrouter.ai/
OPENROUTER_API_KEY=sk-or-v1-[TU_CLAVE_REAL_AQUI]

# Get from MongoDB Atlas
MONGODB_CONNECTION_STRING=mongodb+srv://username:password@cluster0.abc123.mongodb.net/

# Database name (can leave as default)
MONGODB_DATABASE_NAME=oskaros_bot

# Environment (development for testing)
ENVIRONMENT=development
LOG_LEVEL=INFO
DEFAULT_TIMEZONE=UTC
```

### 3. Get Your Credentials

#### 🤖 Telegram Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Choose a name: `OskarOS Assistant`
4. Choose a username: `your_oskaros_bot` (must end with `bot`)
5. Copy the token provided

#### 🧠 OpenRouter API Key
1. Go to [OpenRouter](https://openrouter.ai/)
2. Sign up/login
3. Go to "API Keys" section
4. Create new key
5. Copy the key (starts with `sk-or-v1-`)

#### 🗄️ MongoDB Atlas
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create free account
3. Create new cluster (M0 free tier)
4. Go to Database Access → Add Database User
5. Go to Network Access → Add IP Address (0.0.0.0/0 for testing)
6. Go to Database → Connect → Connect your application
7. Copy connection string, replace `<password>` with your password

### 4. Test Configuration

```bash
# Test if everything is configured correctly
python test_setup.py
```

Expected output:
```
🔄 Probando imports...
✅ All modules imported successfully!
✅ Telegram token configured
✅ OpenRouter API key configured  
✅ MongoDB connection configured
```

### 5. Run the Bot

```bash
# Method 1: Direct execution
python main.py

# Method 2: Using VS Code task
# Press Ctrl+Shift+P → "Tasks: Run Task" → "Start OskarOS Bot"
```

Expected startup output:
```
2025-10-06 23:35:01 | INFO | 🚀 Iniciando OskarOS Assistant Bot...
2025-10-06 23:35:01 | INFO | ⚙️ Configuración cargada
2025-10-06 23:35:01 | INFO | 🗄️ Conexión a MongoDB establecida
2025-10-06 23:35:01 | INFO | ⏰ Scheduler iniciado
2025-10-06 23:35:01 | INFO | 🤖 Bot iniciado: @your_oskaros_bot
2025-10-06 23:35:01 | INFO | 📱 Iniciando bot de Telegram...
```

## 🧪 Testing the Bot

1. **Start a conversation** with your bot on Telegram
2. Send `/start` to see the welcome message
3. Try these commands:
   - `/recordar llamar médico mañana a las 9`
   - `/nota Idea: mejorar productividad`
   - `/listar`
   - `/status`

## 📁 Project Structure

```
oskaros_bot/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── .env                   # Environment variables (edit this!)
├── .env.example          # Template
├── README.md             # Main documentation
├── SETUP.md              # This file
├── test_setup.py         # Configuration test
├── bot/
│   ├── telegram_interface.py    # Main bot logic
│   ├── ai_interpreter.py        # OpenRouter/Llama 3.3
│   ├── reminder_manager.py      # Reminder logic
│   ├── note_manager.py          # Note management
│   ├── scheduler_service.py     # Background tasks
│   └── memory_index.py          # User context
├── database/
│   ├── models.py               # MongoDB schemas
│   └── connection.py           # Database manager
├── config/
│   └── settings.py             # Configuration
├── utils/
│   ├── logger.py              # Logging setup
│   └── helpers.py             # Utility functions
└── .vscode/
    └── tasks.json             # VS Code tasks
```

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'loguru'"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### "Token is invalid!"
- Check your `TELEGRAM_BOT_TOKEN` in `.env`
- Make sure token is correct from @BotFather
- No extra spaces or quotes

### "DNS query name does not exist"
- Check your `MONGODB_CONNECTION_STRING` in `.env`
- Make sure MongoDB cluster is running
- Check network access settings in MongoDB Atlas

### "Error API OpenRouter"
- Check your `OPENROUTER_API_KEY` in `.env`
- Make sure you have credits in OpenRouter
- Verify the key starts with `sk-or-v1-`

## 🚀 Deployment

### Render.com (Recommended)
1. Push code to GitHub
2. Connect Render to your repository
3. Use `render.yaml` configuration
4. Add environment variables in Render dashboard

### DigitalOcean App Platform
1. Push code to GitHub
2. Create new app in DigitalOcean
3. Configure environment variables
4. Deploy

### Docker
```bash
# Build image
docker build -t oskaros-bot .

# Run container
docker run -d --env-file .env oskaros-bot
```

## 📝 Features

- ✅ Natural language reminder interpretation
- ✅ Automated pre-reminders (7d, 2d, 1d)
- ✅ Smart note classification with AI
- ✅ Semantic search
- ✅ Weekly AI summaries
- ✅ User context memory
- ✅ Background scheduler
- ✅ Error handling and logging

## 🆘 Support

If you need help:
1. Check this setup guide
2. Run `python test_setup.py` to verify configuration
3. Check logs for specific error messages
4. Verify all credentials are correct

Happy coding! 🎉