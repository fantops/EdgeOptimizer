#!/usr/bin/env python3
"""
EdgeOptimizer - Modular optimization and monitoring package

This package provides modular components for:
- Power and system monitoring
- Model management and inference
- Configuration management
- Cloud inference management
- Experiment running and analysis
- Edge computing optimization
"""

from .agent import EdgeOptimizerAgent
from .monitor import SystemMonitor, PowerTracker
from .logging_config import get_logger
from .model_manager import ModelManager, get_model_manager
from .config import ConfigManager, get_config_manager, load_config
from .cloud_inference import CloudInferenceManager
from .experiment_runner import ExperimentRunner, PowerExperimentRunner

__all__ = [
    'EdgeOptimizerAgent',
    'SystemMonitor', 
    'PowerTracker',
    'ModelManager',
    'get_model_manager',
    'ConfigManager',
    'get_config_manager', 
    'load_config',
    'CloudInferenceManager',
    'ExperimentRunner',
    'PowerExperimentRunner'
]

__version__ = "1.0.0"