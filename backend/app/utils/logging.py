"""
Logging configuration and utilities
"""
import sys
from loguru import logger
from core.config import settings


def setup_logging():
    """Configure logging for the application"""
    
    # Remove default logger
    logger.remove()
    
    # Add console logger with custom format
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # Add file logger for errors
    logger.add(
        "logs/error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    # Add file logger for all logs
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        rotation="50 MB",
        retention="7 days",
        compression="zip"
    )
    
    logger.info("Logging configured successfully")


def get_logger(name: str):
    """Get a logger instance for a specific module"""
    return logger.bind(name=name)
