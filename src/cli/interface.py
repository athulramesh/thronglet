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
            error_msg = response.get(
                'error', 'Unknown error') if response else 'Unknown error'
            print(f"Error listing creatures: {error_msg}")
            return

        creatures = response['creatures']
        print(f"=== Creatures ({response['count']}) ===")

        if not creatures:
            print(
                "No creatures found. Add some with: python main.py add [name]")
            return

        for creature in creatures:
            age_str = f"{creature['age']}/{creature['max_age']}"
            happiness_emoji = self._get_happiness_emoji(creature['happiness'])

            print(f"{creature['name']} ({creature['id'][:8]}) {
                  happiness_emoji}")
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

        if response['peers']:
            for peer in response['peers']:
                print(f"  {peer}")
        else:
            print("  No connected peers (Phase 2 feature)")

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

    def detailed_stats(self):
        """Show comprehensive simulation statistics"""
        if not self.daemon_client.is_daemon_running():
            print("Error: Daemon is not running. Start with: python daemon.py")
            return

        response = self.daemon_client.send_command("stats")
        if not response or "error" in response:
            print(f"Error getting stats: {
                  response.get('error', 'Unknown error')}")
            return

        print(f"=== Detailed Statistics ===")

        # Runtime stats
        runtime = response['runtime']
        print(f"\n📊 Runtime:")
        print(f"  Tick Count: {runtime['tick_count']}")
        print(f"  Births This Session: {runtime['births_this_session']}")
        print(f"  Deaths This Session: {runtime['deaths_this_session']}")

        # World stats
        world = response['world']
        print(f"\n🌍 World State:")
        print(f"  Food: {world['food']}/{world['max_food']}")
        print(f"  Temperature: {world['temperature']}°C")
        print(f"  Population: {
              world['population_count']}/{world['max_population']}")

        # Creature stats
        creatures = response['creatures']
        print(f"\n🐾 Population Demographics:")
        print(f"  Total Population: {creatures['total_population']}")
        print(f"  Average Age: {creatures['average_age']}")
        print(f"  Average Energy: {creatures['average_energy']}")
        print(f"  Average Happiness: {creatures['average_happiness']}")
        print(f"  Average Hunger: {creatures['average_hunger']}")

        # State distribution
        print(f"\n🎭 Creature States:")
        for state, count in creatures['state_distribution'].items():
            print(f"  {state.capitalize()}: {count}")

        # Age distribution
        print(f"\n👶 Age Groups:")
        for age_group, count in creatures['age_distribution'].items():
            print(f"  {age_group.capitalize()}: {count}")

        # Happiness distribution
        if 'happiness_distribution' in creatures:
            print(f"\n😊 Happiness Levels:")
            happiness_emojis = {
                'miserable': '😢', 'sad': '😟', 'content': '😐',
                'happy': '😊', 'ecstatic': '🤩'
            }
            for mood, count in creatures['happiness_distribution'].items():
                emoji = happiness_emojis.get(mood, '😐')
                print(f"  {emoji} {mood.capitalize()}: {count}")

        # Generations
        print(f"\n🧬 Generations:")
        for gen, count in creatures['generations'].items():
            print(f"  {gen.replace('_', ' ').title()}: {count}")

        # Behavior transitions
        if response['behavior_transitions']:
            print(f"\n🔄 State Transitions (This Session):")
            for transition, count in response['behavior_transitions'].items():
                print(f"  {transition}: {count}")

    def feed_all(self):
        """Emergency feeding for all creatures"""
        if not self.daemon_client.is_daemon_running():
            print("Error: Daemon is not running. Start with: python daemon.py")
            return

        response = self.daemon_client.send_command("feed_all")
        if not response or "error" in response:
            print(f"Error feeding creatures: {
                  response.get('error', 'Unknown error')}")
            return

        print(f"✅ {response['message']}")

    def force_reproduce(self, creature_id: str = None):
        """Force a creature to reproduce"""
        if not self.daemon_client.is_daemon_running():
            print("Error: Daemon is not running. Start with: python daemon.py")
            return

        if not creature_id:
            # Get list of creatures to choose from
            list_response = self.daemon_client.send_command("list")
            if not list_response or "error" in list_response:
                print("Error: Could not get creature list")
                return

            creatures = list_response['creatures']
            if not creatures:
                print("No creatures available for reproduction")
                return

            print("Available creatures:")
            for i, creature in enumerate(creatures):
                print(f"  {i+1}. {creature['name']} ({creature['id'][:8]}) - "
                      f"Age: {creature['age']}, Energy: {creature['energy']}")

            try:
                choice = int(input("Select creature number: ")) - 1
                if 0 <= choice < len(creatures):
                    creature_id = creatures[choice]['id']
                else:
                    print("Invalid selection")
                    return
            except (ValueError, KeyboardInterrupt):
                print("Selection cancelled")
                return

        response = self.daemon_client.send_command(
            "force_reproduce", creature_id=creature_id)
        if not response or "error" in response:
            print(f"Error forcing reproduction: {
                  response.get('error', 'Unknown error')}")
            return

        if response['success']:
            print(f"✅ {response['message']}")
        else:
            print(f"❌ {response['message']}")

    def _get_happiness_emoji(self, happiness: int) -> str:
        """Get emoji representation of happiness level"""
        if happiness < 20:
            return "😢"  # miserable
        elif happiness < 40:
            return "😟"  # sad
        elif happiness < 60:
            return "😐"  # content
        elif happiness < 80:
            return "😊"  # happy
        else:
            return "🤩"  # ecstatic

    def run(self, args: List[str]):
        """Main CLI entry point"""
        parser = argparse.ArgumentParser(
            description='Thronglet Virtual Pet Ecosystem',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python main.py status                    # Show population status
  python main.py list                      # List all creatures
  python main.py add "Fluffy"             # Add creature named Fluffy
  python main.py stats                     # Detailed statistics
  python main.py feed_all                  # Emergency feeding
  python main.py reproduce <creature_id>   # Force reproduction
  python main.py network                   # Network status
            """
        )

        subparsers = parser.add_subparsers(
            dest='command', help='Available commands')

        # Status command
        subparsers.add_parser('status', help='Show local population status')

        # List command
        subparsers.add_parser('list', help='List all creatures with details')

        # Network command
        subparsers.add_parser(
            'network', help='Show network connectivity status')

        # Add creature command
        add_parser = subparsers.add_parser(
            'add', help='Add new creature to simulation')
        add_parser.add_argument(
            'name', nargs='?', help='Creature name (optional)')

        # Detailed stats command
        subparsers.add_parser(
            'stats', help='Show comprehensive simulation statistics')

        # Feed all command
        subparsers.add_parser(
            'feed_all', help='Emergency feeding for all hungry creatures')

        # Force reproduction command
        reproduce_parser = subparsers.add_parser(
            'reproduce', help='Force a creature to reproduce')
        reproduce_parser.add_argument('creature_id', nargs='?',
                                      help='Creature ID (will prompt if not provided)')

        # Parse arguments
        parsed_args = parser.parse_args(args)

        # Execute commands
        if parsed_args.command == 'status':
            self.status()
        elif parsed_args.command == 'list':
            self.list_creatures()
        elif parsed_args.command == 'network':
            self.network_status()
        elif parsed_args.command == 'add':
            self.add_creature(parsed_args.name)
        elif parsed_args.command == 'stats':
            self.detailed_stats()
        elif parsed_args.command == 'feed_all':
            self.feed_all()
        elif parsed_args.command == 'reproduce':
            self.force_reproduce(parsed_args.creature_id)
        else:
            parser.print_help()
