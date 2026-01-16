"""
Configuração de logging com loguru para o QuantFund.

Configura logs para arquivo e console com rotação automática.
"""

import sys
from pathlib import Path

from loguru import logger

from jobs.config.settings import LOGS_DIR


def setup_logger(
    log_name: str = "quantfund",
    level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "7 days",
) -> None:
    """
    Configura o logger com arquivo e console.

    Args:
        log_name: Nome base do arquivo de log
        level: Nível mínimo de log ("DEBUG", "INFO", "WARNING", "ERROR")
        rotation: Quando rotacionar (ex: "10 MB", "1 day")
        retention: Quanto tempo manter logs antigos
    """
    # Remove handlers padrão
    logger.remove()

    # Formato para console (colorido)
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Formato para arquivo (sem cores)
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )

    # Handler para console
    logger.add(
        sys.stderr,
        format=console_format,
        level=level,
        colorize=True,
    )

    # Handler para arquivo
    log_file = LOGS_DIR / f"{log_name}.log"
    logger.add(
        log_file,
        format=file_format,
        level=level,
        rotation=rotation,
        retention=retention,
        compression="gz",
        enqueue=True,  # Thread-safe
    )

    logger.info(f"Logger configurado: {log_file}")


def get_component_logger(component: str):
    """
    Retorna logger com contexto de componente.

    Args:
        component: Nome do componente (ex: "fetch_iron_ore")

    Returns:
        Logger com bind do componente
    """
    return logger.bind(component=component)


# Configura logger padrão na importação
setup_logger()
