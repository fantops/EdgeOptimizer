"""
Logging configuration for EdgeOptimizer
Provides centralized logging with file and console output
"""

import logging
import os
from datetime import datetime
from pathlib import Path

class EdgeOptimizerLogger:
    """Centralized logging for EdgeOptimizer components"""
    
    def __init__(self, name: str = "EdgeOptimizer", log_level: str = "INFO"):
        self.name = name
        self.log_level = getattr(logging, log_level.upper())
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration with file and console handlers"""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.log_level)
        
        # Avoid duplicate handlers
        if self.logger.handlers:
            return self.logger
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler for detailed logs
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"edgeoptimizer_{timestamp}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        return self.logger
    
    def get_logger(self):
        """Get the configured logger instance"""
        return self.logger

# Global logger instance
_logger_instance = None

def get_logger(name: str = "EdgeOptimizer") -> logging.Logger:
    """Get or create a logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = EdgeOptimizerLogger(name)
    return _logger_instance.get_logger()

def log_experiment_start(mode: str, duration: int, model_info: dict):
    """Log experiment start with parameters"""
    logger = get_logger("Experiment")
    logger.info(f"Starting {mode} experiment - Duration: {duration}s, Local: {model_info.get('local_model', 'unknown')}, Cloud: {model_info.get('cloud_provider', 'unknown')}")

def log_inference_result(provider: str, success: bool, response_time: float, error: str = None):
    """Log individual inference results"""
    logger = get_logger("Inference")
    status = "SUCCESS" if success else "FAILED"
    if success:
        logger.info(f"{provider.upper()} inference {status} - Time: {response_time:.3f}s")
    else:
        logger.error(f"{provider.upper()} inference {status} - Time: {response_time:.3f}s - Error: {error}")

def log_system_status(battery: int, cpu: float, memory: float):
    """Log system status"""
    logger = get_logger("System")
    logger.info(f"System Status - Battery: {battery}%, CPU: {cpu:.1f}%, Memory: {memory:.1f}%")

def log_power_reading(phase: str, before: dict, after: dict):
    """Log power consumption readings"""
    logger = get_logger("Power")
    cpu_change = after['cpu_percent'] - before['cpu_percent']
    memory_change = after['memory_percent'] - before['memory_percent']
    logger.debug(f"{phase.upper()} Power Reading - CPU: {before['cpu_percent']:.1f}% -> {after['cpu_percent']:.1f}% ({cpu_change:+.1f}%), Memory: {before['memory_percent']:.1f}% -> {after['memory_percent']:.1f}% ({memory_change:+.1f}%)")
