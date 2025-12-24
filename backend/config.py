"""
Configuration management for Oslo Commute Time Optimizer.
Centralizes all configuration settings with defaults and environment variable overrides.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""

    # API Keys
    GOOGLE_MAPS_API_KEY: Optional[str] = os.getenv('GOOGLE_MAPS_API_KEY')
    DATEX_USERNAME: Optional[str] = os.getenv('DATEX_USERNAME')
    DATEX_PASSWORD: Optional[str] = os.getenv('DATEX_PASSWORD')

    # Server Configuration
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', '8000'))
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'

    # Database Configuration
    DB_PATH: str = os.getenv('DB_PATH', os.path.join(
        os.path.dirname(__file__), '..', 'data', 'commute.db'
    ))

    # DATEX Collection Settings
    DATEX_POLL_INTERVAL_SECONDS: int = int(os.getenv('DATEX_POLL_INTERVAL_SECONDS', '300'))  # 5 minutes
    DATEX_TIMEOUT_SECONDS: int = int(os.getenv('DATEX_TIMEOUT_SECONDS', '30'))
    DATEX_AUTO_START: bool = os.getenv('DATEX_AUTO_START', 'false').lower() == 'true'

    # Analysis Settings
    ANALYSIS_START_HOUR: int = int(os.getenv('ANALYSIS_START_HOUR', '6'))
    ANALYSIS_END_HOUR: int = int(os.getenv('ANALYSIS_END_HOUR', '10'))
    ANALYSIS_INTERVAL_MINUTES: int = int(os.getenv('ANALYSIS_INTERVAL_MINUTES', '15'))
    MIN_SAMPLES_FOR_QUALITY: int = int(os.getenv('MIN_SAMPLES_FOR_QUALITY', '3'))

    # Google Maps Settings
    GOOGLE_MAPS_TIMEOUT_SECONDS: int = int(os.getenv('GOOGLE_MAPS_TIMEOUT_SECONDS', '10'))
    GOOGLE_MAPS_TRAFFIC_MODEL: str = os.getenv('GOOGLE_MAPS_TRAFFIC_MODEL', 'best_guess')

    # Oslo Area Filtering (for DATEX segments)
    OSLO_KEYWORDS: list = [
        'oslo', 'e18', 'e6', 'ring 3', 'rv 4', 'lysaker', 'sandvika',
        'asker', 'drammen', 'lørenskog', 'romerike', 'ski', 'lillestrøm'
    ]

    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: Optional[str] = os.getenv('LOG_FILE')

    # CORS Settings
    CORS_ORIGINS: list = os.getenv('CORS_ORIGINS', '*').split(',')

    @classmethod
    def is_google_maps_configured(cls) -> bool:
        """Check if Google Maps is configured."""
        return bool(cls.GOOGLE_MAPS_API_KEY)

    @classmethod
    def is_datex_configured(cls) -> bool:
        """Check if DATEX is configured."""
        return bool(cls.DATEX_USERNAME and cls.DATEX_PASSWORD)

    @classmethod
    def get_summary(cls) -> dict:
        """Get configuration summary (excluding sensitive data)."""
        return {
            'google_maps_configured': cls.is_google_maps_configured(),
            'datex_configured': cls.is_datex_configured(),
            'datex_auto_start': cls.DATEX_AUTO_START,
            'datex_poll_interval': cls.DATEX_POLL_INTERVAL_SECONDS,
            'analysis_hours': f"{cls.ANALYSIS_START_HOUR:02d}:00-{cls.ANALYSIS_END_HOUR:02d}:00",
            'analysis_interval': f"{cls.ANALYSIS_INTERVAL_MINUTES} minutes",
            'debug_mode': cls.DEBUG,
            'host': cls.HOST,
            'port': cls.PORT,
        }


# Singleton instance
config = Config()
