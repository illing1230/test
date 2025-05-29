#!/usr/bin/env python3
"""
Langflow Local Setup Script
This script handles the complete setup process for running Langflow locally.
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

class LangflowSetup:
    def __init__(self):
        self.project_dir = Path.cwd()
        self.langflow_dir = self.project_dir / "langflow"
        self.python_executable = sys.executable
        
    def check_prerequisites(self):
        """Check if all required tools are installed"""
        print("🔍 Checking prerequisites...")
        
        required_tools = {
            'git': 'Git is required to clone the repository',
            'node': 'Node.js is required for frontend components',
            'npm': 'npm is required for package management'
        }
        
        missing_tools = []
        
        for tool, description in required_tools.items():
            if not shutil.which(tool):
                missing_tools.append(f"  ❌ {tool}: {description}")
            else:
                print(f"  ✅ {tool}: Found")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            missing_tools.append("  ❌ Python 3.8+ is required")
        else:
            print(f"  ✅ Python {python_version.major}.{python_version.minor}: Compatible")
        
        if missing_tools:
            print("\n❌ Missing prerequisites:")
            for tool in missing_tools:
                print(tool)
            return False
        
        print("✅ All prerequisites met!")
        return True
    
    def clone_repository(self):
        """Clone the Langflow repository"""
        print("\n📥 Cloning Langflow repository...")
        
        if self.langflow_dir.exists():
            print(f"  ⚠️  Directory {self.langflow_dir} already exists")
            response = input("  Do you want to remove it and clone fresh? (y/N): ")
            if response.lower() == 'y':
                shutil.rmtree(self.langflow_dir)
            else:
                print("  Using existing directory...")
                return True
        
        try:
            result = subprocess.run([
                'git', 'clone', 
                'https://github.com/langflow-ai/langflow.git',
                str(self.langflow_dir)
            ], check=True, capture_output=True, text=True)
            print("  ✅ Repository cloned successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to clone repository: {e}")
            print(f"  Error output: {e.stderr}")
            return False
    
    def setup_python_environment(self):
        """Set up Python virtual environment and install dependencies"""
        print("\n🐍 Setting up Python environment...")
        
        venv_dir = self.langflow_dir / "venv"
        
        # Create virtual environment
        if not venv_dir.exists():
            print("  Creating virtual environment...")
            try:
                subprocess.run([
                    self.python_executable, '-m', 'venv', str(venv_dir)
                ], check=True)
                print("  ✅ Virtual environment created")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Failed to create virtual environment: {e}")
                return False
        else:
            print("  ✅ Virtual environment already exists")
        
        # Determine pip executable path
        if platform.system() == "Windows":
            pip_executable = venv_dir / "Scripts" / "pip"
            python_executable = venv_dir / "Scripts" / "python"
        else:
            pip_executable = venv_dir / "bin" / "pip"
            python_executable = venv_dir / "bin" / "python"
        
        # Upgrade pip
        print("  Upgrading pip...")
        try:
            subprocess.run([
                str(python_executable), '-m', 'pip', 'install', '--upgrade', 'pip'
            ], check=True, cwd=self.langflow_dir)
            print("  ✅ Pip upgraded")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Warning: Failed to upgrade pip: {e}")
        
        # Install langflow in development mode
        print("  Installing Langflow dependencies...")
        try:
            subprocess.run([
                str(pip_executable), 'install', '-e', '.'
            ], check=True, cwd=self.langflow_dir)
            print("  ✅ Langflow dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to install dependencies: {e}")
            return False
    
    def setup_frontend(self):
        """Set up frontend dependencies"""
        print("\n⚛️  Setting up frontend...")
        
        frontend_dir = self.langflow_dir / "src" / "frontend"
        if not frontend_dir.exists():
            # Try alternative frontend location
            frontend_dir = self.langflow_dir / "frontend"
        
        if not frontend_dir.exists():
            print("  ⚠️  Frontend directory not found, skipping frontend setup")
            return True
        
        print(f"  Installing frontend dependencies in {frontend_dir}...")
        try:
            subprocess.run(['npm', 'install'], check=True, cwd=frontend_dir)
            print("  ✅ Frontend dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to install frontend dependencies: {e}")
            return False
    
    def create_config_files(self):
        """Create necessary configuration files"""
        print("\n⚙️  Creating configuration files...")
        
        # Copy our config files to the langflow directory
        config_files = ['config.py', 'langflow_config.yaml']
        
        for config_file in config_files:
            src_path = self.project_dir / config_file
            dest_path = self.langflow_dir / config_file
            
            if src_path.exists():
                try:
                    shutil.copy2(src_path, dest_path)
                    print(f"  ✅ Copied {config_file}")
                except Exception as e:
                    print(f"  ⚠️  Warning: Failed to copy {config_file}: {e}")
        
        return True
    
    def run_setup(self):
        """Run the complete setup process"""
        print("🚀 Starting Langflow local setup...")
        print("=" * 50)
        
        steps = [
            self.check_prerequisites,
            self.clone_repository,
            self.setup_python_environment,
            self.setup_frontend,
            self.create_config_files
        ]
        
        for i, step in enumerate(steps, 1):
            print(f"\n[Step {i}/{len(steps)}]")
            if not step():
                print(f"\n❌ Setup failed at step {i}")
                return False
        
        print("\n" + "=" * 50)
        print("🎉 Langflow setup completed successfully!")
        print("\nNext steps:")
        print("1. Run './start.sh' to start the Langflow server")
        print("2. Run 'python verify_setup.py' to verify the installation")
        print("3. Open http://localhost:7860 in your browser")
        
        return True

if __name__ == "__main__":
    setup = LangflowSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)
