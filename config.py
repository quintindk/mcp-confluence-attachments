from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging
from logging.config import dictConfig

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 8080
DEFAULT_LOG_LEVEL = 'INFO'

class Settings(BaseSettings):
    # Server settings
    MCP_HOST: str = Field(
        default=DEFAULT_HOST,
        description='IP address to listen on'
    )

    MCP_PORT: int = Field(
        default=DEFAULT_PORT,
        description='Server port',
        gt=0,
        lt=65536
    )

    MCP_DEBUG: bool = Field(
        default=False,
        description='Enable debug mode'
    )

    MCP_RELOAD: bool = Field(
        default=False,
        description='Enable auto-reload in development'
    )

    TRANSPORT: str = Field(
        default='stdio',
        description='Transport mode (stdio, sse, http)'
    )

    LOG_LEVEL: str = Field(
        default=DEFAULT_LOG_LEVEL,
        description='Logging level'
    )

    # Confluence settings
    CONFLUENCE_URL: str = Field(
        default='',
        description='Confluence instance URL'
    )

    CONFLUENCE_PERSONAL_TOKEN: str = Field(
        default='',
        description='Confluence personal access token'
    )

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
        validate_default=True,
    )

    @field_validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        if not v:
            return DEFAULT_LOG_LEVEL
        v = v.upper()
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v not in valid_levels:
            raise ValueError(f'Invalid log level: {v}')
        return v

    @field_validator('TRANSPORT')
    def validate_transport(cls, v):
        if not v:
            return 'stdio'
        v = str(v).strip().lower()
        valid_transports = {'stdio', 'sse', 'http'}
        if v not in valid_transports:
            raise ValueError(f'Invalid transport: {v}')
        return v

    @field_validator('CONFLUENCE_URL')
    def validate_confluence_url(cls, v):
        if v:
            v = v.rstrip('/')
        return v

try:
    settings = Settings()
except Exception as e:
    print(f"Configuration error: {e}")
    raise

logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default' if settings.MCP_DEBUG else 'simple',
            'stream': 'ext://sys.stderr',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': settings.LOG_LEVEL,
            'propagate': True
        },
    }
}

dictConfig(logging_config)
logger = logging.getLogger(__name__)
