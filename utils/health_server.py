"""
Health check server para DigitalOcean App Platform
"""

import asyncio
from aiohttp import web, Application
from loguru import logger


class HealthServer:
    """Servidor simple para health checks"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.app = None
        self.runner = None
        self.site = None
    
    async def health_handler(self, request):
        """Endpoint de health check"""
        return web.json_response({
            "status": "healthy", 
            "service": "oskaros-bot",
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def start(self):
        """Iniciar servidor de health check"""
        try:
            self.app = Application()
            self.app.router.add_get('/health', self.health_handler)
            self.app.router.add_get('/', self.health_handler)  # Root también
            
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, '0.0.0.0', self.port)
            await self.site.start()
            
            logger.info(f"🩺 Health server iniciado en puerto {self.port}")
            
        except Exception as e:
            logger.error(f"❌ Error iniciando health server: {e}")
    
    async def stop(self):
        """Detener servidor"""
        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            logger.info("🩺 Health server detenido")
        except Exception as e:
            logger.error(f"❌ Error deteniendo health server: {e}")