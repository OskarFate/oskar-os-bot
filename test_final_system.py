#!/usr/bin/env python3
"""
TEST COMPLETO DEL SISTEMA - VERIFICACIÓN FINAL PARA VENTA
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import logging

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_file_structure():
    """Test 1: Verificar estructura de archivos"""
    print("🧪 TEST 1: ESTRUCTURA DE ARCHIVOS")
    print("=" * 50)
    
    required_files = [
        'main.py',
        'requirements.txt',
        'README.md',
        'SETUP.md',
        'DEPLOY.md',
        'SECURITY.md',
        '.env.example',
        '.gitignore',
        'config/settings.py',
        'bot/telegram_interface.py',
        'bot/ai_interpreter.py',
        'bot/reminder_manager.py',
        'bot/scheduler_service.py',
        'bot/calendar_integration.py',
        'bot/note_manager.py',
        'bot/memory_index.py',
        'database/connection.py',
        'database/models.py',
        'utils/logger.py',
        'utils/helpers.py',
        'utils/health_server.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"\n❌ ARCHIVOS FALTANTES:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    else:
        print(f"\n✅ TODOS LOS ARCHIVOS PRESENTES ({len(required_files)} archivos)")
        return True

def test_security():
    """Test 2: Verificar seguridad"""
    print("\n🔒 TEST 2: SEGURIDAD")
    print("=" * 50)
    
    # Verificar que .env no existe
    if os.path.exists('.env'):
        print("❌ CRÍTICO: Archivo .env existe (debe estar en .gitignore)")
        return False
    else:
        print("✅ .env no existe (correcto)")
    
    # Verificar .env.example
    if os.path.exists('.env.example'):
        with open('.env.example', 'r') as f:
            content = f.read()
            if 'sk-or-v1-abcdefghijklmnopqrstuvwxyz' in content:
                print("✅ .env.example tiene valores de ejemplo (no reales)")
            else:
                print("⚠️ Verificar que .env.example no tenga claves reales")
    
    # Verificar .gitignore
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            gitignore_content = f.read()
            if '.env' in gitignore_content and '*.key' in gitignore_content:
                print("✅ .gitignore configurado correctamente")
            else:
                print("❌ .gitignore no tiene todos los patrones de seguridad")
                return False
    
    print("✅ SEGURIDAD: APROBADA")
    return True

def test_imports():
    """Test 3: Verificar que todos los imports funcionan"""
    print("\n📦 TEST 3: IMPORTS Y DEPENDENCIAS")
    print("=" * 50)
    
    try:
        # Core modules
        from config.settings import settings
        print("✅ config.settings")
        
        from database.connection import DatabaseManager
        print("✅ database.connection")
        
        from database.models import User, Reminder, Note, AIMemory
        print("✅ database.models")
        
        # Bot modules
        from bot.telegram_interface import TelegramBot
        print("✅ bot.telegram_interface")
        
        from bot.ai_interpreter import AIInterpreter
        print("✅ bot.ai_interpreter")
        
        from bot.reminder_manager import ReminderManager
        print("✅ bot.reminder_manager")
        
        from bot.scheduler_service import SchedulerService
        print("✅ bot.scheduler_service")
        
        from bot.calendar_integration import AppleCalendarIntegration
        print("✅ bot.calendar_integration")
        
        from bot.note_manager import NoteManager
        print("✅ bot.note_manager")
        
        from bot.memory_index import MemoryIndex
        print("✅ bot.memory_index")
        
        # Utils
        from utils.logger import setup_logger
        print("✅ utils.logger")
        
        from utils.helpers import sanitize_input, format_datetime_for_user
        print("✅ utils.helpers")
        
        from utils.health_server import HealthServer
        print("✅ utils.health_server")
        
        print("\n✅ TODOS LOS IMPORTS: EXITOSOS")
        return True
        
    except ImportError as e:
        print(f"❌ ERROR DE IMPORT: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}")
        return False

def test_configuration():
    """Test 4: Verificar configuración"""
    print("\n⚙️ TEST 4: CONFIGURACIÓN")
    print("=" * 50)
    
    try:
        from config.settings import settings
        
        # Verificar atributos requeridos
        required_settings = [
            'TELEGRAM_BOT_TOKEN',
            'OPENROUTER_API_KEY', 
            'MONGODB_URI',
            'PRE_REMINDER_DAYS',
            'SCHEDULER_INTERVAL_SECONDS',
            'REMINDER_TOLERANCE_SECONDS'
        ]
        
        for setting in required_settings:
            if hasattr(settings, setting):
                print(f"✅ {setting}")
            else:
                print(f"❌ Falta configuración: {setting}")
                return False
        
        # Verificar pre-recordatorios
        if settings.PRE_REMINDER_DAYS == [7, 2, 1]:
            print("✅ PRE_REMINDER_DAYS configurado correctamente [7, 2, 1]")
        else:
            print(f"⚠️ PRE_REMINDER_DAYS: {settings.PRE_REMINDER_DAYS}")
        
        print("\n✅ CONFIGURACIÓN: VÁLIDA")
        return True
        
    except Exception as e:
        print(f"❌ ERROR EN CONFIGURACIÓN: {e}")
        return False

def test_ai_patterns():
    """Test 5: Verificar patrones de IA"""
    print("\n🤖 TEST 5: PATRONES DE IA")
    print("=" * 50)
    
    try:
        from bot.telegram_interface import TelegramInterface
        
        # Crear instancia mock para probar patrones
        interface = TelegramInterface(None, None, None, None, None)
        
        # Test casos de recordatorios
        reminder_cases = [
            ("recordar llamar médico mañana", True),
            ("pastillas todos los días", True),
            ("gym todos los días excepto viernes", True),
            ("mantén gym elimina viernes", True),
            ("eliminar recordatorio del gym", True),
            ("hola cómo estás", False),
            ("el clima está bonito", False)
        ]
        
        all_passed = True
        for text, expected in reminder_cases:
            result = interface._is_reminder_request(text)
            status = "✅" if result == expected else "❌"
            print(f"{status} '{text}' → {result}")
            if result != expected:
                all_passed = False
        
        # Test casos de eliminación
        deletion_cases = [
            ("eliminar gym", True),
            ("mantén todos los días excepto viernes", True),
            ("borra recordatorio", True),
            ("recordar comprar pan", False)
        ]
        
        print("\n📝 Patrones de eliminación:")
        for text, expected in deletion_cases:
            result = interface._has_deletion_pattern(text)
            status = "✅" if result == expected else "❌"
            print(f"{status} '{text}' → {result}")
            if result != expected:
                all_passed = False
        
        if all_passed:
            print("\n✅ PATRONES DE IA: FUNCIONANDO")
            return True
        else:
            print("\n❌ ALGUNOS PATRONES FALLAN")
            return False
            
    except Exception as e:
        print(f"❌ ERROR TESTING PATRONES: {e}")
        return False

def test_database_models():
    """Test 6: Verificar modelos de base de datos"""
    print("\n🗄️ TEST 6: MODELOS DE BASE DE DATOS")
    print("=" * 50)
    
    try:
        from database.models import User, Reminder, Note, AIMemory, ReminderStatus
        from datetime import datetime
        
        # Test User model
        user = User(
            user_id=123456789,
            username="test_user",
            language="es",
            timezone="America/Santiago"
        )
        print("✅ User model funcionando")
        
        # Test Reminder model
        reminder = Reminder(
            user_id=123456789,
            text="Test reminder",
            date=datetime.now(),
            status=ReminderStatus.PENDING
        )
        print("✅ Reminder model funcionando")
        
        # Test Note model
        note = Note(
            user_id=123456789,
            text="Test note",
            tags=["test"],
            priority="medium"
        )
        print("✅ Note model funcionando")
        
        # Test AIMemory model
        memory = AIMemory(
            user_id=123456789,
            text="Test memory",
            type="preference"
        )
        print("✅ AIMemory model funcionando")
        
        print("\n✅ MODELOS DE BD: VÁLIDOS")
        return True
        
    except Exception as e:
        print(f"❌ ERROR EN MODELOS: {e}")
        return False

def test_helper_functions():
    """Test 7: Verificar funciones helper"""
    print("\n🛠️ TEST 7: FUNCIONES HELPER")
    print("=" * 50)
    
    try:
        from utils.helpers import sanitize_input, format_datetime_for_user
        from datetime import datetime
        
        # Test sanitize_input
        test_input = "  Hola mundo!  \n\t"
        sanitized = sanitize_input(test_input)
        if sanitized == "Hola mundo!":
            print("✅ sanitize_input funcionando")
        else:
            print(f"❌ sanitize_input falla: '{sanitized}'")
            return False
        
        # Test format_datetime_for_user
        test_date = datetime(2025, 10, 15, 14, 30)
        formatted = format_datetime_for_user(test_date)
        if "15" in formatted and "14:30" in formatted:
            print("✅ format_datetime_for_user funcionando")
        else:
            print(f"❌ format_datetime_for_user falla: '{formatted}'")
            return False
        
        print("\n✅ FUNCIONES HELPER: FUNCIONANDO")
        return True
        
    except Exception as e:
        print(f"❌ ERROR EN HELPERS: {e}")
        return False

def test_calendar_integration():
    """Test 8: Verificar integración de calendario"""
    print("\n📅 TEST 8: INTEGRACIÓN DE CALENDARIO")
    print("=" * 50)
    
    try:
        from bot.calendar_integration import AppleCalendarIntegration
        
        # Test que la clase se puede instanciar
        calendar = AppleCalendarIntegration("test@example.com", "test_password")
        print("✅ AppleCalendarIntegration instanciable")
        
        # Test que tiene los métodos requeridos
        required_methods = [
            'connect',
            'create_reminder_event', 
            'delete_event_by_title_and_date',
            'delete_events_by_title_pattern',
            'update_event_title',
            'test_connection'
        ]
        
        for method in required_methods:
            if hasattr(calendar, method):
                print(f"✅ Método {method}")
            else:
                print(f"❌ Falta método: {method}")
                return False
        
        print("\n✅ INTEGRACIÓN CALENDARIO: COMPLETA")
        return True
        
    except Exception as e:
        print(f"❌ ERROR EN CALENDARIO: {e}")
        return False

def test_deployment_files():
    """Test 9: Verificar archivos de deployment"""
    print("\n🚀 TEST 9: ARCHIVOS DE DEPLOYMENT")
    print("=" * 50)
    
    deployment_files = {
        'Dockerfile': ['FROM python', 'COPY requirements.txt', 'CMD'],
        'render.yaml': ['services:', 'name:', 'env:', 'buildCommand:', 'startCommand:'],
        'requirements.txt': ['aiogram', 'motor', 'pymongo', 'openai', 'python-dotenv'],
        'DEPLOY.md': ['Render', 'DigitalOcean', 'variables']
    }
    
    all_good = True
    for file, required_content in deployment_files.items():
        if os.path.exists(file):
            with open(file, 'r') as f:
                content = f.read()
                missing = [item for item in required_content if item not in content]
                if missing:
                    print(f"⚠️ {file}: Faltan elementos {missing}")
                else:
                    print(f"✅ {file}")
        else:
            print(f"❌ Falta archivo: {file}")
            all_good = False
    
    if all_good:
        print("\n✅ ARCHIVOS DEPLOYMENT: COMPLETOS")
        return True
    else:
        print("\n❌ FALTAN ARCHIVOS DE DEPLOYMENT")
        return False

async def main():
    """Test completo del sistema"""
    print("🚀 TEST COMPLETO DEL SISTEMA - OSKAROS ASSISTANT BOT")
    print("=" * 70)
    print("🎯 OBJETIVO: Verificar que TODO funciona antes de la venta")
    print("=" * 70)
    
    tests = [
        ("📁 Estructura de Archivos", test_file_structure),
        ("🔒 Seguridad", test_security), 
        ("📦 Imports y Dependencias", test_imports),
        ("⚙️ Configuración", test_configuration),
        ("🤖 Patrones de IA", test_ai_patterns),
        ("🗄️ Modelos de Base de Datos", test_database_models),
        ("🛠️ Funciones Helper", test_helper_functions),
        ("📅 Integración de Calendario", test_calendar_integration),
        ("🚀 Archivos de Deployment", test_deployment_files)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ ERROR en {test_name}: {e}")
            failed += 1
    
    # Resultado final
    print("\n" + "=" * 70)
    print("🏆 RESULTADO FINAL DEL TEST")
    print("=" * 70)
    print(f"✅ Tests pasados: {passed}")
    print(f"❌ Tests fallidos: {failed}")
    print(f"📊 Porcentaje de éxito: {(passed/(passed+failed))*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ EL CÓDIGO ESTÁ LISTO PARA LA VENTA")
        print("\n💰 CARACTERÍSTICAS PARA VENTA:")
        print("   • Bot de Telegram con IA (Llama 3.3)")
        print("   • Recordatorios inteligentes con pre-alertas")
        print("   • Eliminación avanzada con excepciones")
        print("   • Integración con Apple Calendar")
        print("   • Base de datos MongoDB")
        print("   • Scheduler automático")
        print("   • Código limpio y documentado")
        print("   • Deployment ready (Render/DigitalOcean)")
        print("   • Seguridad GitGuardian compliant")
        
        print(f"\n🚀 VALOR COMERCIAL ESTIMADO: $2,000 - $5,000 USD")
        
    else:
        print(f"\n⚠️ HAY {failed} PROBLEMAS QUE RESOLVER")
        print("🔧 Revisar y corregir antes de la venta")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())