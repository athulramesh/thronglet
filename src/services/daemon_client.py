import socket
import json
from typing import Dict, Any, Optional


class DaemonClient:
    def __init__(self, host: str = 'localhost', port: int = 7892):
        self.host = host
        self.port = port

    def send_command(self, command: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Send command to daemon and return response"""
        try:
            # Create request
            request = {"command": command, **kwargs}

            # Connect to daemon
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.host, self.port))

            # Send request
            client_socket.send(json.dumps(request).encode('utf-8'))

            # Receive response
            response_data = client_socket.recv(4096).decode('utf-8')
            response = json.loads(response_data)

            client_socket.close()
            return response

        except Exception as e:
            print(f"Error communicating with daemon: {e}")
            return None

    def is_daemon_running(self) -> bool:
        """Check if daemon is accessible"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(1)
            result = client_socket.connect_ex((self.host, self.port))
            client_socket.close()
            return result == 0
        except:
            return False
