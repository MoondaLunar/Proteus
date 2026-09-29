"""Maritime AI System Setup"""
import os
import json
from pathlib import Path

def init_project():
    """Initialize project structure and core files"""
    base_dir = Path(__file__).parent
    
    # Create directories
    dirs = [
        'app',
        'app/routes',
        'app/models',
        'app/services',
        'app/utils',
        'tests',
        'docker',
        'docs',
        'logs',
    ]
    
    for d in dirs:
        (base_dir / d).mkdir(parents=True, exist_ok=True)
        print(f"✓ Directory: {d}")
    
    print("\n✓ Project structure initialized!")

if __name__ == "__main__":
    init_project()
