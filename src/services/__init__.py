"""
Service layer - Application services and orchestration.

Contains the core application logic:
- Simulation engine for creature lifecycle management
- Network services for distributed communication
- IPC communication between daemon and CLI
"""

from .simulation import SimulationEngine
from .network import NetworkManager, NetworkPeer
from .daemon_server import DaemonServer
from .daemon_client import DaemonClient

__all__ = [
    "SimulationEngine",
    "NetworkManager",
    "NetworkPeer",
    "DaemonServer",
    "DaemonClient"
]
