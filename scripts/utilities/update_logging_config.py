#!/usr/bin/env python
"""Update logging configuration in .env file to consolidate logs."""
import os
import re
from pathlib import Path

def update_env_file():
    """Update the .env file to configure consolidated logging."""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("No .env file found. Creating a new one with consolidated logging settings.")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("# Consolidated Logging Configuration\n")
            f.write("ENHANCED_LOGGING_ENABLED=true\n")
            f.write("LOG_STRUCTURED_FORMAT=true\n")
            f.write("LOG_MAX_FILE_SIZE_MB=20\n")
            f.write("LOG_ROTATION_BACKUP_COUNT=3\n")
            print("Created .env file with consolidated logging settings.")
        return
    
    # Read existing .env file
    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if logging settings already exist
    log_settings = {
        "ENHANCED_LOGGING_ENABLED": "true",
        "LOG_STRUCTURED_FORMAT": "true",
        "LOG_MAX_FILE_SIZE_MB": "20",
        "LOG_ROTATION_BACKUP_COUNT": "3"
    }
    
    modified = False
    new_content = content
    
    # Update or add each setting
    for key, value in log_settings.items():
        pattern = re.compile(f"^{key}=.*$", re.MULTILINE)
        if pattern.search(content):
            # Update existing setting
            new_content = pattern.sub(f"{key}={value}", new_content)
            modified = True
        else:
            # Add new setting
            if not new_content.endswith("\n"):
                new_content += "\n"
            new_content += f"{key}={value}\n"
            modified = True
    
    if modified:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Updated .env file with consolidated logging settings.")
    else:
        print("No changes needed in .env file.")

if __name__ == "__main__":
    update_env_file()
