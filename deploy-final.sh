#!/bin/bash

# 🚀 OskarOS Final Deployment Script for DigitalOcean
# IP: 134.199.196.68
# Date: 7 October 2025

set -e

echo "🚀 OSKAROS ASSISTANT BOT - FINAL DIGITALOCEAN DEPLOYMENT"
echo "========================================================"
echo "🌐 Target IP: 134.199.196.68"
echo "📅 Date: $(date '+%Y-%m-%d %H:%M')"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Step 1: Final Pre-deployment Tests
print_info "Ejecutando tests finales..."
if python test_comprehensive_final.py | grep -q "🎯 TASA DE ÉXITO: 100.0%"; then
    print_success "Tests finales: 100% SUCCESS"
else
    print_error "Tests fallaron - Deployment abortado"
    exit 1
fi

# Step 2: Git commit and push
print_info "Preparando código para deployment..."
git add .
if ! git diff --staged --quiet; then
    git commit -m "🚀 Final DigitalOcean deployment - IP 134.199.196.68 - $(date '+%Y-%m-%d %H:%M')"
    print_success "Cambios commitados"
else
    print_info "No hay cambios nuevos para commitear"
fi

if git push origin main; then
    print_success "Código subido a GitHub: OskarFate/oskar-os-bot"
else
    print_error "Error subiendo a GitHub"
    exit 1
fi

# Step 3: Verify files for deployment
print_info "Verificando archivos de deployment..."

required_files=(
    "Dockerfile"
    "digitalocean-app-final.yaml"
    "main.py"
    "requirements.txt"
    "bot/telegram_interface.py"
    "bot/ai_interpreter.py"
    "bot/reminder_manager.py"
    "utils/health_server.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_success "✓ $file"
    else
        print_error "✗ $file - FALTA"
        exit 1
    fi
done

# Step 4: Display deployment information
echo ""
print_info "📋 INFORMACIÓN DE DEPLOYMENT:"
echo "================================"
echo "🏷️  App Name: oskaros-assistant-bot"
echo "🌐 IP Address: 134.199.196.68"
echo "📍 Region: NYC1 (New York)"
echo "💰 Plan: Basic XXS (\$5/month)"
echo "📦 Repository: OskarFate/oskar-os-bot"
echo "🌿 Branch: main"
echo "🔄 Auto-deploy: Enabled"
echo ""

# Step 5: Environment variables template
print_info "📝 Variables de entorno requeridas:"
echo "======================================"
cat << 'EOF'
TELEGRAM_BOT_TOKEN=tu_bot_token_de_botfather
OPENROUTER_API_KEY=tu_api_key_de_openrouter  
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DB_NAME=oskaros_bot
TIMEZONE=America/Mexico_City
LOG_LEVEL=INFO
ENVIRONMENT=production
PORT=8080
EOF

echo ""

# Step 6: Deployment commands
print_info "🚀 Comandos para deployment final:"
echo "=================================="
echo ""
echo "1️⃣  Instalar doctl (si no está instalado):"
echo "   wget https://github.com/digitalocean/doctl/releases/latest/download/doctl-1.105.0-linux-amd64.tar.gz"
echo "   tar xf *.tar.gz && sudo mv doctl /usr/local/bin"
echo ""
echo "2️⃣  Autenticar con DigitalOcean:"
echo "   doctl auth init"
echo ""
echo "3️⃣  Crear la aplicación:"
echo "   doctl apps create digitalocean-app-final.yaml"
echo ""
echo "4️⃣  Obtener ID de la app:"
echo "   doctl apps list"
echo ""
echo "5️⃣  Configurar secrets en el dashboard:"
echo "   https://cloud.digitalocean.com/apps"
echo "   → Seleccionar: oskaros-assistant-bot"
echo "   → Settings → Environment Variables"
echo "   → Agregar como ENCRYPTED:"
echo "     • TELEGRAM_BOT_TOKEN"
echo "     • OPENROUTER_API_KEY"
echo "     • MONGODB_URI"
echo ""
echo "6️⃣  Monitorear deployment:"
echo "   doctl apps logs [APP_ID] --follow"
echo ""
echo "7️⃣  Verificar health check:"
echo "   curl https://oskaros-assistant-bot-[random].ondigitalocean.app/health"
echo ""

# Step 7: Expected results
print_info "📊 Resultados esperados:"
echo "========================"
echo "✅ URL de la app: https://oskaros-assistant-bot-[random].ondigitalocean.app"
echo "✅ Health check: https://[tu-app].ondigitalocean.app/health"
echo "✅ Tiempo de deployment: 5-10 minutos"
echo "✅ Costo mensual: \$5 USD"
echo "✅ Uptime esperado: 99.9%"
echo "✅ Capacidad: 50+ usuarios concurrentes"
echo ""

# Step 8: Post-deployment checklist
print_info "📋 Checklist post-deployment:"
echo "============================"
echo "□ Health check responde OK"
echo "□ Bot responde a /start"
echo "□ Comandos básicos funcionan"
echo "□ AI interpreta correctamente"
echo "□ Base de datos conectada"
echo "□ Logs sin errores"
echo "□ Alertas configuradas"
echo ""

print_success "🎉 DEPLOYMENT PREPARATION COMPLETED!"
print_info "📧 Contacto: OskarFate/oskar-os-bot"
print_info "🔧 Support: GitHub Issues"
print_info "💡 Features: 100% tested and ready"

echo ""
echo "🎯 NEXT STEP: Run the doctl commands above to deploy!"
echo "⏱️  Estimated deployment time: 5-10 minutes"
echo "💰 Monthly cost: \$5 USD"