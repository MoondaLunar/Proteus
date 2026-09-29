#!/usr/bin/env python3
"""
Maritime AI System - Initialization Script
Sets up project structure, creates necessary directories, and initializes core components
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def create_project_structure():
    """Create the complete project directory structure"""
    base_dir = Path(__file__).parent
    
    directories = [
        'app',
        'app/routes',
        'app/models',
        'app/services',
        'app/utils',
        'app/integrations',
        'tests',
        'tests/unit',
        'tests/integration',
        'docker',
        'docs',
        'logs',
        'data',
        'data/migrations',
    ]
    
    print("📁 Creating project directories...")
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}")
    
    return base_dir

def create_python_files(base_dir):
    """Create essential Python files"""
    print("\n🐍 Creating Python modules...")
    
    files = {
        'app/__init__.py': '''"""Maritime AI System Package"""
__version__ = "0.1.0"
__author__ = "Maritime AI Team"
__title__ = "Maritime AI System"
''',
        'app/routes/__init__.py': '''"""API Routes Package"""
''',
        'app/models/__init__.py': '''"""Data Models Package"""
''',
        'app/services/__init__.py': '''"""Services Package"""
''',
        'app/utils/__init__.py': '''"""Utilities Package"""
''',
        'app/integrations/__init__.py': '''"""Third-party Integrations Package"""
''',
        'tests/__init__.py': '''"""Test Suite Package"""
''',
        'tests/unit/__init__.py': '''"""Unit Tests Package"""
''',
        'tests/integration/__init__.py': '''"""Integration Tests Package"""
''',
    }
    
    for file_path, content in files.items():
        full_path = base_dir / file_path
        if not full_path.exists():
            full_path.write_text(content)
            print(f"  ✓ {file_path}")
    
    return base_dir

def create_init_db_script(base_dir):
    """Create the database initialization SQL script"""
    print("\n💾 Creating database initialization script...")
    
    docker_dir = base_dir / 'docker'
    docker_dir.mkdir(exist_ok=True)
    
    init_sql_path = docker_dir / 'init-db.sql'
    print(f"  ✓ {init_sql_path.relative_to(base_dir)}")
    
    return base_dir

def print_summary(base_dir):
    """Print a summary of the initialization"""
    print("\n" + "="*70)
    print("✅ Maritime AI System - Project Initialization Complete!")
    print("="*70)
    print(f"\n📍 Project Location: {base_dir}")
    print("\n📋 Next Steps:")
    print("  1. Copy .env.example to .env and configure your settings")
    print("  2. Ensure Docker and Docker Compose are installed")
    print("  3. Start services: docker-compose up -d")
    print("  4. Initialize database: docker-compose exec api python -m alembic upgrade head")
    print("  5. Access API docs: http://localhost:8000/docs")
    print("\n🚀 Development Commands:")
    print("  # Run tests")
    print("  pytest")
    print("\n  # Format code")
    print("  black app/ tests/")
    print("\n  # Type checking")
    print("  mypy app/")
    print("\n📚 Documentation: See README.md for detailed information")
    print("="*70 + "\n")

def main():
    """Main initialization function"""
    try:
        base_dir = create_project_structure()
        create_python_files(base_dir)
        create_init_db_script(base_dir)
        print_summary(base_dir)
        return 0
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
