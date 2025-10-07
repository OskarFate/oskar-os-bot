"""
Sistema de logging con loguru
"""

import sys
from pathlib import Path
from loguru import logger
from config.settings import settings


def setup_logger():
    """Configurar sistema de logging"""
    
    # Remover logger por defecto
    logger.remove()
    
    # Configurar formato
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Logger para consola
    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Logger para archivo (solo en producción)
    if settings.is_production:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Archivo de logs rotativo
        logger.add(
            log_dir / "oskaros_bot.log",
            format=log_format,
            level="INFO",
            rotation="1 day",
            retention="7 days",
            compression="gz",
            backtrace=True,
            diagnose=False  # No incluir información sensible en archivos
        )
        
        # Archivo separado para errores
        logger.add(
            log_dir / "errors.log",
            format=log_format,
            level="ERROR",
            rotation="1 week",
            retention="30 days",
            compression="gz",
            backtrace=True,
            diagnose=False
        )
    
    logger.info(f"📊 Logger configurado - Nivel: {settings.LOG_LEVEL}")


def get_logger(name: str):
    """Obtener logger con nombre específico"""
    return logger.bind(name=name)