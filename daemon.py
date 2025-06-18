#!/usr/bin/env python3
import signal
import sys
import logging
from src.services.simulation import SimulationEngine
from src.services.network import NetworkManager
from src.services.daemon_server import DaemonServer


def main():
    logging.basicConfig(level=logging.INFO)

    simulation = SimulationEngine()
    network = NetworkManager()
    daemon_server = DaemonServer(simulation)

    def shutdown_handler(signum, frame):
        print("Shutting down...")
        daemon_server.stop()
        simulation.stop()
        network.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Start services
    simulation.start()
    network.start()
    daemon_server.start()

    print("Thronglet daemon started. Press Ctrl+C to stop.")

    # Keep alive
    try:
        signal.pause()
    except KeyboardInterrupt:
        shutdown_handler(None, None)


if __name__ == "__main__":
    main()
