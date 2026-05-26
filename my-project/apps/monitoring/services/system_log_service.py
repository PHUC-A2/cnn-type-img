"""Ghi log hệ thống — DB + loguru."""

import traceback
from typing import Any, Optional

from apps.monitoring.repositories.log_repository import SystemLogRepository
from core.enums.log_level import LogLevel


class SystemLogService:
    """Service ghi system_logs kèm loguru."""

    @staticmethod
    def _write_loguru(level: LogLevel, source: str, message: str) -> None:
        try:
            from loguru import logger
            text = f'[{source}] {message}'
            if level == LogLevel.ERROR:
                logger.error(text)
            elif level == LogLevel.WARNING:
                logger.warning(text)
            else:
                logger.info(text)
        except ImportError:
            pass

    @staticmethod
    def log(
        level: LogLevel,
        source: str,
        message: str,
        stack_trace: str = '',
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Ghi log vào DB và loguru."""
        SystemLogService._write_loguru(level, source, message)
        try:
            SystemLogRepository.create(
                level=level.value,
                source=source,
                message=message,
                stack_trace=stack_trace or None,
                context_json=context or None,
            )
        except Exception:
            pass

    @staticmethod
    def info(source: str, message: str, context: Optional[dict] = None) -> None:
        SystemLogService.log(LogLevel.INFO, source, message, context=context)

    @staticmethod
    def warning(source: str, message: str, context: Optional[dict] = None) -> None:
        SystemLogService.log(LogLevel.WARNING, source, message, context=context)

    @staticmethod
    def error(
        source: str,
        message: str,
        exc: Optional[BaseException] = None,
        context: Optional[dict] = None,
    ) -> None:
        stack = ''
        if exc:
            stack = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        SystemLogService.log(LogLevel.ERROR, source, message, stack_trace=stack, context=context)
