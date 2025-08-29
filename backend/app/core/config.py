"""
Core configuration settings for the application
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    app_name: str = "SixtyFour Workflow Engine"
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Server Configuration
    host: str = os.getenv("BACKEND_HOST", "localhost")
    port: int = int(os.getenv("BACKEND_PORT", 8000))
    
    # Sixtyfour API Configuration
    sixtyfour_api_key: Optional[str] = os.getenv("SIXTYFOUR_API_KEY")
    sixtyfour_org_id: Optional[str] = os.getenv("SIXTYFOUR_ORG_ID")
    sixtyfour_base_url: str = os.getenv("SIXTYFOUR_BASE_URL", "https://api.sixtyfour.ai")
    
    # File Storage Configuration
    upload_folder: str = os.getenv("UPLOAD_FOLDER", "./uploads")
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB
    
    # Redis Configuration (for job queue)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Supabase Configuration
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_key: Optional[str] = os.getenv("SUPABASE_KEY")
    supabase_service_key: Optional[str] = os.getenv("SUPABASE_SERVICE_KEY")
    
    # Database Configuration (if using local PostgreSQL)
    database_url: Optional[str] = os.getenv("DATABASE_URL")
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    model_config = {
        "env_file": str(Path(__file__).parent.parent.parent.parent / ".env"),
        "case_sensitive": False,
        "extra": "ignore"  # Allow extra fields in .env file
    }


# Global settings instance
settings = Settings()
