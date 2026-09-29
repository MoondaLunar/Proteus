#!/usr/bin/env python3
"""Initialize Maritime AI project structure"""
import os
import sys

def create_directories():
    """Create necessary directory structure"""
    directories = [
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
    
    for dir_path in directories:
        full_path = os.path.join(os.path.dirname(__file__), dir_path)
        os.makedirs(full_path, exist_ok=True)
        print(f"Created directory: {dir_path}")

if __name__ == "__main__":
    create_directories()
    print("Project structure initialized successfully!")
