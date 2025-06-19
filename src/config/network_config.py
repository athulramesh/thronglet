"""
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
MIGRATION_INTERVAL = 120  # seconds between migration attempts
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
MAX_MESSAGE_SIZE = 64000  # bytes
PROTOCOL_VERSION = "1.0"
