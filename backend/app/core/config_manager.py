"""
Modular configuration management for the application.
This provides environment-specific configuration and validation.
"""
from typing import Optional, Dict, Any
from functools import lru_cache
from app.config import Settings


class ConfigManager:
    """Manages application configuration with environment-specific settings."""
    
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or Settings()
        self._environment = self._settings.environment
        self._config_cache: Dict[str, Any] = {}
    
    @property
    def environment(self) -> str:
        """Get current environment."""
        return self._environment
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self._environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self._environment == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self._environment == "testing"
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for current environment."""
        cache_key = f"database_{self._environment}"
        if cache_key not in self._config_cache:
            config = {
                "url": self._settings.mongodb_url,
                "database_name": self._settings.mongodb_database,
                "ssl": self._settings.mongodb_ssl,
                "ssl_verify": self._settings.mongodb_ssl_verify,
                "timeout": getattr(self._settings, 'mongodb_timeout', 30000),
                "max_pool_size": getattr(self._settings, 'mongodb_max_pool_size', 10),
                "min_pool_size": getattr(self._settings, 'mongodb_min_pool_size', 1),
            }
            
            # Environment-specific overrides
            if self.is_development:
                config["ssl"] = False
                config["timeout"] = 10000  # Shorter timeout for dev
            elif self.is_production:
                config["ssl"] = True
                config["timeout"] = 30000  # Longer timeout for prod
            elif self.is_testing:
                config["url"] = "mongodb://localhost:27017/test"
                config["ssl"] = False
            
            self._config_cache[cache_key] = config
        
        return self._config_cache[cache_key]
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration for current environment."""
        cache_key = f"openai_{self._environment}"
        if cache_key not in self._config_cache:
            config = {
                "api_key": self._settings.openai_api_key,
                "model": self._settings.openai_model,
                "max_tokens": self._settings.openai_max_tokens,
                "temperature": self._settings.openai_temperature,
                "timeout": self._settings.openai_timeout,
            }
            
            # Environment-specific overrides
            if self.is_development:
                config["temperature"] = 0.7  # More creative in dev
                config["timeout"] = 30  # Shorter timeout for dev
            elif self.is_production:
                config["temperature"] = 0.5  # More consistent in prod
                config["timeout"] = 60  # Longer timeout for prod
            elif self.is_testing:
                config["api_key"] = "test_key"
                config["timeout"] = 5  # Very short timeout for tests
            
            self._config_cache[cache_key] = config
        
        return self._config_cache[cache_key]
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration for current environment."""
        cache_key = f"security_{self._environment}"
        if cache_key not in self._config_cache:
            config = {
                "secret_key": self._settings.secret_key,
                "algorithm": self._settings.algorithm,
                "access_token_expire_minutes": self._settings.access_token_expire_minutes,
                "cors_origins": self._settings.cors_origins,
            }
            
            # Environment-specific overrides
            if self.is_development:
                config["access_token_expire_minutes"] = 60  # Longer tokens in dev
                config["cors_origins"] = ["http://localhost:3000", "http://127.0.0.1:3000"]
            elif self.is_production:
                config["access_token_expire_minutes"] = 30  # Shorter tokens in prod
                config["cors_origins"] = self._settings.cors_origins
            elif self.is_testing:
                config["secret_key"] = "test_secret_key"
                config["access_token_expire_minutes"] = 5  # Very short tokens for tests
            
            self._config_cache[cache_key] = config
        
        return self._config_cache[cache_key]
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration for current environment."""
        cache_key = f"logging_{self._environment}"
        if cache_key not in self._config_cache:
            config = {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": None,
            }
            
            # Environment-specific overrides
            if self.is_development:
                config["level"] = "DEBUG"
                config["format"] = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            elif self.is_production:
                config["level"] = "WARNING"
                config["file"] = "/var/log/vacation-chatbot/app.log"
            elif self.is_testing:
                config["level"] = "ERROR"
                config["format"] = "%(levelname)s - %(message)s"
            
            self._config_cache[cache_key] = config
        
        return self._config_cache[cache_key]
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration for current environment."""
        cache_key = f"performance_{self._environment}"
        if cache_key not in self._config_cache:
            config = {
                "cache_ttl": 300,  # 5 minutes
                "max_concurrent_requests": 10,
                "request_timeout": 30,
                "database_timeout": 10,
            }
            
            # Environment-specific overrides
            if self.is_development:
                config["cache_ttl"] = 60  # Shorter cache in dev
                config["max_concurrent_requests"] = 5
                config["request_timeout"] = 60  # Longer timeout for debugging
            elif self.is_production:
                config["cache_ttl"] = 600  # Longer cache in prod
                config["max_concurrent_requests"] = 50
                config["request_timeout"] = 30
            elif self.is_testing:
                config["cache_ttl"] = 0  # No cache in tests
                config["max_concurrent_requests"] = 1
                config["request_timeout"] = 5
            
            self._config_cache[cache_key] = config
        
        return self._config_cache[cache_key]
    
    def validate_config(self) -> bool:
        """Validate configuration for current environment."""
        try:
            # Validate database config
            db_config = self.get_database_config()
            if not db_config["url"]:
                raise ValueError("Database URL is required")
            
            # Validate OpenAI config
            openai_config = self.get_openai_config()
            if not openai_config["api_key"]:
                raise ValueError("OpenAI API key is required")
            
            # Validate security config
            security_config = self.get_security_config()
            if not security_config["secret_key"]:
                raise ValueError("Secret key is required")
            
            return True
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration for current environment."""
        return {
            "environment": self._environment,
            "database": self.get_database_config(),
            "openai": self.get_openai_config(),
            "security": self.get_security_config(),
            "logging": self.get_logging_config(),
            "performance": self.get_performance_config(),
        }
    
    def clear_cache(self):
        """Clear configuration cache."""
        self._config_cache.clear()
    
    def get_config(self, config_type: str) -> Dict[str, Any]:
        """Get specific configuration type."""
        config_methods = {
            "database": self.get_database_config,
            "openai": self.get_openai_config,
            "security": self.get_security_config,
            "logging": self.get_logging_config,
            "performance": self.get_performance_config,
        }
        
        if config_type not in config_methods:
            raise ValueError(f"Unknown config type: {config_type}")
        
        return config_methods[config_type]()


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


@lru_cache()
def get_config() -> Dict[str, Any]:
    """Get all configuration for current environment."""
    return get_config_manager().get_all_config() 