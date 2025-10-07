<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->
- [x] Verify that the copilot-instructions.md file in the .github directory is created. ✅ Created

- [x] Clarify Project Requirements ✅ Requirements clear: OskarOS Assistant Bot - Python Telegram bot with aiogram, OpenRouter AI, MongoDB Atlas, APScheduler

- [x] Scaffold the Project ✅ Complete project structure created with all modules

- [x] Customize the Project ✅ All modules implemented according to specifications

- [x] Install Required Extensions ✅ Python extension available

- [x] Compile the Project ✅ Dependencies installed and resolved

- [x] Create and Run Task ✅ Task created for running the bot

- [x] Launch the Project ✅ Bot can be launched (requires credentials configuration)

- [x] Ensure Documentation is Complete ✅ README, SETUP.md, and deployment files created

## Project: OskarOS Assistant Bot
- **Type**: Personal AI Second Brain (Telegram + OpenRouter + MongoDB)
- **Language**: Python
- **Framework**: aiogram (Telegram Bot)
- **AI**: Llama 3.3 70B via OpenRouter
- **Database**: MongoDB Atlas
- **Scheduler**: APScheduler
- **Deployment**: Render/DigitalOcean/Vercel Cron

## Key Features:
- Natural language reminder interpretation
- Smart note classification
- Automated pre-reminders (7d, 2d, 1d, day)
- Voice message support (future)
- Weekly AI summaries
- Semantic search

## Architecture:
- `telegram_interface`: Bot commands and message handling
- `ai_interpreter`: OpenRouter Llama 3.3 integration
- `reminder_manager`: Reminder creation and management
- `note_manager`: Note storage and classification
- `scheduler_service`: Background reminder notifications
- `memory_index`: User context and habits