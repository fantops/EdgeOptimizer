#!/usr/bin/env python3
"""
Configuration management utilities for EdgeOptimizer
Centralized configuration loading and validation
"""

import json
import os
from typing import Dict, Any, Optional, Union, List
from pathlib import Path


class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.configs = {}  # Cache loaded configs
        
        # Find project root (where configs directory should be)
        self.project_root = self._find_project_root()
        if self.project_root:
            self.config_dir = self.project_root / config_dir
    
    def _find_project_root(self) -> Optional[Path]:
        """Find the project root directory"""
        current = Path(__file__).parent.parent  # Start from optimizer parent
        
        # Look for indicators of project root
        indicators = ["configs", "requirements.txt", "README.md", ".git"]
        
        for _ in range(5):  # Don't go too far up
            if any((current / indicator).exists() for indicator in indicators):
                return current
            current = current.parent
            
        return None
    
    def load_config(self, config_name: str, required: bool = True) -> Dict[str, Any]:
        """Load a configuration file"""
        if config_name in self.configs:
            return self.configs[config_name]
        
        # Try different possible paths
        possible_paths = [
            self.config_dir / f"{config_name}.json",
            self.config_dir / config_name,
            Path(config_name),  # Direct path
            Path("configs") / f"{config_name}.json",
            Path("configs") / config_name
        ]
        
        config_data = None
        config_path = None
        
        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        config_data = json.load(f)
                    config_path = path
                    break
                except (json.JSONDecodeError, IOError) as e:
                    if required:
                        print(f"Warning: Could not load config from {path}: {e}")
                    continue
        
        if config_data is None:
            if required:
                print(f"Warning: Could not find config '{config_name}' in any of these locations:")
                for path in possible_paths:
                    print(f"  - {path}")
                
                # Return default config based on name
                config_data = self._get_default_config(config_name)
            else:
                return {}
        
        # Cache the loaded config
        self.configs[config_name] = config_data
        
        if config_path:
            print(f"✅ Loaded config from: {config_path}")
        
        return config_data
    
    def _get_default_config(self, config_name: str) -> Dict[str, Any]:
        """Get default configuration for known config types"""
        defaults = {
            "optimizer_config": {
                "battery_threshold": 20,
                "cpu_threshold": 80,
                "memory_threshold": 85,
                "temperature_threshold": 70,
                "auto_fallback_cloud": True,
                "monitoring_interval": 5.0
            },
            "experiment_config": {
                "test_prompts": [
                    "What is machine learning?",
                    "Explain quantum computing",
                    "How does a neural network work?",
                    "What are the benefits of edge computing?"
                ],
                "experiment_duration": 180,
                "measurement_interval": 15,
                "cloud_provider": "huggingface",
                "cloud_api_url": "https://api-inference.huggingface.co/models/gpt2",
                "cloud_api_key": "free-no-key-required",
                "inference_settings": {
                    "local_model": "gpt2",
                    "cloud_model": "gpt2",
                    "local_max_tokens": 50,
                    "cloud_max_tokens": 50,
                    "use_mock_cloud": False
                }
            }
        }
        
        # Try to match config name to default
        for key, default in defaults.items():
            if key in config_name or config_name.replace(".json", "") == key.replace("_config", ""):
                return default
        
        return {}
    
    def get(self, config_name: str, key: str, default: Any = None) -> Any:
        """Get a specific value from a config"""
        config = self.load_config(config_name, required=False)
        return config.get(key, default)
    
    def get_nested(self, config_name: str, key_path: str, default: Any = None) -> Any:
        """Get a nested value using dot notation (e.g., 'inference_settings.local_model')"""
        config = self.load_config(config_name, required=False)
        
        keys = key_path.split('.')
        value = config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def save_config(self, config_name: str, config_data: Dict[str, Any]) -> bool:
        """Save configuration to file"""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine file path
            if not config_name.endswith('.json'):
                config_name += '.json'
            
            config_path = self.config_dir / config_name
            
            # Save config
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2, sort_keys=True)
            
            # Update cache
            self.configs[config_name.replace('.json', '')] = config_data
            
            print(f"✅ Saved config to: {config_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save config {config_name}: {e}")
            return False
    
    def list_configs(self) -> List[str]:
        """List available configuration files"""
        if not self.config_dir.exists():
            return []
        
        configs = []
        for file_path in self.config_dir.glob("*.json"):
            configs.append(file_path.stem)
        
        return sorted(configs)
    
    def validate_config(self, config_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a configuration against a schema"""
        config = self.load_config(config_name, required=False)
        errors = []
        
        for key, expected_type in schema.items():
            if key not in config:
                errors.append(f"Missing required key: {key}")
            elif not isinstance(config[key], expected_type):
                errors.append(f"Key '{key}' should be {expected_type.__name__}, got {type(config[key]).__name__}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "config": config
        }


# Global config manager instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get the singleton config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def load_config(config_name: str) -> Dict[str, Any]:
    """Convenience function to load a config"""
    return get_config_manager().load_config(config_name)
