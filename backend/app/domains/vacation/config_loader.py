import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class VacationConfigLoader:
    
    def __init__(self, config_dir: Optional[Path] = None):
        # Initialize configuration loader with optional config directory
        if config_dir is None:
            config_dir = Path(__file__).parent / "config"
        
        self.config_dir = Path(config_dir)
        self._prompts_cache: Optional[Dict] = None
        self._examples_cache: Optional[Dict] = None
        self._keywords_cache: Optional[Dict] = None
        self._destinations_cache: Optional[List[str]] = None
        self._destination_responses_cache: Optional[Dict] = None
    
    def load_prompts(self) -> Dict[str, Any]:
        # Load prompts and system messages from configuration.
        if self._prompts_cache is None:
            prompts_file = self.config_dir / "prompts.json"
            if prompts_file.exists():
                with open(prompts_file, 'r', encoding='utf-8') as f:
                    self._prompts_cache = json.load(f)
            else:
                logger.warning(f"Prompts file not found: {prompts_file}")
                self._prompts_cache = {}
        return self._prompts_cache
    
    def load_examples(self) -> Dict[str, Any]:
        # Load example conversations and responses.
        if self._examples_cache is None:
            examples_file = self.config_dir / "examples.json"
            if examples_file.exists():
                with open(examples_file, 'r', encoding='utf-8') as f:
                    self._examples_cache = json.load(f)
            else:
                logger.warning(f"Examples file not found: {examples_file}")
                self._examples_cache = {}
        return self._examples_cache
    
    def load_keywords(self) -> Dict[str, Any]:
        # Load keywords for stage detection and intent recognition.
        if self._keywords_cache is None:
            keywords_file = self.config_dir / "keywords.json"
            if keywords_file.exists():
                with open(keywords_file, 'r', encoding='utf-8') as f:
                    self._keywords_cache = json.load(f)
            else:
                logger.warning(f"Keywords file not found: {keywords_file}")
                self._keywords_cache = {}
        return self._keywords_cache
    
    def load_destinations(self) -> List[str]:
        # Load list of known destinations.
        if self._destinations_cache is None:
            destinations_file = self.config_dir / "destinations.json"
            if destinations_file.exists():
                with open(destinations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._destinations_cache = data.get("destinations", [])
            else:
                logger.warning(f"Destinations file not found: {destinations_file}")
                self._destinations_cache = []
        return self._destinations_cache
    
    def load_destination_responses(self) -> Dict[str, Any]:
        # Load destination-specific response templates.
        if self._destination_responses_cache is None:
            responses_file = self.config_dir / "destination_responses.json"
            if responses_file.exists():
                with open(responses_file, 'r', encoding='utf-8') as f:
                    self._destination_responses_cache = json.load(f)
            else:
                logger.warning(f"Destination responses file not found: {responses_file}")
                self._destination_responses_cache = {}
        return self._destination_responses_cache
    
    def get_config(self, config_type: str) -> Any:
        # Get configuration by type
        config_map = {
            "prompts": self.load_prompts(),
            "examples": self.load_examples(),
            "keywords": self.load_keywords(),
            "destinations": {"destinations": self.load_destinations()},
            "destination_responses": self.load_destination_responses()
        }
        return config_map.get(config_type, {})
    
    def build_system_prompt(self) -> str:
        # Build the complete system prompt from configuration.
        # Combines base prompt, rules, capabilities, and examples.
        prompts = self.load_prompts()
        examples = self.load_examples()
        
        system_prompt_parts = []
        
        if "base" in prompts.get("system_prompt", {}):
            system_prompt_parts.append(prompts["system_prompt"]["base"])
        
        if "rules" in prompts.get("system_prompt", {}):
            system_prompt_parts.append("\n\nRules:")
            for rule in prompts["system_prompt"]["rules"]:
                system_prompt_parts.append(f"- {rule}")
        
        if "capabilities" in prompts.get("system_prompt", {}):
            system_prompt_parts.append("\n\nYour capabilities include:")
            for capability in prompts["system_prompt"]["capabilities"]:
                system_prompt_parts.append(f"- {capability}")
        
        if "examples" in examples:
            system_prompt_parts.append("\n\nExample interactions:")
            for example in examples["examples"]:
                system_prompt_parts.append(f"\nUser: {example.get('user', '')}")
                system_prompt_parts.append(f"Assistant: {example.get('assistant', '')}")
        
        return "\n".join(system_prompt_parts)
    
    def get_response_template(self, template_name: str, **kwargs) -> str:
        # Get a response template and fill in variables
        prompts = self.load_prompts()
        templates = prompts.get("response_templates", {})
        
        template = templates.get(template_name, "")
        
        for key, value in kwargs.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        
        return template
    
    def reload(self):
        # Reload all configuration files (useful for testing or hot-reloading).
        self._prompts_cache = None
        self._examples_cache = None
        self._keywords_cache = None
        self._destinations_cache = None
        self._destination_responses_cache = None

# Global instance for easy access
vacation_config_loader = VacationConfigLoader()
