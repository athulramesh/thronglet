#!/usr/bin/env python3
from src.services.daemon_server import DaemonServer
from src.services.network import NetworkManager
from src.services.simulation import SimulationEngine
import signal
import sys
import logging
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("/opt/thronglet/logs")
    if not log_dir.exists():
        # Try local logs directory
        log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "throngletd.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Thronglet daemon...")

    # Initialize services
    simulation = SimulationEngine()
    network = NetworkManager(simulation)  # Pass simulation to network manager
    daemon_server = DaemonServer(simulation)

    # IMPORTANT: Connect simulation and network manager
    simulation.set_network_manager(network)

    # Verify connection
    if simulation.network_manager is None:
        logger.error("Failed to connect network manager to simulation!")
        sys.exit(1)
    else:
        logger.info("✓ Network manager connected to simulation")

    def shutdown_handler(signum, frame):
        logger.info("Shutdown signal received, stopping services...")
        daemon_server.stop()
        simulation.stop()
        network.stop()
        logger.info("Thronglet daemon stopped")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        # Start services in order
        logger.info("Starting simulation engine...")
        simulation.start()

        logger.info("Starting network manager...")
        network.start()

        logger.info("Starting daemon server...")
        daemon_server.start()

        logger.info("Thronglet daemon started successfully")
        logger.info("Services running:")
        logger.info(f"  - Simulation: {len(simulation.creatures)} creatures")
        logger.info(f"  - Network discovery on port 7890")
        logger.info(f"  - Network communication on port 7891")
        logger.info(f"  - IPC server on port 7892")
        logger.info(
            f"  - Network manager: {'Connected' if simulation.network_manager else 'NOT Connected'}")
        logger.info("Press Ctrl+C to stop.")

        # Keep alive
        signal.pause()

    except KeyboardInterrupt:
        shutdown_handler(None, None)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        shutdown_handler(None, None)


if __name__ == "__main__":
    main()
