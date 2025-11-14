#!/usr/bin/env python3
"""
CI/CD Setup Script for ISD2 Appointment System
Run this script to set up the CI/CD environment
"""

import os
import sys

def check_environment():
    """Check if all required files exist."""
    required_files = [
        '.github/workflows/python-app.yml',
        'requirements.txt',
        'requirements-dev.txt',
        '.codecov.yml',
        'app.py',
        'config.py',
        'run.py',
        'tests/',
        'routes/',
        'utils/'
    ]
    
    print("🔍 Checking project structure...")
    missing_files = []
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    else:
        print("✅ All required files present")
        return True

def display_next_steps():
    """Display next steps for CI/CD setup."""
    print("\n🎯 NEXT STEPS FOR CI/CD SETUP:")
    print("=" * 50)
    print("1. Commit and push these new files:")
    print("   git add .github/workflows/python-app.yml requirements-dev.txt .codecov.yml setup_ci.py")
    print("   git commit -m 'feat: Add CI/CD pipeline with GitHub Actions'")
    print("   git push origin main")
    print()
    print("2. Set up Codecov (optional but recommended):")
    print("   - Go to https://codecov.io")
    print("   - Sign in with GitHub")
    print("   - Add your repository")
    print("   - Get the upload token")
    print()
    print("3. Monitor your first workflow run:")
    print("   - Go to your GitHub repository")
    print("   - Click on 'Actions' tab")
    print("   - Watch the workflow execution")
    print()
    print("4. Add badges to your README.md:")
    print("   Copy the badge URLs from GitHub Actions and Codecov")

def main():
    print("🚀 ISD2 CI/CD Setup Script")
    print("=" * 40)
    
    if check_environment():
        display_next_steps()
        return 0
    else:
        print("\n❌ Please create the missing files before setting up CI/CD")
        return 1

if __name__ == "__main__":
    sys.exit(main())