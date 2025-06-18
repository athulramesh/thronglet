import socket
import json
import threading
from typing import Dict, Any


class DaemonServer:
    def __init__(self, simulation_engine, port: int = 7892):
        self.simulation = simulation_engine
        self.port = port
        self.running = False
        self.server_socket = None
        self.server_thread = None

    def start(self):
        """Start the IPC server"""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('localhost', self.port))
        self.server_socket.listen(5)

        self.server_thread = threading.Thread(target=self._server_loop)
        self.server_thread.daemon = True
        self.server_thread.start()
        print(f"Daemon IPC server started on port {self.port}")

    def stop(self):
        """Stop the IPC server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if self.server_thread:
            self.server_thread.join()

    def _server_loop(self):
        """Main server loop"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket,),
                    daemon=True
                ).start()
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    print(f"Server error: {e}")

    def _handle_client(self, client_socket):
        """Handle individual client requests"""
        try:
            # Receive request
            data = client_socket.recv(4096).decode('utf-8')
            request = json.loads(data)

            # Process request
            response = self._process_request(request)

            # Send response
            client_socket.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            error_response = {"error": str(e)}
            client_socket.send(json.dumps(error_response).encode('utf-8'))
        finally:
            client_socket.close()

    def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming requests"""
        command = request.get('command')

        if command == 'status':
            return self._get_status()
        elif command == 'list':
            return self._list_creatures()
        elif command == 'add':
            name = request.get('name')
            return self._add_creature(name)
        elif command == 'network':
            return self._get_network_status()
        elif command == 'stats':
            return self._get_detailed_stats()
        elif command == 'feed_all':
            return self._feed_all_creatures()
        elif command == 'force_reproduce':
            creature_id = request.get('creature_id')
            return self._force_reproduction(creature_id)
        else:
            return {"error": f"Unknown command: {command}"}

    def _get_status(self) -> Dict[str, Any]:
        """Get simulation status"""
        creatures = self.simulation.creatures
        world = self.simulation.world_state

        # State breakdown
        state_counts = {}
        for creature in creatures.values():
            state = creature.state.value
            state_counts[state] = state_counts.get(state, 0) + 1

        return {
            "population": len(creatures),
            "max_population": world.max_population,
            "food": world.food,
            "max_food": world.max_food,
            "temperature": world.temperature,
            "machine_id": self.simulation.get_machine_id(),
            "state_counts": state_counts
        }

    def _list_creatures(self) -> Dict[str, Any]:
        """List all creatures"""
        creatures = self.simulation.creatures
        creature_list = []

        for creature in creatures.values():
            creature_list.append({
                "id": creature.id,
                "name": creature.name,
                "age": creature.age,
                "max_age": creature.max_age,
                "energy": creature.energy,
                "hunger": creature.hunger,
                "happiness": creature.happiness,
                "state": creature.state.value
            })

        return {
            "count": len(creatures),
            "creatures": creature_list
        }

    def _add_creature(self, name: str = None) -> Dict[str, Any]:
        """Add new creature"""
        creature = self.simulation.add_creature(name)
        return {
            "success": True,
            "creature": {
                "id": creature.id,
                "name": creature.name
            }
        }

    def _get_network_status(self) -> Dict[str, Any]:
        """Get network status"""
        # This would integrate with NetworkManager
        return {
            "machine_id": self.simulation.get_machine_id(),
            "connected_peers": 0,  # Placeholder
            "peers": []
        }

    def _get_detailed_stats(self) -> Dict[str, Any]:
        """Get comprehensive simulation statistics"""
        return self.simulation.get_simulation_stats()

    def _feed_all_creatures(self) -> Dict[str, Any]:
        """Emergency feeding for all creatures"""
        fed_count = self.simulation.feed_all_creatures()
        return {
            "success": True,
            "fed_count": fed_count,
            "message": f"Fed {fed_count} hungry creatures"
        }

    def _force_reproduction(self, creature_id: str) -> Dict[str, Any]:
        """Force a creature to reproduce"""
        if not creature_id:
            return {"error": "creature_id required"}

        success = self.simulation.force_reproduction(creature_id)
        return {
            "success": success,
            "message": f"Reproduction {'initiated' if success else 'failed'} for creature {creature_id[:8]}"
        }
