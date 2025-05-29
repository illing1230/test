#!/usr/bin/env python3
"""
Langflow Setup Verification Script
This script verifies that Langflow has been properly installed and configured.
"""

import os
import sys
import time
import requests
import subprocess
import platform
from pathlib import Path
from typing import List, Tuple, Optional
import json

class SetupVerifier:
    def __init__(self):
        self.project_dir = Path.cwd()
        self.langflow_dir = self.project_dir / "langflow"
        self.passed_checks = 0
        self.total_checks = 0
        self.issues = []
        
    def print_header(self):
        """Print verification header"""
        print("🔍 Langflow Setup Verification")
        print("=" * 50)
        print()
    
    def check_prerequisite(self, command: str, description: str) -> bool:
        """Check if a prerequisite command is available"""
        self.total_checks += 1
        
        try:
            result = subprocess.run([command, '--version'], 
                                 capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {description}: Available")
                self.passed_checks += 1
                return True
            else:
                print(f"❌ {description}: Not working properly")
                self.issues.append(f"{description} command failed")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"❌ {description}: Not found")
            self.issues.append(f"{description} is not installed")
            return False
    
    def check_python_version(self) -> bool:
        """Check Python version compatibility"""
        self.total_checks += 1
        
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            print(f"✅ Python Version: {version.major}.{version.minor}.{version.micro} (Compatible)")
            self.passed_checks += 1
            return True
        else:
            print(f"❌ Python Version: {version.major}.{version.minor}.{version.micro} (Requires 3.8+)")
            self.issues.append("Python 3.8+ is required")
            return False
    
    def check_directory_structure(self) -> bool:
        """Check if the required directories exist"""
        self.total_checks += 1
        
        required_paths = [
            self.langflow_dir,
            self.langflow_dir / "venv",
        ]
        
        missing_paths = []
        for path in required_paths:
            if not path.exists():
                missing_paths.append(str(path))
        
        if missing_paths:
            print(f"❌ Directory Structure: Missing paths - {', '.join(missing_paths)}")
            self.issues.append("Run setup.py to create required directories")
            return False
        else:
            print("✅ Directory Structure: All required paths exist")
            self.passed_checks += 1
            return True
    
    def check_virtual_environment(self) -> bool:
        """Check if virtual environment is properly set up"""
        self.total_checks += 1
        
        venv_dir = self.langflow_dir / "venv"
        
        if platform.system() == "Windows":
            python_exe = venv_dir / "Scripts" / "python.exe"
            pip_exe = venv_dir / "Scripts" / "pip.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
            pip_exe = venv_dir / "bin" / "pip"
        
        if python_exe.exists() and pip_exe.exists():
            print("✅ Virtual Environment: Properly configured")
            self.passed_checks += 1
            return True
        else:
            print("❌ Virtual Environment: Missing executables")
            self.issues.append("Virtual environment is not properly set up")
            return False
    
    def check_langflow_installation(self) -> bool:
        """Check if Langflow is properly installed"""
        self.total_checks += 1
        
        venv_dir = self.langflow_dir / "venv"
        
        if platform.system() == "Windows":
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
        
        try:
            # Test langflow import
            result = subprocess.run([
                str(python_exe), '-c', 'import langflow; print(langflow.__version__)'
            ], capture_output=True, text=True, timeout=30, cwd=self.langflow_dir)
            
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✅ Langflow Installation: Version {version}")
                self.passed_checks += 1
                return True
            else:
                print(f"❌ Langflow Installation: Import failed - {result.stderr}")
                self.issues.append("Langflow is not properly installed")
                return False
        except subprocess.TimeoutExpired:
            print("❌ Langflow Installation: Import test timed out")
            self.issues.append("Langflow import test timed out")
            return False
    
    def check_configuration_files(self) -> bool:
        """Check if configuration files exist and are valid"""
        self.total_checks += 1
        
        config_files = [
            "langflow_config.yaml",
            "config.py"
        ]
        
        missing_files = []
        for config_file in config_files:
            if not (self.project_dir / config_file).exists():
                missing_files.append(config_file)
        
        if missing_files:
            print(f"❌ Configuration Files: Missing - {', '.join(missing_files)}")
            self.issues.append("Some configuration files are missing")
            return False
        else:
            print("✅ Configuration Files: All present")
            self.passed_checks += 1
            return True
    
    def check_database_config(self) -> bool:
        """Check database configuration"""
        self.total_checks += 1
        
        try:
            # Import our config module
            sys.path.insert(0, str(self.project_dir))
            from config import LangflowConfig
            
            config = LangflowConfig()
            db_config = config.get_database_config()
            
            if db_config['url']:
                db_type = "PostgreSQL" if db_config['url'].startswith('postgresql') else "SQLite"
                print(f"✅ Database Configuration: {db_type} configured")
                self.passed_checks += 1
                return True
            else:
                print("❌ Database Configuration: No valid database URL")
                self.issues.append("Database configuration is incomplete")
                return False
        except Exception as e:
            print(f"❌ Database Configuration: Error loading config - {e}")
            self.issues.append("Failed to load database configuration")
            return False
    
    def check_server_startup(self) -> bool:
        """Check if the server can start (without actually starting it)"""
        self.total_checks += 1
        
        venv_dir = self.langflow_dir / "venv"
        
        if platform.system() == "Windows":
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
        
        try:
            # Test if langflow can be imported and run help
            result = subprocess.run([
                str(python_exe), '-m', 'langflow', '--help'
            ], capture_output=True, text=True, timeout=30, cwd=self.langflow_dir)
            
            if result.returncode == 0:
                print("✅ Server Startup: Langflow CLI is functional")
                self.passed_checks += 1
                return True
            else:
                print(f"❌ Server Startup: CLI test failed - {result.stderr}")
                self.issues.append("Langflow CLI is not working")
                return False
        except subprocess.TimeoutExpired:
            print("❌ Server Startup: CLI test timed out")
            self.issues.append("Langflow CLI test timed out")
            return False
    
    def check_port_availability(self, port: int = 7860) -> bool:
        """Check if the default port is available"""
        self.total_checks += 1
        
        import socket
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                print(f"✅ Port Availability: Port {port} is available")
                self.passed_checks += 1
                return True
        except OSError:
            print(f"❌ Port Availability: Port {port} is in use")
            self.issues.append(f"Port {port} is already in use")
            return False
    
    def check_frontend_dependencies(self) -> bool:
        """Check if frontend dependencies are installed"""
        self.total_checks += 1
        
        frontend_dirs = [
            self.langflow_dir / "src" / "frontend",
            self.langflow_dir / "frontend"
        ]
        
        frontend_dir = None
        for dir_path in frontend_dirs:
            if dir_path.exists():
                frontend_dir = dir_path
                break
        
        if not frontend_dir:
            print("✅ Frontend Dependencies: No separate frontend directory found (using built-in)")
            self.passed_checks += 1
            return True
        
        node_modules = frontend_dir / "node_modules"
        package_json = frontend_dir / "package.json"
        
        if package_json.exists():
            if node_modules.exists():
                print("✅ Frontend Dependencies: node_modules installed")
                self.passed_checks += 1
                return True
            else:
                print("❌ Frontend Dependencies: node_modules not found")
                self.issues.append("Frontend dependencies not installed")
                return False
        else:
            print("✅ Frontend Dependencies: No package.json found (using built-in frontend)")
            self.passed_checks += 1
            return True
    
    def perform_integration_test(self) -> bool:
        """Perform a quick integration test by starting server briefly"""
        print("\n🧪 Performing Integration Test...")
        print("Starting Langflow server for testing...")
        
        venv_dir = self.langflow_dir / "venv"
        
        if platform.system() == "Windows":
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
        
        # Start server in background
        try:
            process = subprocess.Popen([
                str(python_exe), '-m', 'langflow', 'run',
                '--host', '127.0.0.1',
                '--port', '7861',  # Use different port to avoid conflicts
                '--no-open-browser'
            ], cwd=self.langflow_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            print("Waiting for server to start...")
            time.sleep(10)
            
            # Test if server is responding
            try:
                response = requests.get('http://127.0.0.1:7861/api/v1/health', timeout=5)
                if response.status_code == 200:
                    print("✅ Integration Test: Server started and responding")
                    integration_success = True
                else:
                    print(f"❌ Integration Test: Server returned status {response.status_code}")
                    integration_success = False
            except requests.exceptions.RequestException as e:
                print(f"❌ Integration Test: Failed to connect to server - {e}")
                integration_success = False
            
            # Stop the server
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            return integration_success
            
        except Exception as e:
            print(f"❌ Integration Test: Failed to start server - {e}")
            return False
    
    def print_summary(self):
        """Print verification summary"""
        print("\n" + "=" * 50)
        print("📊 Verification Summary")
        print("=" * 50)
        
        success_rate = (self.passed_checks / self.total_checks) * 100 if self.total_checks > 0 else 0
        
        print(f"Passed: {self.passed_checks}/{self.total_checks} ({success_rate:.1f}%)")
        
        if self.issues:
            print(f"\n❌ Issues Found ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
        
        if success_rate >= 90:
            print(f"\n🎉 Setup Status: EXCELLENT")
            print("Your Langflow installation is ready to use!")
            print("\nNext steps:")
            print("1. Run './start.sh' to start Langflow")
            print("2. Open http://localhost:7860 in your browser")
        elif success_rate >= 70:
            print(f"\n✅ Setup Status: GOOD")
            print("Your installation is mostly ready, but has some minor issues.")
            print("You can try starting Langflow, but consider fixing the issues above.")
        elif success_rate >= 50:
            print(f"\n⚠️  Setup Status: PARTIAL")
            print("Your installation has significant issues that should be fixed.")
            print("Please address the issues above before starting Langflow.")
        else:
            print(f"\n❌ Setup Status: FAILED")
            print("Your installation has critical issues and needs to be fixed.")
            print("Please run setup.py again or address the issues manually.")
        
        print("\n" + "=" * 50)
    
    def run_verification(self):
        """Run all verification checks"""
        self.print_header()
        
        print("🔧 Checking Prerequisites...")
        self.check_python_version()
        self.check_prerequisite('git', 'Git')
        self.check_prerequisite('node', 'Node.js')
        self.check_prerequisite('npm', 'npm')
        
        print("\n📁 Checking Installation...")
        self.check_directory_structure()
        self.check_virtual_environment()
        self.check_langflow_installation()
        
        print("\n⚙️  Checking Configuration...")
        self.check_configuration_files()
        self.check_database_config()
        
        print("\n🌐 Checking Environment...")
        self.check_port_availability()
        self.check_frontend_dependencies()
        self.check_server_startup()
        
        # Optional integration test
        response = input("\n🧪 Run integration test? This will briefly start the server (y/N): ")
        if response.lower() == 'y':
            self.perform_integration_test()
        
        self.print_summary()


if __name__ == "__main__":
    verifier = SetupVerifier()
    verifier.run_verification()
