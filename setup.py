#!/usr/bin/env python3
"""
Setup script for EdgeOptimizer
Copies template config files and sets up initial environment
"""

import os
import shutil
import sys

def setup_config():
    """Copy template config files if they don't exist"""
    
    # Check if experiment_config.json exists
    config_path = "configs/experiment_config.json"
    template_path = "configs/experiment_config.template.json"
    
    if not os.path.exists(config_path):
        if os.path.exists(template_path):
            shutil.copy(template_path, config_path)
            print(f"✅ Created {config_path} from template")
            print("⚠️  Remember to update your HuggingFace API key in the config file!")
        else:
            print(f"❌ Template file {template_path} not found")
            return False
    else:
        print(f"✅ Config file {config_path} already exists")
        
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    print("✅ Created logs directory")
    
    return True

def main():
    """Run setup"""
    print("🔧 EdgeOptimizer Setup")
    print("=" * 50)
    
    if setup_config():
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Update configs/experiment_config.json with your HuggingFace token")
        print("2. Run: python main.py")
        print("3. Run experiments: python experiments/power_comparison.py")
    else:
        print("\n❌ Setup failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
