# 🔒 SECURITY GUIDELINES - OskarOS Assistant Bot

## ⚠️ VARIABLES DE ENTORNO CRÍTICAS

**NUNCA subir al repositorio:**

- `TELEGRAM_BOT_TOKEN` - Token del bot de Telegram
- `OPENROUTER_API_KEY` - Clave API de OpenRouter
- `MONGODB_URI` - String de conexión a MongoDB
- `ICLOUD_EMAIL` - Email de iCloud
- `ICLOUD_PASSWORD` - Contraseña de aplicación de iCloud

## ✅ ARCHIVOS DE SEGURIDAD

### `.gitignore` configurado para excluir:
- `.env*` (todas las variantes)
- `*.key`, `*.pem`, `*.p12`
- `credentials.json`
- `secrets.yaml`
- Archivos de base de datos

### `.env.example` disponible con:
- Plantilla de todas las variables necesarias
- Valores de ejemplo (NO reales)
- Instrucciones de configuración

## 🚀 DEPLOYMENT SEGURO

### Para Render.com / DigitalOcean / Vercel:
1. **NO subir archivo `.env`**
2. Configurar variables en el panel web
3. Usar secrets management del proveedor
4. Verificar que `.env` está en `.gitignore`

### Para desarrollo local:
1. Copiar `.env.example` a `.env`
2. Rellenar con valores reales
3. Verificar que `.env` NO está tracked por git

## 🔍 VERIFICACIÓN

```bash
# Verificar que .env no está tracked
git status | grep .env

# Debería mostrar solo:
# .env.example (tracked)
# .env (untracked o no aparecer)
```

## 📋 CHECKLIST DE SEGURIDAD

- [x] `.env` en `.gitignore`
- [x] `.env.example` configurado
- [x] Variables reales eliminadas del código
- [x] Documentación de deployment actualizada
- [x] Credenciales removidas de archivos de configuración
- [x] GitGuardian patterns implementados

## 🛡️ BUENAS PRÁCTICAS

1. **Rotación de claves**: Cambiar claves periódicamente
2. **Permisos mínimos**: Solo los necesarios
3. **Monitoreo**: Revisar logs de acceso
4. **Backup seguro**: Guardar credenciales en manager de passwords

---

**IMPORTANTE**: Si accidentalmente subes credenciales:
1. Regenerar TODAS las claves inmediatamente
2. Revisar logs de acceso
3. Actualizar deployment con nuevas claves