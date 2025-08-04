#!/usr/bin/env python3
"""
Centralized Logging Configuration for EdgeOptimizer
Provides organized, structured logging across all modules
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class EdgeOptimizerLogger:
    """Centralized logging manager for EdgeOptimizer"""
    
    def __init__(self, base_dir: str = "logs"):
        self.base_dir = Path(base_dir)
        self.setup_log_directories()
        self.loggers = {}
        
    def setup_log_directories(self):
        """Create organized log directory structure"""
        directories = [
            "power_analysis",
            "experiments", 
            "system",
            "archive"
        ]
        
        for dir_name in directories:
            (self.base_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    def get_logger(self, name: str, log_type: str = "system", level: int = logging.INFO) -> logging.Logger:
        """Get or create a logger with organized file structure"""
        
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Clear any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create timestamp for log file
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = self.base_dir / log_type / f"{name}_{timestamp}.log"
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self.loggers[name] = logger
        return logger
    
    def save_experiment_results(self, data: Dict[str, Any], experiment_type: str = "power_comparison") -> str:
        """Save experiment results with organized naming"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.base_dir / "experiments" / f"{experiment_type}_{timestamp}.json"
        
        # Add metadata
        data["metadata"] = {
            "timestamp": timestamp,
            "experiment_type": experiment_type,
            "version": "2.0",
            "generated_by": "EdgeOptimizer"
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return str(filename)
    
    def save_power_analysis(self, data: Dict[str, Any], analysis_type: str = "comparison") -> str:
        """Save power analysis with structured naming"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.base_dir / "power_analysis" / f"power_{analysis_type}_{timestamp}.json"
        
        # Add analysis metadata
        data["analysis_metadata"] = {
            "timestamp": timestamp,
            "analysis_type": analysis_type,
            "version": "2.0",
            "tools_used": ["enhanced_power_monitor", "power_comparison"]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return str(filename)
    
    def archive_old_logs(self, days_old: int = 7):
        """Archive logs older than specified days"""
        import shutil
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        archived_count = 0
        
        for log_dir in ["power_analysis", "experiments", "system"]:
            log_path = self.base_dir / log_dir
            if not log_path.exists():
                continue
                
            for log_file in log_path.glob("*"):
                if log_file.is_file():
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        archive_path = self.base_dir / "archive" / log_file.name
                        shutil.move(str(log_file), str(archive_path))
                        archived_count += 1
        
        return archived_count
    
    def cleanup_logs(self, keep_recent: int = 10):
        """Keep only the most recent N log files in each category"""
        for log_dir in ["power_analysis", "experiments", "system"]:
            log_path = self.base_dir / log_dir
            if not log_path.exists():
                continue
            
            # Get all files sorted by modification time (newest first)
            files = sorted(log_path.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Move older files to archive
            for old_file in files[keep_recent:]:
                if old_file.is_file():
                    archive_path = self.base_dir / "archive" / old_file.name
                    old_file.rename(archive_path)
    
    def get_log_summary(self) -> Dict[str, Any]:
        """Get summary of current log structure"""
        summary = {}
        
        for log_dir in ["power_analysis", "experiments", "system", "archive"]:
            log_path = self.base_dir / log_dir
            if log_path.exists():
                files = list(log_path.glob("*"))
                summary[log_dir] = {
                    "count": len(files),
                    "files": [f.name for f in files[:5]]  # Show first 5
                }
        
        return summary

# Global logger instance
_logger_instance = None

def get_logger(name: str, log_type: str = "system") -> logging.Logger:
    """Get a logger instance with organized structure"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = EdgeOptimizerLogger()
    
    return _logger_instance.get_logger(name, log_type)

def save_experiment_results(data: Dict[str, Any], experiment_type: str = "power_comparison") -> str:
    """Save experiment results with organized structure"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = EdgeOptimizerLogger()
    
    return _logger_instance.save_experiment_results(data, experiment_type)

def save_power_analysis(data: Dict[str, Any], analysis_type: str = "comparison") -> str:
    """Save power analysis with organized structure"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = EdgeOptimizerLogger()
    
    return _logger_instance.save_power_analysis(data, analysis_type)

def cleanup_logs(keep_recent: int = 10) -> int:
    """Clean up old log files"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = EdgeOptimizerLogger()
    
    _logger_instance.cleanup_logs(keep_recent)
    return _logger_instance.archive_old_logs()
