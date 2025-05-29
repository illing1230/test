"""
Langflow Configuration Module
This module provides configuration utilities for the Langflow application.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import yaml


class LangflowConfig:
    """Configuration manager for Langflow application"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "langflow_config.yaml"
        self.config_data = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file and environment variables"""
        # Load from YAML file if it exists
        if Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config_data = yaml.safe_load(f) or {}
                print(f"✅ Loaded configuration from {self.config_file}")
            except Exception as e:
                print(f"⚠️  Warning: Failed to load config file {self.config_file}: {e}")
                self.config_data = {}
        else:
            print(f"ℹ️  Config file {self.config_file} not found, using defaults")
            self.config_data = {}
        
        # Override with environment variables
        self._load_env_overrides()
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables"""
        env_mappings = {
            'LANGFLOW_HOST': ('server', 'host'),
            'LANGFLOW_PORT': ('server', 'port'),
            'LANGFLOW_DATABASE_URL': ('database', 'url'),
            'LANGFLOW_LOG_LEVEL': ('logging', 'level'),
            'LANGFLOW_DEV_MODE': ('server', 'dev_mode'),
            'LANGFLOW_CONFIG_DIR': ('paths', 'config_dir'),
            'LANGFLOW_AUTO_LOGIN': ('auth', 'auto_login'),
            'LANGFLOW_SUPERUSER_USERNAME': ('auth', 'superuser_username'),
            'LANGFLOW_SUPERUSER_PASSWORD': ('auth', 'superuser_password'),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                if section not in self.config_data:
                    self.config_data[section] = {}
                
                # Convert string values to appropriate types
                if key in ['port']:
                    try:
                        value = int(value)
                    except ValueError:
                        print(f"⚠️  Warning: Invalid port value {value}, using default")
                        continue
                elif key in ['dev_mode', 'auto_login']:
                    value = value.lower() in ('true', '1', 'yes', 'on')
                
                self.config_data[section][key] = value
                print(f"✅ Environment override: {env_var} -> {section}.{key}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config_data.get(section, {}).get(key, default)
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        database_url = self.get('database', 'url')
        
        if not database_url:
            # Try to construct from PostgreSQL environment variables
            pg_host = os.getenv('PGHOST')
            pg_user = os.getenv('PGUSER')
            pg_password = os.getenv('PGPASSWORD')
            pg_database = os.getenv('PGDATABASE')
            pg_port = os.getenv('PGPORT', '5432')
            
            if all([pg_host, pg_user, pg_password, pg_database]):
                database_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
                print("✅ Constructed PostgreSQL URL from environment variables")
            else:
                database_url = "sqlite:///./langflow.db"
                print("ℹ️  Using default SQLite database")
        
        return {
            'url': database_url,
            'pool_size': self.get('database', 'pool_size', 10),
            'max_overflow': self.get('database', 'max_overflow', 20),
            'echo': self.get('database', 'echo', False)
        }
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration"""
        return {
            'host': self.get('server', 'host', '0.0.0.0'),
            'port': self.get('server', 'port', 7860),
            'dev_mode': self.get('server', 'dev_mode', True),
            'reload': self.get('server', 'reload', True),
            'workers': self.get('server', 'workers', 1)
        }
    
    def get_auth_config(self) -> Dict[str, Any]:
        """Get authentication configuration"""
        return {
            'auto_login': self.get('auth', 'auto_login', False),
            'superuser_username': self.get('auth', 'superuser_username', 'admin'),
            'superuser_password': self.get('auth', 'superuser_password', 'admin'),
            'secret_key': self.get('auth', 'secret_key', 'your-secret-key-here'),
            'access_token_expire_minutes': self.get('auth', 'access_token_expire_minutes', 30)
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'level': self.get('logging', 'level', 'INFO'),
            'format': self.get('logging', 'format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            'file': self.get('logging', 'file', 'langflow.log')
        }
    
    def get_paths_config(self) -> Dict[str, Any]:
        """Get paths configuration"""
        return {
            'config_dir': self.get('paths', 'config_dir', '.'),
            'logs_dir': self.get('paths', 'logs_dir', './logs'),
            'temp_dir': self.get('paths', 'temp_dir', './temp'),
            'uploads_dir': self.get('paths', 'uploads_dir', './uploads')
        }
    
    def create_directories(self):
        """Create necessary directories"""
        paths_config = self.get_paths_config()
        
        for dir_type, dir_path in paths_config.items():
            if dir_type.endswith('_dir'):
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {dir_path}")
    
    def validate_config(self) -> bool:
        """Validate the configuration"""
        errors = []
        
        # Validate server config
        server_config = self.get_server_config()
        if not (1 <= server_config['port'] <= 65535):
            errors.append(f"Invalid port: {server_config['port']}")
        
        # Validate database config
        database_config = self.get_database_config()
        if not database_config['url']:
            errors.append("Database URL is required")
        
        if errors:
            print("❌ Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        print("✅ Configuration validation passed")
        return True
    
    def print_config_summary(self):
        """Print a summary of the current configuration"""
        print("\n🔧 Langflow Configuration Summary")
        print("=" * 40)
        
        server_config = self.get_server_config()
        print(f"Server: {server_config['host']}:{server_config['port']}")
        print(f"Dev Mode: {server_config['dev_mode']}")
        
        database_config = self.get_database_config()
        db_type = "PostgreSQL" if database_config['url'].startswith('postgresql') else "SQLite"
        print(f"Database: {db_type}")
        
        auth_config = self.get_auth_config()
        print(f"Auto Login: {auth_config['auto_login']}")
        
        logging_config = self.get_logging_config()
        print(f"Log Level: {logging_config['level']}")
        
        print("=" * 40)


def setup_langflow_config() -> LangflowConfig:
    """Set up and return Langflow configuration"""
    config = LangflowConfig()
    
    # Create necessary directories
    config.create_directories()
    
    # Validate configuration
    if not config.validate_config():
        raise ValueError("Invalid configuration")
    
    # Print summary
    config.print_config_summary()
    
    return config


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = setup_langflow_config()
        print("\n✅ Configuration setup completed successfully!")
    except Exception as e:
        print(f"\n❌ Configuration setup failed: {e}")
