"""
Rift Configuration
Loads and validates environment configuration
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment"""

    # DigitalOcean
    digitalocean_api_token: str
    do_spaces_access_key: Optional[str] = None
    do_spaces_secret_key: Optional[str] = None
    do_spaces_region: str = "nyc3"

    # Gradient AI Agents
    monitor_agent_endpoint: str
    monitor_agent_key: str
    monitor_agent_id: str

    diagnostic_agent_endpoint: str
    diagnostic_agent_key: str
    diagnostic_agent_id: str

    remediation_agent_endpoint: str
    remediation_agent_key: str
    remediation_agent_id: str

    provisioner_agent_endpoint: str
    provisioner_agent_key: str
    provisioner_agent_id: str

    # Knowledge Base
    knowledge_base_id: str

    # Monitoring
    prometheus_url: str = "http://localhost:9090"
    prometheus_user: Optional[str] = None
    prometheus_password: Optional[str] = None

    # Terraform
    terraform_workspace: str = "rift"
    terraform_state_bucket: str = "rift-tfstate"

    # Application
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000
    log_level: str = "INFO"
    environment: str = "development"

    # Security
    api_secret_key: str
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # Demo & Automation
    demo_mode: bool = True
    auto_remediation_enabled: bool = True
    confidence_threshold: float = 0.85
    max_cost_auto_approve: float = 50.00

    # Droplet IPs (optional, filled after creation)
    control_plane_ip: Optional[str] = None
    web_app_ip: Optional[str] = None
    api_server_ip: Optional[str] = None
    prometheus_ip: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance"""
    global settings
    if settings is None:
        settings = Settings()
    return settings


def reload_settings() -> Settings:
    """Force reload settings from environment"""
    global settings
    settings = Settings()
    return settings
