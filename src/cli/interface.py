import argparse
import sys
from typing import List
from ..services.daemon_client import DaemonClient


class ThrongletCLI:
    def __init__(self):
        self.daemon_client = DaemonClient()

    def status(self):
        """Show local population status"""
        if not self.daemon_client.is_daemon_running():
            print("Error: Daemon is not running. Start with: python daemon.py")
            return

        response = self.daemon_client.send_command("status")
        if not response or "error" in response:
            print(f"Error getting status: {
                  response.get('error', 'Unknown error')}")
            return

        print(f"=== Thronglet Status ===")
        print(f"Population: {response['population']
                             }/{response['max_population']}")
        print(f"Food Available: {response['food']}/{response['max_food']}")
        print(f"Temperature: {response['temperature']}°C")
        print(f"Machine ID: {response['machine_id']}")

        print(f"\nCreature States:")
        for state, count in response['state_counts'].items():
            print(f"  {state.capitalize()}: {count}")

    def list_creatures(self):
        """List all creatures with details"""
        if not self.daemon_client.is_daemon_running():
            print("Error: Daemon is not running. Start with: python daemon.py")
            return

        response = self.daemon_client.send_command("list")
        if not response or "error" in response:
            print(f"Error listing creatures: {
                  response.get('error', 'Unknown error')}")
            return

        creatures = response['creatures']
        print(f"=== Creatures ({response['count']}) ===")

        for creature in creatures:
            age_str = f"{creature['age']}/{creature['max_age']}"
            print(f"{creature['name']} ({creature['id'][:8]})")
            print(f"  Age: {age_str} | Energy: {
                  creature['energy']} | Hunger: {creature['hunger']}")
            print(f"  State: {creature['state']} | Happiness: {
                  creature['happiness']}")
            print()

    def network_status(self):
        """Show network connectivity"""
        if not self.daemon_client.is_daemon_running():
            print("Error: Daemon is not running. Start with: python daemon.py")
            return

        response = self.daemon_client.send_command("network")
        if not response or "error" in response:
            print(f"Error getting network status: {
                  response.get('error', 'Unknown error')}")
            return

        print(f"=== Network Status ===")
        print(f"Machine ID: {response['machine_id']}")
        print(f"Connected Peers: {response['connected_peers']}")

        for peer in response['peers']:
            print(f"  {peer}")

    def add_creature(self, name: str = None):
        """Add new creature"""
        if not self.daemon_client.is_daemon_running():
            print("Error: Daemon is not running. Start with: python daemon.py")
            return

        response = self.daemon_client.send_command("add", name=name)
        if not response or "error" in response:
            print(f"Error adding creature: {
                  response.get('error', 'Unknown error')}")
            return

        creature = response['creature']
        print(f"Created creature: {creature['name']} ({creature['id'][:8]})")

    def run(self, args: List[str]):
        """Main CLI entry point"""
        parser = argparse.ArgumentParser(
            description='Thronglet Virtual Pet Ecosystem')
        subparsers = parser.add_subparsers(
            dest='command', help='Available commands')

        # Status command
        subparsers.add_parser('status', help='Show local population status')

        # List command
        subparsers.add_parser('list', help='List all creatures')

        # Network command
        subparsers.add_parser('network', help='Show network status')

        # Add creature command
        add_parser = subparsers.add_parser('add', help='Add new creature')
        add_parser.add_argument('name', nargs='?', help='Creature name')

        parsed_args = parser.parse_args(args)

        if parsed_args.command == 'status':
            self.status()
        elif parsed_args.command == 'list':
            self.list_creatures()
        elif parsed_args.command == 'network':
            self.network_status()
        elif parsed_args.command == 'add':
            self.add_creature(parsed_args.name)
        else:
            parser.print_help()
