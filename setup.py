#!/usr/bin/env python3
"""
Setup script for Thronglet distributed virtual pet ecosystem
"""

import os
import sys
from pathlib import Path
import subprocess


def create_directories():
    """Create required directories"""
    directories = [
        "/opt/thronglet/data",
        "/opt/thronglet/logs",
        "/opt/thronglet/config"
    ]

    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"✓ Created directory: {directory}")
        except PermissionError:
            print(f"⚠ Could not create {
                  directory} - you may need to run with sudo")
            # Try local directory instead
            local_dir = Path("data") / Path(directory).name
            local_dir.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created local directory: {local_dir}")


def check_python_version():
    """Ensure Python 3.8+"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{
          sys.version_info.minor} detected")


def setup_permissions():
    """Set up file permissions"""
    try:
        # Make scripts executable
        scripts = ["daemon.py", "main.py", "setup.py"]
        for script in scripts:
            if Path(script).exists():
                os.chmod(script, 0o755)
                print(f"✓ Made {script} executable")

        # Set data directory permissions if it exists
        if Path("/opt/thronglet").exists():
            os.chmod("/opt/thronglet", 0o755)
            os.chmod("/opt/thronglet/data", 0o755)
            os.chmod("/opt/thronglet/logs", 0o755)
            print("✓ Set directory permissions")

    except PermissionError:
        print("⚠ Could not set all permissions. You may need to run with sudo.")


def test_network_ports():
    """Test if required network ports are available"""
    import socket

    ports = [7890, 7891, 7892]
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            print(f"✓ Port {port} is available")
        except OSError:
            print(f"⚠ Port {port} may be in use")


def create_config_directory():
    """Create config directory and files in project"""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)

    # Create network_config.py if it doesn't exist
    network_config_file = config_dir / "network_config.py"
    if not network_config_file.exists():
        network_config_content = '''"""
Network configuration for Thronglet ecosystem.
Safe for home networks - uses local discovery only.
"""

# Network ports
DISCOVERY_PORT = 7890
COMMUNICATION_PORT = 7891
DAEMON_IPC_PORT = 7892

# Discovery settings
DISCOVERY_INTERVAL = 30  # seconds
DISCOVERY_TIMEOUT = 5    # seconds
HEARTBEAT_INTERVAL = 15  # seconds
PEER_TIMEOUT = 60       # seconds

# Migration settings
MIGRATION_CHANCE = 0.1   # 10% chance per eligible creature per migration cycle
MIGRATION_INTERVAL = 120 # seconds between migration attempts
MAX_MIGRATION_SIZE = 3   # max creatures per migration batch

# Security settings (for home network safety)
ALLOWED_NETWORKS = [
    "192.168.0.0/16",    # Standard home networks
    "10.0.0.0/8",        # Private networks
    "172.16.0.0/12",     # Private networks
    "127.0.0.0/8"        # Localhost
]

# Protocol settings
MESSAGE_TIMEOUT = 10     # seconds
MAX_MESSAGE_SIZE = 64000 # bytes
PROTOCOL_VERSION = "1.0"
'''
        with open(network_config_file, 'w') as f:
            f.write(network_config_content)
        print(f"✓ Created {network_config_file}")

    # Create __init__.py in config
    init_file = config_dir / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        print(f"✓ Created {init_file}")


def check_project_structure():
    """Verify project structure"""
    required_files = [
        "src/domain/creature.py",
        "src/services/simulation.py",
        "daemon.py",
        "main.py"
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print("⚠ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        print("Please ensure you have the complete Thronglet project structure.")
        return False

    print("✓ Project structure looks good")
    return True


def main():
    print("=== Thronglet Setup ===")
    print("Setting up distributed virtual pet ecosystem...\n")

    check_python_version()

    if not check_project_structure():
        print("\n❌ Setup failed due to missing files")
        return

    create_config_directory()
    create_directories()
    setup_permissions()
    test_network_ports()

    print("\n" + "="*50)
    print("✅ Setup complete!")
    print("\nTo start the daemon:")
    print("  python3 daemon.py")
    print("\nTo use the CLI:")
    print("  python3 main.py status")
    print("  python3 main.py list")
    print("  python3 main.py network")
    print("  python3 main.py add MyCreature")
    print("\nFor multi-machine setup:")
    print("  1. Run setup.py on each machine")
    print("  2. Ensure all machines are on the same network")
    print("  3. Start daemon.py on each machine")
    print("  4. Creatures will automatically migrate between machines!")
    print("\nData will be stored in:")
    if Path("/opt/thronglet").exists():
        print("  /opt/thronglet/data/")
    else:
        print("  ./data/ (local directory)")


if __name__ == "__main__":
    main()
