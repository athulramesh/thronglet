import socket
import json
import threading
from typing import Dict, Any
import logging
import time


class DaemonServer:
    def __init__(self, simulation_engine, port: int = 7892):
        self.simulation = simulation_engine
        self.port = port
        self.running = False
        self.server_socket = None
        self.server_thread = None
        self.logger = logging.getLogger(__name__)

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
        elif command == 'network_overview':  # NEW COMMAND
            return self._get_network_overview()
        elif command == 'stats':
            return self._get_detailed_stats()
        elif command == 'feed_all':
            return self._feed_all_creatures()
        elif command == 'force_reproduce':
            creature_id = request.get('creature_id')
            return self._force_reproduction(creature_id)
        elif command == 'force_migration':
            creature_name = request.get('creature_name')
            return self._force_migration(creature_name)
        else:
            return {"error": f"Unknown command: {command}"}

    def _get_network_overview(self) -> Dict[str, Any]:
        """Get comprehensive network overview including all peer data"""
        try:
            # Start with local machine data
            local_data = {
                self.simulation.get_machine_id(): {
                    'host': 'localhost',
                    'population': len(self.simulation.creatures),
                    'max_population': self.simulation.world_state.max_population,
                    'food': self.simulation.world_state.food,
                    'max_food': self.simulation.world_state.max_food,
                    'temperature': self.simulation.world_state.temperature,
                    'last_seen': time.time(),
                    'is_local': True,
                    'state_counts': self._get_state_counts()
                }
            }

            # Collect data from all connected peers
            ecosystem_data = local_data.copy()

            if self.simulation.network_manager:
                peers = self.simulation.network_manager.get_connected_peers()

                for peer in peers:
                    # Query each peer for their detailed status
                    peer_data = self._query_peer_status(peer)
                    if peer_data:
                        ecosystem_data[peer.machine_id] = {
                            'host': peer.host,
                            'population': peer_data.get('population', peer.population_count),
                            'max_population': peer_data.get('max_population', 50),
                            'food': peer_data.get('food', peer.available_food),
                            'max_food': peer_data.get('max_food', 100),
                            'temperature': peer_data.get('temperature', 20),
                            'last_seen': peer.last_seen,
                            'is_local': False,
                            'state_counts': peer_data.get('state_counts', {})
                        }

            # Get migration activity data
            migration_activity = self._get_migration_activity()

            return {
                'ecosystem_data': ecosystem_data,
                'migration_activity': migration_activity,
                'timestamp': time.time()
            }

        except Exception as e:
            self.logger.error(f"Error getting network overview: {e}")
            return {"error": f"Failed to get network overview: {str(e)}"}

    def _query_peer_status(self, peer) -> Dict[str, Any]:
        """Query a specific peer for detailed status information"""
        try:
            if not self.simulation.network_manager:
                return None

            # Create status request message
            from ..infrastructure.network_protocol import NetworkMessage, MessageType
            import uuid

            status_request = NetworkMessage(
                message_type=MessageType.HEARTBEAT,  # Reuse heartbeat for status
                sender_id=self.simulation.get_machine_id(),
                recipient_id=peer.machine_id,
                timestamp=time.time(),
                payload={'request_detailed_status': True},
                message_id=str(uuid.uuid4())
            )

            # Send request and get response
            response = self.simulation.network_manager._send_reliable_message(
                peer, status_request)

            if response and response.payload:
                return response.payload

            return None

        except Exception as e:
            self.logger.error(f"Error querying peer {peer.machine_id}: {e}")
            return None

    def _get_state_counts(self) -> Dict[str, int]:
        """Get count of creatures in each state"""
        state_counts = {}
        for creature in self.simulation.creatures.values():
            state = creature.state.value
            state_counts[state] = state_counts.get(state, 0) + 1
        return state_counts

    def _get_migration_activity(self) -> Dict[str, Any]:
        """Get migration activity statistics"""
        # This would ideally read from a migration log
        # For now, return basic data that could be enhanced later

        migration_data = {
            'total_migrations': 0,
            'recent_migrations': []
        }

        # Check if we have migration logs
        try:
            from pathlib import Path
            migration_log = Path("/opt/thronglet/data/migrations.log")
            if not migration_log.exists():
                migration_log = Path("data/migrations.log")

            if migration_log.exists():
                # Read recent migration events
                with open(migration_log, 'r') as f:
                    lines = f.readlines()

                migration_data['total_migrations'] = len(lines)

                # Parse recent migrations (last 10)
                recent_lines = lines[-10:] if len(lines) > 10 else lines
                for line in recent_lines:
                    try:
                        import json
                        timestamp, event_json = line.strip().split(': ', 1)
                        event = json.loads(event_json)
                        migration_data['recent_migrations'].append(event)
                    except:
                        continue  # Skip malformed lines

        except Exception as e:
            self.logger.error(f"Error reading migration activity: {e}")

        return migration_data

    def _force_migration(self, creature_name: str = None) -> Dict[str, Any]:
        """Force migration of a specific creature"""
        # Debug logging
        self.logger.info(f"Force migration requested for: {creature_name}")
        self.logger.info(f"Network manager available: {
                         self.simulation.network_manager is not None}")

        if not hasattr(self.simulation, 'network_manager') or self.simulation.network_manager is None:
            return {"error": "Network manager not available. Make sure daemon was started properly."}

        peers = self.simulation.network_manager.get_connected_peers()
        self.logger.info(f"Connected peers: {len(peers)}")

        if not peers:
            return {"error": "No connected peers for migration. Start daemon on another machine first."}

        # Find creature to migrate
        target_creature = None
        if creature_name:
            # Find by name
            for creature in self.simulation.creatures.values():
                if creature.name == creature_name:
                    target_creature = creature
                    break
            if not target_creature:
                available_names = [
                    c.name for c in self.simulation.creatures.values()]
                return {"error": f"Creature '{creature_name}' not found. Available: {available_names}"}
        else:
            # Find random eligible creature
            eligible = [c for c in self.simulation.creatures.values()
                        if c.can_migrate()]
            if eligible:
                import random
                target_creature = random.choice(eligible)

        if not target_creature:
            return {"error": "No eligible creatures for migration. Creatures must be age > 50, energy > 30, and not dying/reproducing."}

        if not target_creature.can_migrate():
            return {"error": f"Creature {target_creature.name} is not eligible for migration (age: {target_creature.age}, energy: {target_creature.energy}, state: {target_creature.state.value})"}

        # Attempt migration
        best_peer = self.simulation.network_manager._find_best_migration_target()
        if not best_peer:
            return {"error": "No suitable migration target found"}

        self.logger.info(f"Attempting migration of {
                         target_creature.name} to {best_peer.machine_id}")
        success = self.simulation.network_manager._migrate_creature(
            target_creature, best_peer)

        return {
            "success": success,
            "message": f"{'Successfully migrated' if success else 'Failed to migrate'} {target_creature.name} to {best_peer.machine_id}"
        }

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

    def _get_network_status(self) -> Dict[str, Any]:
        """Get network status including peer information"""
        network_status = self.simulation.get_network_status()

        return {
            "machine_id": network_status['machine_id'],
            "connected_peers": network_status['connected_peers'],
            "peers": [
                f"{peer['machine_id']} ({
                    peer['host']}) - Pop: {peer['population']}, Food: {peer['food']}"
                for peer in network_status['peer_details']
            ]
        }
