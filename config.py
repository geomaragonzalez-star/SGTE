# config.py
"""Módulo de configuración centralizada para SGTE."""

from pathlib import Path
from dataclasses import dataclass
from loguru import logger

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


@dataclass
class PathsConfig:
    db_path: str
    expedientes_root: str
    templates_path: str
    backup_path: str


@dataclass  
class DatabaseConfig:
    timeout_seconds: int
    max_retries: int
    retry_delay_ms: int


@dataclass
class EmailConfig:
    registro_curricular: str
    send_delay_seconds: int


@dataclass
class AppConfig:
    debug_mode: bool
    log_level: str
    app_name: str
    version: str


class Config:
    """Gestor de configuración singleton."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _get_secret(self, section: str, key: str, default=None):
        if not HAS_STREAMLIT:
            return default
        try:
            return st.secrets[section][key]
        except (KeyError, FileNotFoundError):
            return default
    
    def _load_config(self):
        self.paths = PathsConfig(
            db_path=self._get_secret("paths", "db_path", "./data/sgte.db"),
            expedientes_root=self._get_secret("paths", "expedientes_root", "./data/expedientes"),
            templates_path=self._get_secret("paths", "templates_path", "./templates"),
            backup_path=self._get_secret("paths", "backup_path", "./backups")
        )
        self.database = DatabaseConfig(
            timeout_seconds=self._get_secret("database", "timeout_seconds", 30),
            max_retries=self._get_secret("database", "max_retries", 5),
            retry_delay_ms=self._get_secret("database", "retry_delay_ms", 500)
        )
        self.email = EmailConfig(
            registro_curricular=self._get_secret("email", "registro_curricular", "registro@example.com"),
            send_delay_seconds=self._get_secret("email", "send_delay_seconds", 2)
        )
        self.app = AppConfig(
            debug_mode=self._get_secret("app", "debug_mode", True),
            log_level=self._get_secret("app", "log_level", "DEBUG"),
            app_name=self._get_secret("app", "app_name", "SGTE"),
            version=self._get_secret("app", "version", "2.0.0")
        )
        self._setup_logging()
    
    def _setup_logging(self):
        import sys
        logger.remove()
        logger.add(sys.stderr, level=self.app.log_level, colorize=True,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>")
        Path("logs").mkdir(exist_ok=True)
        logger.add("logs/sgte_{time:YYYY-MM-DD}.log", level="DEBUG", rotation="1 day", retention="30 days")
    
    def ensure_directories(self):
        for d in [Path(self.paths.db_path).parent, Path(self.paths.expedientes_root),
                  Path(self.paths.templates_path), Path(self.paths.backup_path), Path("logs")]:
            d.mkdir(parents=True, exist_ok=True)


def get_config() -> Config:
    return Config()
