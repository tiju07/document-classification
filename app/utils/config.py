from pydantic_settings import BaseSettings
import yaml
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_title: str = "Document Ingestion System"
    app_version: str = "1.0.0"
    database_url: str = "sqlite:///documents.db"
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def load_yaml_config(self):
        config_path = Path("config/settings.yaml")
        if config_path.exists():
            with open(config_path, "r") as file:
                yaml_config = yaml.safe_load(file)
                self.app_title = yaml_config.get("app", {}).get("title", self.app_title)
                self.app_version = yaml_config.get("app", {}).get("version", self.app_version)
                self.database_url = yaml_config.get("database", {}).get("url", self.database_url)
                self.rabbitmq_host = yaml_config.get("message_bus", {}).get("rabbitmq_host", self.rabbitmq_host)
                self.rabbitmq_port = yaml_config.get("message_bus", {}).get("rabbitmq_port", self.rabbitmq_port)
                self.rabbitmq_user = yaml_config.get("message_bus", {}).get("rabbitmq_user", self.rabbitmq_user)
                self.rabbitmq_password = yaml_config.get("message_bus", {}).get("rabbitmq_password", self.rabbitmq_password)

# Initialize settings
settings = Settings()
settings.load_yaml_config()