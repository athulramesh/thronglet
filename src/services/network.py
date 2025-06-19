import socket
import json
import threading
import time
import uuid
import ipaddress
from typing import Dict, List, Optional, Callable, Any
import logging
from ..infrastructure.network_protocol import NetworkMessage, MessageType, CreatureMigrationData
from config.network_config import *


class NetworkPeer:
    def __init__(self, host: str, port: int, machine_id: str):
        self.host = host
        self.port = port
        self.machine_id = machine_id
        self.last_seen = time.time()
        self.population_count = 0
        self.available_food = 0

    def update_status(self, population: int, food: int):
        self.population_count = population
        self.available_food = food
        self.last_seen = time.time()

    def is_alive(self) -> bool:
        return time.time() - self.last_seen < PEER_TIMEOUT

    def migration_attractiveness(self) -> float:
        """Calculate how attractive this peer is for migration"""
        # Prefer peers with lower population and more food
        if self.population_count == 0:
            return 1.0
        food_factor = min(self.available_food / 50.0, 1.0)
        population_factor = max(1.0 - (self.population_count / 50.0), 0.1)
        return (food_factor + population_factor) / 2.0


class NetworkManager:
    def __init__(self, simulation_engine=None):
        self.simulation = simulation_engine
        self.machine_id = socket.gethostname()
        self.peers: Dict[str, NetworkPeer] = {}
        self.running = False

        # Network threads
        self._discovery_thread = None
        self._heartbeat_thread = None
        self._comm_server_thread = None
        self._migration_thread = None

        # Sockets
        self._discovery_socket = None
        self._comm_socket = None

        # Message handlers
        self.message_handlers = {
            MessageType.DISCOVERY: self._handle_discovery,
            MessageType.DISCOVERY_RESPONSE: self._handle_discovery_response,
            MessageType.HEARTBEAT: self._handle_heartbeat,
            MessageType.CREATURE_MIGRATION: self._handle_creature_migration,
            MessageType.CREATURE_MIGRATION_ACK: self._handle_migration_ack,
        }

        self.logger = logging.getLogger(__name__)

    def start(self):
        """Start all network services"""
        if self.running:
            return

        self.running = True

        # Start discovery service
        self._start_discovery()

        # Start communication server
        self._start_communication_server()

        # Start heartbeat
        self._start_heartbeat()

        # Start migration manager
        self._start_migration_manager()

        self.logger.info(f"Network services started for machine {
                         self.machine_id}")

    def stop(self):
        """Stop all network services"""
        self.running = False

        if self._discovery_socket:
            self._discovery_socket.close()
        if self._comm_socket:
            self._comm_socket.close()

        # Wait for threads to finish
        for thread in [self._discovery_thread, self._heartbeat_thread,
                       self._comm_server_thread, self._migration_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=2)

        self.logger.info("Network services stopped")

    def _is_safe_network(self, ip: str) -> bool:
        """Check if IP is in allowed network ranges"""
        try:
            ip_addr = ipaddress.ip_address(ip)
            for network in ALLOWED_NETWORKS:
                if ip_addr in ipaddress.ip_network(network):
                    return True
            return False
        except ValueError:
            return False

    def _start_discovery(self):
        """Start UDP discovery service"""
        self._discovery_thread = threading.Thread(target=self._discovery_loop)
        self._discovery_thread.daemon = True
        self._discovery_thread.start()

    def _discovery_loop(self):
        """UDP broadcast discovery loop"""
        try:
            # Setup UDP socket for discovery
            self._discovery_socket = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM)
            self._discovery_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._discovery_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._discovery_socket.bind(('', DISCOVERY_PORT))
            self._discovery_socket.settimeout(1.0)

            last_broadcast = 0

            while self.running:
                # Send discovery broadcast
                if time.time() - last_broadcast > DISCOVERY_INTERVAL:
                    self._send_discovery_broadcast()
                    last_broadcast = time.time()

                # Listen for discovery messages
                try:
                    data, addr = self._discovery_socket.recvfrom(1024)
                    if self._is_safe_network(addr[0]) and addr[0] != self._get_local_ip():
                        self._handle_discovery_message(
                            data.decode('utf-8'), addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Discovery error: {e}")

        except Exception as e:
            self.logger.error(f"Discovery service error: {e}")

    def _send_discovery_broadcast(self):
        """Send discovery broadcast message"""
        message = NetworkMessage(
            message_type=MessageType.DISCOVERY,
            sender_id=self.machine_id,
            recipient_id=None,
            timestamp=time.time(),
            payload={
                'comm_port': COMMUNICATION_PORT,
                'population': len(self.simulation.creatures) if self.simulation else 0,
                'food': self.simulation.world_state.food if self.simulation else 0,
                'protocol_version': PROTOCOL_VERSION
            },
            message_id=str(uuid.uuid4())
        )

        try:
            broadcast_addr = ('255.255.255.255', DISCOVERY_PORT)
            self._discovery_socket.sendto(
                message.to_json().encode('utf-8'), broadcast_addr)
        except Exception as e:
            self.logger.error(f"Failed to send discovery broadcast: {e}")

    def _handle_discovery_message(self, data: str, addr):
        """Handle incoming discovery message"""
        try:
            message = NetworkMessage.from_json(data)

            if message.message_type == MessageType.DISCOVERY:
                # Respond to discovery
                self._send_discovery_response(addr[0], message)

            # Update peer info
            self._update_peer_info(message, addr[0])

        except Exception as e:
            self.logger.error(f"Error handling discovery message: {e}")

    def _send_discovery_response(self, target_ip: str, original_message: NetworkMessage):
        """Send discovery response"""
        response = NetworkMessage(
            message_type=MessageType.DISCOVERY_RESPONSE,
            sender_id=self.machine_id,
            recipient_id=original_message.sender_id,
            timestamp=time.time(),
            payload={
                'comm_port': COMMUNICATION_PORT,
                'population': len(self.simulation.creatures) if self.simulation else 0,
                'food': self.simulation.world_state.food if self.simulation else 0,
                'protocol_version': PROTOCOL_VERSION
            },
            message_id=str(uuid.uuid4())
        )

        try:
            self._discovery_socket.sendto(
                response.to_json().encode('utf-8'),
                (target_ip, DISCOVERY_PORT)
            )
        except Exception as e:
            self.logger.error(f"Failed to send discovery response: {e}")

    def _update_peer_info(self, message: NetworkMessage, ip: str):
        """Update peer information"""
        if message.sender_id != self.machine_id:  # Don't add ourselves
            comm_port = message.payload.get('comm_port', COMMUNICATION_PORT)

            if message.sender_id not in self.peers:
                self.peers[message.sender_id] = NetworkPeer(
                    host=ip,
                    port=comm_port,
                    machine_id=message.sender_id
                )
                self.logger.info(f"Discovered new peer: {
                                 message.sender_id} at {ip}")

            # Update peer status
            peer = self.peers[message.sender_id]
            peer.update_status(
                message.payload.get('population', 0),
                message.payload.get('food', 0)
            )

    def _start_communication_server(self):
        """Start TCP communication server"""
        self._comm_server_thread = threading.Thread(
            target=self._communication_server_loop)
        self._comm_server_thread.daemon = True
        self._comm_server_thread.start()

    def _communication_server_loop(self):
        """TCP server for reliable communication"""
        try:
            self._comm_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self._comm_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._comm_socket.bind(('', COMMUNICATION_PORT))
            self._comm_socket.listen(5)
            self._comm_socket.settimeout(1.0)

            while self.running:
                try:
                    client_socket, addr = self._comm_socket.accept()
                    if self._is_safe_network(addr[0]):
                        threading.Thread(
                            target=self._handle_communication_client,
                            args=(client_socket,),
                            daemon=True
                        ).start()
                    else:
                        client_socket.close()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Communication server error: {e}")

        except Exception as e:
            self.logger.error(f"Communication server setup error: {e}")

    def _handle_communication_client(self, client_socket):
        """Handle TCP communication client"""
        try:
            # Receive message
            data = client_socket.recv(MAX_MESSAGE_SIZE).decode('utf-8')
            message = NetworkMessage.from_json(data)

            # Handle message
            if message.message_type in self.message_handlers:
                response = self.message_handlers[message.message_type](message)
                if response:
                    client_socket.send(response.to_json().encode('utf-8'))

        except Exception as e:
            self.logger.error(f"Error handling communication client: {e}")
        finally:
            client_socket.close()

    def _start_heartbeat(self):
        """Start heartbeat service"""
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self._heartbeat_thread.daemon = True
        self._heartbeat_thread.start()

    def _heartbeat_loop(self):
        """Send periodic heartbeats and clean up dead peers"""
        while self.running:
            # Clean up dead peers
            dead_peers = [
                peer_id for peer_id, peer in self.peers.items()
                if not peer.is_alive()
            ]

            for peer_id in dead_peers:
                self.logger.info(f"Removing dead peer: {peer_id}")
                del self.peers[peer_id]

            time.sleep(HEARTBEAT_INTERVAL)

    def _start_migration_manager(self):
        """Start creature migration manager"""
        self._migration_thread = threading.Thread(target=self._migration_loop)
        self._migration_thread.daemon = True
        self._migration_thread.start()

    def _migration_loop(self):
        """Manage creature migrations"""
        while self.running:
            try:
                if self.simulation and self.peers:
                    self._attempt_migrations()
            except Exception as e:
                self.logger.error(f"Migration error: {e}")

            time.sleep(MIGRATION_INTERVAL)

    def _attempt_migrations(self):
        """Attempt to migrate creatures to other machines"""
        if not self.simulation or not self.peers:
            return

        # Find creatures eligible for migration
        eligible_creatures = [
            creature for creature in self.simulation.creatures.values()
            if creature.can_migrate()
        ]

        if not eligible_creatures:
            return

        # Select creatures for migration
        import random
        migrants = [
            creature for creature in eligible_creatures
            if random.random() < MIGRATION_CHANCE
        ][:MAX_MIGRATION_SIZE]

        if not migrants:
            return

        # Find best destination
        best_peer = self._find_best_migration_target()
        if not best_peer:
            return

        # Migrate creatures
        for creature in migrants:
            if self._migrate_creature(creature, best_peer):
                self.logger.info(f"Migrated {creature.name} to {
                                 best_peer.machine_id}")

    def _find_best_migration_target(self) -> Optional[NetworkPeer]:
        """Find the best peer for migration"""
        if not self.peers:
            return None

        # Sort peers by attractiveness
        sorted_peers = sorted(
            self.peers.values(),
            key=lambda p: p.migration_attractiveness(),
            reverse=True
        )

        # Return the most attractive peer that's alive
        for peer in sorted_peers:
            if peer.is_alive():
                return peer
        return None

    def _migrate_creature(self, creature, target_peer: NetworkPeer) -> bool:
        """Migrate a creature to target peer (enhanced with logging)"""
        try:
            migration_data = CreatureMigrationData(
                creature_data=creature.prepare_for_migration(),
                migration_reason="seeking_better_conditions"
            )

            message = NetworkMessage(
                message_type=MessageType.CREATURE_MIGRATION,
                sender_id=self.machine_id,
                recipient_id=target_peer.machine_id,
                timestamp=time.time(),
                payload=migration_data.to_dict(),
                message_id=str(uuid.uuid4())
            )

            # Send migration request
            response = self._send_reliable_message(target_peer, message)

            if response and response.message_type == MessageType.CREATURE_MIGRATION_ACK:
                if response.payload.get('accepted', False):
                    # Log successful migration
                    self._log_migration_event({
                        'creature_name': creature.name,
                        'creature_id': creature.id,
                        'from': self.machine_id,
                        'to': target_peer.machine_id,
                        'timestamp': time.time(),
                        'reason': 'seeking_better_conditions'
                    })

                    # Remove creature from local simulation
                    self.simulation.remove_creature(creature.id)
                    return True
                else:
                    self.logger.warning(f"Migration rejected: {
                                        response.payload.get('reason', 'unknown')}")

            return False

        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            return False

    def _log_migration_event(self, event: Dict[str, Any]):
        """Log migration event to file"""
        try:
            from pathlib import Path
            import json

            # Try to use system directory first, fall back to local
            log_dir = Path("/opt/thronglet/data")
            if not log_dir.exists():
                log_dir = Path("data")
            log_dir.mkdir(parents=True, exist_ok=True)

            migration_log = log_dir / "migrations.log"

            with open(migration_log, 'a') as f:
                f.write(f"{time.time()}: {json.dumps(event)}\n")

        except Exception as e:
            self.logger.error(f"Failed to log migration event: {e}")

    def _send_reliable_message(self, peer: NetworkPeer, message: NetworkMessage) -> Optional[NetworkMessage]:
        """Send message via TCP and wait for response"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(MESSAGE_TIMEOUT)
            sock.connect((peer.host, peer.port))

            # Send message
            sock.send(message.to_json().encode('utf-8'))

            # Wait for response
            response_data = sock.recv(MAX_MESSAGE_SIZE).decode('utf-8')
            response = NetworkMessage.from_json(response_data)

            sock.close()
            return response

        except Exception as e:
            self.logger.error(f"Failed to send reliable message: {e}")
            return None

    def _handle_discovery(self, message: NetworkMessage) -> Optional[NetworkMessage]:
        """Handle discovery message"""
        # Discovery responses are sent via UDP
        return None

    def _handle_discovery_response(self, message: NetworkMessage) -> Optional[NetworkMessage]:
        """Handle discovery response"""
        # Already handled in discovery loop
        return None

    def _handle_heartbeat(self, message: NetworkMessage) -> NetworkMessage:
        """Handle heartbeat message with optional detailed status request"""
        payload = {
            'population': len(self.simulation.creatures) if self.simulation else 0,
            'food': self.simulation.world_state.food if self.simulation else 0
        }

        # Check if detailed status is requested
        if message.payload.get('request_detailed_status'):
            payload.update({
                'max_population': self.simulation.world_state.max_population if self.simulation else 50,
                'max_food': self.simulation.world_state.max_food if self.simulation else 100,
                'temperature': self.simulation.world_state.temperature if self.simulation else 20,
                'state_counts': self._get_local_state_counts() if self.simulation else {}
            })

        return NetworkMessage(
            message_type=MessageType.HEARTBEAT,
            sender_id=self.machine_id,
            recipient_id=message.sender_id,
            timestamp=time.time(),
            payload=payload,
            message_id=str(uuid.uuid4())
        )

    def _get_local_state_counts(self) -> Dict[str, int]:
        """Get count of creatures in each state for local machine"""
        if not self.simulation:
            return {}

        state_counts = {}
        for creature in self.simulation.creatures.values():
            state = creature.state.value
            state_counts[state] = state_counts.get(state, 0) + 1
        return state_counts

    def _handle_creature_migration(self, message: NetworkMessage) -> NetworkMessage:
        """Handle incoming creature migration"""
        try:
            if not self.simulation:
                return self._create_migration_response(False, "No simulation running")

            migration_data = CreatureMigrationData.from_dict(message.payload)

            # Check if we can accept the creature
            if not self.simulation.world_state.can_support_creature():
                return self._create_migration_response(False, "Population limit reached")

            # Create creature from migration data
            from ..domain.creature import Creature
            migrated_creature = Creature.from_migration_data(
                migration_data.creature_data,
                self.machine_id
            )

            # Add to simulation
            self.simulation.creatures[migrated_creature.id] = migrated_creature
            self.simulation.world_state.population_count += 1

            self.logger.info(f"Accepted migrated creature: {
                             migrated_creature.name} from {message.sender_id}")

            return self._create_migration_response(True, "Migration accepted")

        except Exception as e:
            self.logger.error(f"Error handling creature migration: {e}")
            return self._create_migration_response(False, f"Error: {str(e)}")

    def _create_migration_response(self, accepted: bool, reason: str) -> NetworkMessage:
        """Create migration response message"""
        return NetworkMessage(
            message_type=MessageType.CREATURE_MIGRATION_ACK,
            sender_id=self.machine_id,
            recipient_id=None,  # Will be set by caller
            timestamp=time.time(),
            payload={
                'accepted': accepted,
                'reason': reason
            },
            message_id=str(uuid.uuid4())
        )

    def _handle_migration_ack(self, message: NetworkMessage) -> Optional[NetworkMessage]:
        """Handle migration acknowledgment"""
        # Migration acks are handled by the migration initiator
        return None

    def _get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            # Connect to a remote address to determine local IP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            local_ip = sock.getsockname()[0]
            sock.close()
            return local_ip
        except:
            return "127.0.0.1"

    def get_connected_peers(self) -> List[NetworkPeer]:
        """Get list of active network peers"""
        return [peer for peer in self.peers.values() if peer.is_alive()]

    def get_network_stats(self) -> Dict:
        """Get network statistics"""
        peers = self.get_connected_peers()
        return {
            'machine_id': self.machine_id,
            'connected_peers': len(peers),
            'peer_details': [
                {
                    'machine_id': peer.machine_id,
                    'host': peer.host,
                    'population': peer.population_count,
                    'food': peer.available_food,
                    'last_seen': peer.last_seen
                }
                for peer in peers
            ]
        }
