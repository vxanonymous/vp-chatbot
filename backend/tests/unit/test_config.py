from app.core.config_manager import ConfigManager, get_config_manager, get_config
from app.domains.vacation.config_loader import VacationConfigLoader, vacation_config_loader
from pathlib import Path
from unittest.mock import MagicMock, patch
from unittest.mock import patch, mock_open
import json
import pytest

class TestConfigManager:
    
    def test_init_default(self):
        manager = ConfigManager()
        
        assert manager._environment is not None
        assert manager._config_cache == {}
    
    def test_init_custom_settings(self):
        mock_settings = MagicMock()
        mock_settings.environment = "test"
        
        manager = ConfigManager(settings=mock_settings)
        
        assert manager._environment == "test"
    
    def test_environment_property(self):
        manager = ConfigManager()
        result = manager.environment
        
        assert result is not None
    
    def test_is_development_true(self):
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        
        manager = ConfigManager(settings=mock_settings)
        
        assert manager.is_development is True
        assert manager.is_production is False
        assert manager.is_testing is False
    
    def test_is_production_true(self):
        mock_settings = MagicMock()
        mock_settings.environment = "production"
        
        manager = ConfigManager(settings=mock_settings)
        
        assert manager.is_production is True
        assert manager.is_development is False
        assert manager.is_testing is False
    
    def test_is_testing_true(self):
        mock_settings = MagicMock()
        mock_settings.environment = "testing"
        
        manager = ConfigManager(settings=mock_settings)
        
        assert manager.is_testing is True
        assert manager.is_development is False
        assert manager.is_production is False
    
    def test_get_database_config_development(self):
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        mock_settings.mongodb_url = "mongodb://localhost:27017/test"
        mock_settings.mongodb_database = "test_db"
        mock_settings.mongodb_ssl = True
        mock_settings.mongodb_ssl_verify = True
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_database_config()
        
        assert config["url"] == "mongodb://localhost:27017/test"
        assert config["ssl"] is False
        assert config["timeout"] == 10000
    
    def test_get_database_config_production(self):
        mock_settings = MagicMock()
        mock_settings.environment = "production"
        mock_settings.mongodb_url = "mongodb://localhost:27017/test"
        mock_settings.mongodb_database = "test_db"
        mock_settings.mongodb_ssl = True
        mock_settings.mongodb_ssl_verify = True
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_database_config()
        
        assert config["ssl"] is True
        assert config["timeout"] == 30000
    
    def test_get_database_config_testing(self):
        mock_settings = MagicMock()
        mock_settings.environment = "testing"
        mock_settings.mongodb_url = "mongodb://localhost:27017/test"
        mock_settings.mongodb_database = "test_db"
        mock_settings.mongodb_ssl = True
        mock_settings.mongodb_ssl_verify = True
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_database_config()
        
        assert config["url"] == "mongodb://localhost:27017/test"
        assert config["ssl"] is False
    
    def test_get_openai_config_development(self):
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        mock_settings.openrouter_api_key = "test_key"
        mock_settings.openrouter_model = "x-ai/grok-4.1-fast"
        mock_settings.openrouter_max_tokens = 8000
        mock_settings.openrouter_temperature = 0.5
        mock_settings.openrouter_timeout = 30
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_openai_config()
        
        assert config["temperature"] == 0.7
        assert config["timeout"] == 120
    
    def test_get_openai_config_production(self):
        mock_settings = MagicMock()
        mock_settings.environment = "production"
        mock_settings.openrouter_api_key = "prod_key"
        mock_settings.openrouter_model = "x-ai/grok-4.1-fast"
        mock_settings.openrouter_max_tokens = 8000
        mock_settings.openrouter_temperature = 0.5
        mock_settings.openrouter_timeout = 30
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_openai_config()
        
        assert config["temperature"] == 0.5
        assert config["timeout"] == 180
    
    def test_get_openai_config_testing(self):
        mock_settings = MagicMock()
        mock_settings.environment = "testing"
        mock_settings.openrouter_api_key = "test_key"
        mock_settings.openrouter_model = "x-ai/grok-4.1-fast"
        mock_settings.openrouter_max_tokens = 8000
        mock_settings.openrouter_temperature = 0.5
        mock_settings.openrouter_timeout = 5
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_openai_config()
        
        assert config["api_key"] == "test_key"
        assert config["base_url"] == "https://openrouter.ai/api/v1"
        assert config["timeout"] == 5
    
    def test_get_security_config_development(self):
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        mock_settings.secret_key = "dev_secret"
        mock_settings.algorithm = "HS256"
        mock_settings.access_token_expire_minutes = 30
        mock_settings.cors_origins = []
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_security_config()
        
        assert config["access_token_expire_minutes"] == 60
        assert "http://localhost:3000" in config["cors_origins"]
    
    def test_get_security_config_production(self):
        mock_settings = MagicMock()
        mock_settings.environment = "production"
        mock_settings.secret_key = "prod_secret"
        mock_settings.algorithm = "HS256"
        mock_settings.access_token_expire_minutes = 30
        mock_settings.cors_origins = ["https://example.com"]
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_security_config()
        
        assert config["access_token_expire_minutes"] == 30
        assert config["cors_origins"] == ["https://example.com"]
    
    def test_get_security_config_testing(self):
        mock_settings = MagicMock()
        mock_settings.environment = "testing"
        mock_settings.secret_key = "test_secret"
        mock_settings.algorithm = "HS256"
        mock_settings.access_token_expire_minutes = 5
        mock_settings.cors_origins = []
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_security_config()
        
        assert config["secret_key"] == "test_secret_key"
        assert config["access_token_expire_minutes"] == 5
    
    def test_get_logging_config_development(self):
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_logging_config()
        
        assert config["level"] == "DEBUG"
        assert "funcName" in config["format"]
    
    def test_get_logging_config_production(self):
        mock_settings = MagicMock()
        mock_settings.environment = "production"
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_logging_config()
        
        assert config["level"] == "WARNING"
        assert config["file"] == "/var/log/vacation-planning-system/app.log"
    
    def test_get_logging_config_testing(self):
        mock_settings = MagicMock()
        mock_settings.environment = "testing"
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_logging_config()
        
        assert config["level"] == "ERROR"
        assert config["format"] == "%(levelname)s - %(message)s"
    
    def test_get_performance_config_development(self):
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_performance_config()
        
        assert config["cache_ttl"] == 60
        assert config["max_concurrent_requests"] == 5
        assert config["request_timeout"] == 120
    
    def test_get_performance_config_production(self):
        mock_settings = MagicMock()
        mock_settings.environment = "production"
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_performance_config()
        
        assert config["cache_ttl"] == 600
        assert config["max_concurrent_requests"] == 50
        assert config["request_timeout"] == 180
    
    def test_get_performance_config_testing(self):
        mock_settings = MagicMock()
        mock_settings.environment = "testing"
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_performance_config()
        
        assert config["cache_ttl"] == 0
        assert config["max_concurrent_requests"] == 1
        assert config["request_timeout"] == 5
    
    def test_validate_config_success(self):
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        mock_settings.mongodb_url = "mongodb://localhost:27017/test"
        mock_settings.mongodb_database = "test_db"
        mock_settings.mongodb_ssl = False
        mock_settings.mongodb_ssl_verify = False
        mock_settings.openrouter_api_key = "test_key"
        mock_settings.openrouter_model = "x-ai/grok-4.1-fast"
        mock_settings.openrouter_max_tokens = 8000
        mock_settings.openrouter_temperature = 0.5
        mock_settings.openrouter_timeout = 30
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        mock_settings.secret_key = "test_secret"
        mock_settings.algorithm = "HS256"
        mock_settings.access_token_expire_minutes = 30
        mock_settings.cors_origins = []
        
        manager = ConfigManager(settings=mock_settings)
        result = manager.validate_config()
        
        assert result is True
    
    def test_validate_config_missing_database_url(self):
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        mock_settings.mongodb_url = ""
        mock_settings.mongodb_database = "test_db"
        mock_settings.mongodb_ssl = False
        mock_settings.mongodb_ssl_verify = False
        mock_settings.openrouter_api_key = "test_key"
        mock_settings.openrouter_model = "x-ai/grok-4.1-fast"
        mock_settings.openrouter_max_tokens = 8000
        mock_settings.openrouter_temperature = 0.5
        mock_settings.openrouter_timeout = 30
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        mock_settings.secret_key = "test_secret"
        mock_settings.algorithm = "HS256"
        mock_settings.access_token_expire_minutes = 30
        mock_settings.cors_origins = []
        
        manager = ConfigManager(settings=mock_settings)
        result = manager.validate_config()
        
        assert result is False
    
    def test_validate_config_missing_openrouter_key(self):
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        mock_settings.mongodb_url = "mongodb://localhost:27017/test"
        mock_settings.mongodb_database = "test_db"
        mock_settings.mongodb_ssl = False
        mock_settings.mongodb_ssl_verify = False
        mock_settings.openrouter_api_key = ""
        mock_settings.openrouter_model = "x-ai/grok-4.1-fast"
        mock_settings.openrouter_max_tokens = 8000
        mock_settings.openrouter_temperature = 0.5
        mock_settings.openrouter_timeout = 30
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        mock_settings.secret_key = "test_secret"
        mock_settings.algorithm = "HS256"
        mock_settings.access_token_expire_minutes = 30
        mock_settings.cors_origins = []
        
        manager = ConfigManager(settings=mock_settings)
        result = manager.validate_config()
        
        assert result is False
    
    def test_validate_config_missing_secret_key(self):
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        mock_settings.mongodb_url = "mongodb://localhost:27017/test"
        mock_settings.mongodb_database = "test_db"
        mock_settings.mongodb_ssl = False
        mock_settings.mongodb_ssl_verify = False
        mock_settings.openrouter_api_key = "test_key"
        mock_settings.openrouter_model = "x-ai/grok-4.1-fast"
        mock_settings.openrouter_max_tokens = 8000
        mock_settings.openrouter_temperature = 0.5
        mock_settings.openrouter_timeout = 30
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        mock_settings.secret_key = ""
        mock_settings.algorithm = "HS256"
        mock_settings.access_token_expire_minutes = 30
        mock_settings.cors_origins = []
        
        manager = ConfigManager(settings=mock_settings)
        result = manager.validate_config()
        
        assert result is False
    
    def test_get_all_config(self):
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        mock_settings.mongodb_url = "mongodb://localhost:27017/test"
        mock_settings.mongodb_database = "test_db"
        mock_settings.mongodb_ssl = False
        mock_settings.mongodb_ssl_verify = False
        mock_settings.openrouter_api_key = "test_key"
        mock_settings.openrouter_model = "x-ai/grok-4.1-fast"
        mock_settings.openrouter_max_tokens = 8000
        mock_settings.openrouter_temperature = 0.5
        mock_settings.openrouter_timeout = 30
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        mock_settings.secret_key = "test_secret"
        mock_settings.algorithm = "HS256"
        mock_settings.access_token_expire_minutes = 30
        mock_settings.cors_origins = []
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_all_config()
        
        assert "environment" in config
        assert "database" in config
        assert "openai" in config
        assert "security" in config
        assert "logging" in config
        assert "performance" in config
    
    def test_clear_cache(self):
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        
        manager = ConfigManager(settings=mock_settings)
        manager._config_cache["test_key"] = "test_value"
        
        manager.clear_cache()
        
        assert manager._config_cache == {}
    
    def test_get_config_valid_type(self):
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        mock_settings.mongodb_url = "mongodb://localhost:27017/test"
        mock_settings.mongodb_database = "test_db"
        mock_settings.mongodb_ssl = False
        mock_settings.mongodb_ssl_verify = False
        
        manager = ConfigManager(settings=mock_settings)
        config = manager.get_config("database")
        
        assert "url" in config
        assert "database_name" in config
    
    def test_get_config_invalid_type(self):
        mock_settings = MagicMock()
        mock_settings.environment = "development"
        
        manager = ConfigManager(settings=mock_settings)
        
        with pytest.raises(ValueError, match="Unknown config type"):
            manager.get_config("invalid_type")



class TestConfigManagerGlobal:
    
    def test_get_config_manager(self):
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        assert manager1 is manager2
    
    def test_get_config(self):
        with patch('app.core.config_manager.get_config_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_all_config.return_value = {"test": "config"}
            mock_get_manager.return_value = mock_manager
            
            result = get_config()
            
            assert result == {"test": "config"}




class TestVacationConfigLoader:
    
    @pytest.fixture
    def config_dir(self, tmp_path):
    # Create a temporary config directory.
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        return config_dir
    
    @pytest.fixture
    def loader(self, config_dir):
    # Create a VacationConfigLoader instance.
        return VacationConfigLoader(config_dir=config_dir)
    
    def test_load_prompts(self, loader, config_dir):
        prompts_data = {
            "system_prompt": "Test system prompt",
            "rules": ["Rule 1", "Rule 2"]
        }
        prompts_file = config_dir / "prompts.json"
        prompts_file.write_text(json.dumps(prompts_data))
        
        result = loader.load_prompts()
        
        assert result == prompts_data
    
    def test_load_prompts_missing_file(self, loader):
        result = loader.load_prompts()
        
        assert result == {}
    
    def test_load_examples(self, loader, config_dir):
        examples_data = [
            {"user": "Test user", "assistant": "Test assistant"}
        ]
        examples_file = config_dir / "examples.json"
        examples_file.write_text(json.dumps(examples_data))
        
        result = loader.load_examples()
        
        assert result == examples_data
    
    def test_load_keywords(self, loader, config_dir):
        keywords_data = {
            "travel_styles": {
                "adventure": ["hiking", "climbing"]
            }
        }
        keywords_file = config_dir / "keywords.json"
        keywords_file.write_text(json.dumps(keywords_data))
        
        result = loader.load_keywords()
        
        assert result == keywords_data
    
    def test_load_destinations(self, loader, config_dir):
        destinations_data = {
            "destinations": ["paris", "tokyo", "london"]
        }
        destinations_file = config_dir / "destinations.json"
        destinations_file.write_text(json.dumps(destinations_data))
        
        result = loader.load_destinations()
        
        assert result == ["paris", "tokyo", "london"]
    
    def test_load_destination_responses(self, loader, config_dir):
        responses_data = {
            "introductions": {
                "paris": "Paris is great!"
            },
            "budget": {
                "paris": "Budget for Paris"
            }
        }
        responses_file = config_dir / "destination_responses.json"
        responses_file.write_text(json.dumps(responses_data))
        
        result = loader.load_destination_responses()
        
        assert result == responses_data
    
    def test_get_config_prompts(self, loader, config_dir):
        prompts_data = {"system_prompt": "Test"}
        prompts_file = config_dir / "prompts.json"
        prompts_file.write_text(json.dumps(prompts_data))
        
        result = loader.get_config("prompts")
        
        assert result == prompts_data
    
    def test_get_config_destinations(self, loader, config_dir):
        destinations_data = {
            "destinations": ["paris", "tokyo"]
        }
        destinations_file = config_dir / "destinations.json"
        destinations_file.write_text(json.dumps(destinations_data))
        
        result = loader.get_config("destinations")
        
        assert result == {"destinations": ["paris", "tokyo"]}
    
    def test_get_config_destination_responses(self, loader, config_dir):
        responses_data = {
            "introductions": {"paris": "Test"}
        }
        responses_file = config_dir / "destination_responses.json"
        responses_file.write_text(json.dumps(responses_data))
        
        result = loader.get_config("destination_responses")
        
        assert result == responses_data
    
    def test_get_config_invalid_type(self, loader):
        result = loader.get_config("invalid_type")
        
        assert result == {}
    
    def test_reload(self, loader, config_dir):
        prompts_file = config_dir / "prompts.json"
        prompts_file.write_text(json.dumps({"test": "data"}))
        
        loader.load_prompts()
        loader.reload()
        
        prompts_file.write_text(json.dumps({"test": "new_data"}))
        result = loader.load_prompts()
        
        assert result == {"test": "new_data"}
    
    def test_global_instance(self):
        assert vacation_config_loader is not None
        assert isinstance(vacation_config_loader, VacationConfigLoader)




class TestVacationConfigLoaderAdditional:
# Additional tests for VacationConfigLoader.
    
    def test_build_system_prompt_with_all_parts(self):
        loader = VacationConfigLoader()
        
        prompts_data = {
            "system_prompt": {
                "base": "You are a travel assistant",
                "rules": ["Rule 1", "Rule 2"],
                "capabilities": ["Capability 1", "Capability 2"]
            }
        }
        examples_data = {
            "examples": [
                {"user": "Hello", "assistant": "Hi!"}
            ]
        }
        
        with patch.object(loader, 'load_prompts', return_value=prompts_data):
            with patch.object(loader, 'load_examples', return_value=examples_data):
                result = loader.build_system_prompt()
                
                assert "You are a travel assistant" in result
                assert "Rule 1" in result
                assert "Capability 1" in result
                assert "Hello" in result
                assert "Hi!" in result
    
    def test_build_system_prompt_with_base_only(self):
        loader = VacationConfigLoader()
        
        prompts_data = {
            "system_prompt": {
                "base": "You are a travel assistant"
            }
        }
        examples_data = {}
        
        with patch.object(loader, 'load_prompts', return_value=prompts_data):
            with patch.object(loader, 'load_examples', return_value=examples_data):
                result = loader.build_system_prompt()
                
                assert "You are a travel assistant" in result
    
    def test_build_system_prompt_with_rules_only(self):
        loader = VacationConfigLoader()
        
        prompts_data = {
            "system_prompt": {
                "rules": ["Rule 1", "Rule 2"]
            }
        }
        examples_data = {}
        
        with patch.object(loader, 'load_prompts', return_value=prompts_data):
            with patch.object(loader, 'load_examples', return_value=examples_data):
                result = loader.build_system_prompt()
                
                assert "Rule 1" in result
                assert "Rule 2" in result
    
    def test_build_system_prompt_with_capabilities_only(self):
        loader = VacationConfigLoader()
        
        prompts_data = {
            "system_prompt": {
                "capabilities": ["Capability 1"]
            }
        }
        examples_data = {}
        
        with patch.object(loader, 'load_prompts', return_value=prompts_data):
            with patch.object(loader, 'load_examples', return_value=examples_data):
                result = loader.build_system_prompt()
                
                assert "Capability 1" in result
    
    def test_get_response_template_with_variables(self):
        loader = VacationConfigLoader()
        
        prompts_data = {
            "response_templates": {
                "destination_mentioned": "Welcome to {{destination}}! It's a great place."
            }
        }
        
        with patch.object(loader, 'load_prompts', return_value=prompts_data):
            result = loader.get_response_template("destination_mentioned", destination="Paris")
            
            assert "Welcome to Paris!" in result
            assert "{{destination}}" not in result
    
    def test_get_response_template_missing_template(self):
        loader = VacationConfigLoader()
        
        prompts_data = {
            "response_templates": {}
        }
        
        with patch.object(loader, 'load_prompts', return_value=prompts_data):
            result = loader.get_response_template("missing_template")
            
            assert result == ""
    
    def test_get_response_template_multiple_variables(self):
        loader = VacationConfigLoader()
        
        prompts_data = {
            "response_templates": {
                "greeting": "Hello {{name}}, welcome to {{destination}}!"
            }
        }
        
        with patch.object(loader, 'load_prompts', return_value=prompts_data):
            result = loader.get_response_template(
                "greeting",
                name="John",
                destination="Paris"
            )
            
            assert "Hello John" in result
            assert "welcome to Paris" in result
    
    def test_reload_clears_cache(self):
        loader = VacationConfigLoader()
        loader._prompts_cache = {"test": "data"}
        loader._examples_cache = {"test": "data"}
        loader._keywords_cache = {"test": "data"}
        loader._destinations_cache = {"test": "data"}
        loader._destination_responses_cache = {"test": "data"}
        
        loader.reload()
        
        assert loader._prompts_cache is None
        assert loader._examples_cache is None
        assert loader._keywords_cache is None
        assert loader._destinations_cache is None
        assert loader._destination_responses_cache is None



