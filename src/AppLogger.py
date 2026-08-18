"""
AppLogger: A thread-safe Python logging singleton module using standard library `logging`.
"""

import logging
import logging.handlers
import os
import socket
import sys
import threading
from typing import Optional, Union


class AppLogger:
    """Thread-safe Singleton wrapper for Python's standard `logging.Logger`."""

    _instance: Optional["AppLogger"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(AppLogger, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        name: str = "app_logger",
        level: Union[int, str] = logging.INFO,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        stdout: bool = True,
        stderr: bool = False,
        file_path: Optional[str] = None,
        syslog_host: Optional[str] = None,
        syslog_port: int = 514,
        syslog_facility: int = logging.handlers.SysLogHandler.LOG_USER,
    ):
        if not getattr(self, "_initialized", False):
            with self._lock:
                if not getattr(self, "_initialized", False):
                    self._logger = logging.getLogger(name)
                    self._initialized = True

        # Always reconfigure when instantiated with explicit arguments
        if file_path is not None or syslog_host is not None or level != logging.INFO or not stdout or stderr:
            self.configure(
                level=level,
                fmt=fmt,
                datefmt=datefmt,
                stdout=stdout,
                stderr=stderr,
                file_path=file_path,
                syslog_host=syslog_host,
                syslog_port=syslog_port,
                syslog_facility=syslog_facility,
            )

    def configure(
        self,
        level: Union[int, str] = logging.INFO,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        stdout: bool = True,
        stderr: bool = False,
        file_path: Optional[str] = None,
        syslog_host: Optional[str] = None,
        syslog_port: int = 514,
        syslog_facility: int = logging.handlers.SysLogHandler.LOG_USER,
    ) -> None:
        """
        Configure or update the underlying logger's level, format, and destination handlers.
        """
        if isinstance(level, str):
            resolved_level = logging.getLevelName(level.upper())
            if isinstance(resolved_level, int):
                level = resolved_level
            else:
                level = logging.INFO

        self._logger.setLevel(level)

        # Properly close and remove existing handlers to avoid duplicates or resource leaks
        if self._logger.hasHandlers():
            for handler in self._logger.handlers[:]:
                try:
                    handler.close()
                except Exception:
                    pass
            self._logger.handlers.clear()

        self._logger.propagate = False

        if not fmt:
            fmt = "[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] - %(message)s"

        formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

        # 1. Stdout Destination
        if stdout:
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setFormatter(formatter)
            stdout_handler.setLevel(level)
            self._logger.addHandler(stdout_handler)

        # 2. Stderr Destination
        if stderr:
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setFormatter(formatter)
            stderr_handler.setLevel(level)
            self._logger.addHandler(stderr_handler)

        # 3. Local File Destination
        if file_path:
            dir_name = os.path.dirname(file_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            file_handler = logging.FileHandler(file_path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            self._logger.addHandler(file_handler)

        # 4. Syslog TCP Destination
        if syslog_host:
            try:
                syslog_handler = logging.handlers.SysLogHandler(
                    address=(syslog_host, syslog_port),
                    facility=syslog_facility,
                    socktype=socket.SOCK_STREAM,
                )
                syslog_handler.setFormatter(formatter)
                syslog_handler.setLevel(level)
                self._logger.addHandler(syslog_handler)
            except (OSError, socket.error) as err:
                sys.stderr.write(
                    f"[AppLogger Warning] Could not connect to Syslog TCP server at {syslog_host}:{syslog_port}: {err}\n"
                )

    @classmethod
    def get_logger(cls) -> logging.Logger:
        return cls()._logger

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    def debug(self, msg: str, *args, **kwargs) -> None:
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs) -> None:
        self._logger.exception(msg, *args, **kwargs)


def get_logger() -> logging.Logger:
    return AppLogger.get_logger()