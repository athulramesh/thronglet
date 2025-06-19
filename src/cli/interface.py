import argparse
import sys
from typing import List, Dict, Any
from ..services.daemon_client import DaemonClient


class ThrongletCLI:
    def __init__(self):
        self.daemon_client = DaemonClient()

    def network_overview(self):
        """Show comprehensive network-wide view of all machines and creatures"""
        if not self.daemon_client.is_daemon_running():
            print("Error: Daemon is not running. Start with: python daemon.py")
            return

        # Get network status and peer details
        network_response = self.daemon_client.send_command("network_overview")
        if not network_response or "error" in network_response:
            print(f"Error getting network overview: {
                  network_response.get('error', 'Unknown error')}")
            return

        print("=" * 80)
        print("🌐 THRONGLET ECOSYSTEM NETWORK OVERVIEW")
        print("=" * 80)

        ecosystem_data = network_response['ecosystem_data']

        # Network summary
        total_machines = len(ecosystem_data)
        total_population = sum(machine['population']
                               for machine in ecosystem_data.values())
        total_food = sum(machine['food']
                         for machine in ecosystem_data.values())
        avg_temperature = sum(machine['temperature'] for machine in ecosystem_data.values(
        )) / total_machines if total_machines > 0 else 0

        print(f"\n📊 ECOSYSTEM SUMMARY")
        print(f"  Connected Machines: {total_machines}")
        print(f"  Total Population: {total_population}")
        print(f"  Total Food Available: {total_food}")
        print(f"  Average Temperature: {avg_temperature:.1f}°C")

        # Calculate ecosystem health
        health_score = self._calculate_ecosystem_health(ecosystem_data)
        health_emoji = "🟢" if health_score > 0.7 else "🟡" if health_score > 0.4 else "🔴"
        print(f"  Ecosystem Health: {health_emoji} {health_score*100:.1f}%")

        # Machine details
        print(f"\n🖥️  MACHINE STATUS")
        print("-" * 80)

        for machine_id, data in ecosystem_data.items():
            is_local = data.get('is_local', False)
            local_indicator = " (LOCAL)" if is_local else ""

            print(f"\n📍 {machine_id}{local_indicator}")
            print(f"   Address: {data.get('host', 'localhost')}")
            print(f"   Population: {
                  data['population']}/{data.get('max_population', 50)} creatures")
            print(f"   Food: {data['food']}/{data.get('max_food', 100)} units")
            print(f"   Temperature: {data['temperature']}°C")
            print(f"   Last Seen: {
                  self._format_last_seen(data.get('last_seen', 0))}")

            # State distribution
            if 'state_counts' in data and data['state_counts']:
                print(f"   States: ", end="")
                state_emojis = {'idle': '😴', 'hungry': '🍽️',
                                'eating': '😋', 'reproducing': '💕', 'dying': '💀'}
                states = []
                for state, count in data['state_counts'].items():
                    emoji = state_emojis.get(state, '❓')
                    states.append(f"{emoji}{count}")
                print(" | ".join(states))

        # Migration activity
        migration_data = network_response.get('migration_activity', {})
        if migration_data:
            print(f"\n🔄 MIGRATION ACTIVITY")
            print("-" * 40)
            total_migrations = migration_data.get('total_migrations', 0)
            recent_migrations = migration_data.get('recent_migrations', [])

            print(f"Total Migrations This Session: {total_migrations}")
            if recent_migrations:
                print("Recent Migrations:")
                for migration in recent_migrations[-5:]:  # Show last 5
                    print(f"  • {migration['creature_name']}: {
                          migration['from']} → {migration['to']}")

        # Population flow analysis
        print(f"\n📈 POPULATION DYNAMICS")
        print("-" * 40)

        # Find most/least populated machines
        if ecosystem_data:
            most_populated = max(ecosystem_data.items(),
                                 key=lambda x: x[1]['population'])
            least_populated = min(ecosystem_data.items(),
                                  key=lambda x: x[1]['population'])

            print(f"Most Populated: {most_populated[0]} ({
                  most_populated[1]['population']} creatures)")
            print(f"Least Populated: {least_populated[0]} ({
                  least_populated[1]['population']} creatures)")

            # Resource distribution
            most_food = max(ecosystem_data.items(), key=lambda x: x[1]['food'])
            least_food = min(ecosystem_data.items(),
                             key=lambda x: x[1]['food'])

            print(f"Most Food: {most_food[0]} ({most_food[1]['food']} units)")
            print(f"Least Food: {least_food[0]} ({
                  least_food[1]['food']} units)")

        # Recommendations
        recommendations = self._generate_ecosystem_recommendations(
            ecosystem_data)
        if recommendations:
            print(f"\n💡 ECOSYSTEM RECOMMENDATIONS")
            print("-" * 40)
            for rec in recommendations:
                print(f"  • {rec}")

    def _calculate_ecosystem_health(self, ecosystem_data: Dict[str, Any]) -> float:
        """Calculate overall ecosystem health score (0.0 to 1.0)"""
        if not ecosystem_data:
            return 0.0

        health_factors = []

        for machine_data in ecosystem_data.values():
            # Population balance (not too empty, not overcrowded)
            pop_ratio = machine_data['population'] / \
                machine_data.get('max_population', 50)
            pop_health = 1.0 - abs(0.6 - pop_ratio)  # Optimal around 60%

            # Food availability
            food_ratio = machine_data['food'] / \
                machine_data.get('max_food', 100)
            food_health = min(food_ratio * 2, 1.0)  # Good if > 50%

            # Temperature comfort (18-22°C is ideal)
            temp = machine_data['temperature']
            temp_health = 1.0 - abs(20 - temp) / \
                20 if abs(20 - temp) <= 20 else 0

            machine_health = (pop_health + food_health + temp_health) / 3
            health_factors.append(machine_health)

        return sum(health_factors) / len(health_factors)

    def _generate_ecosystem_recommendations(self, ecosystem_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations for ecosystem management"""
        recommendations = []

        if not ecosystem_data:
            return ["Start the daemon on multiple machines to create an ecosystem"]

        # Check for imbalances
        populations = [data['population'] for data in ecosystem_data.values()]
        foods = [data['food'] for data in ecosystem_data.values()]

        if max(populations) - min(populations) > 10:
            recommendations.append(
                "Population imbalance detected - consider manual migration")

        if min(foods) < 20:
            recommendations.append("Some machines are running low on food")

        if len(ecosystem_data) == 1:
            recommendations.append(
                "Connect more machines to enable creature migration")

        # Check for dying ecosystems
        total_pop = sum(populations)
        if total_pop < 5:
            recommendations.append(
                "Low population - consider adding more creatures")

        return recommendations

    def _format_last_seen(self, timestamp: float) -> str:
        """Format last seen timestamp"""
        if timestamp == 0:
            return "Never"

        import time
        seconds_ago = time.time() - timestamp

        if seconds_ago < 60:
            return f"{int(seconds_ago)}s ago"
        elif seconds_ago < 3600:
            return f"{int(seconds_ago/60)}m ago"
        else:
            return f"{int(seconds_ago/3600)}h ago"

    def ecosystem_map(self):
        """Show a visual map of the ecosystem network"""
        if not self.daemon_client.is_daemon_running():
            print("Error: Daemon is not running. Start with: python daemon.py")
            return

        network_response = self.daemon_client.send_command("network_overview")
        if not network_response or "error" in network_response:
            print(f"Error getting network data: {
                  network_response.get('error', 'Unknown error')}")
            return

        ecosystem_data = network_response['ecosystem_data']

        print("🗺️  ECOSYSTEM NETWORK MAP")
        print("=" * 60)

        # Create a simple visual representation
        for i, (machine_id, data) in enumerate(ecosystem_data.items()):
            is_local = data.get('is_local', False)

            # Visual indicators
            pop_indicator = "🟢" if data['population'] > 0 else "⚫"
            food_indicator = "🍎" if data['food'] > 50 else "🥜" if data['food'] > 20 else "🪨"
            local_indicator = "⭐" if is_local else "🖥️"

            print(f"{local_indicator} {machine_id[:12]:<12} {pop_indicator} Pop:{
                  data['population']:2d} {food_indicator} Food:{data['food']:3d}")

            # Connection lines (simplified)
            if i < len(ecosystem_data) - 1:
                print("   ┃")

        print("\nLegend:")
        print("⭐ = Your machine   🖥️ = Remote machine")
        print("🟢 = Has creatures  ⚫ = Empty")
        print("🍎 = Rich food     🥜 = Some food     🪨 = Low food")

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

#     def run(self, args: List[str]):
#         """Main CLI entry point"""
#         parser = argparse.ArgumentParser(
#             description='Thronglet Virtual Pet Ecosystem',
#             formatter_class=argparse.RawDescriptionHelpFormatter,
#             epilog="""
# Examples:
#   python main.py status                    # Show population status
#   python main.py list                      # List all creatures
#   python main.py add "Fluffy"             # Add creature named Fluffy
#   python main.py stats                     # Detailed statistics
#   python main.py feed_all                  # Emergency feeding
#   python main.py reproduce <creature_id>   # Force reproduction
#   python main.py network                   # Network status
#             """
#         )
#
#         subparsers = parser.add_subparsers(
#             dest='command', help='Available commands')
#
#         # Status command
#         subparsers.add_parser('status', help='Show local population status')
#
#         # List command
#         subparsers.add_parser('list', help='List all creatures with details')
#
#         # Network command
#         subparsers.add_parser(
#             'network', help='Show network connectivity status')
#
#         # Add creature command
#         add_parser = subparsers.add_parser(
#             'add', help='Add new creature to simulation')
#         add_parser.add_argument(
#             'name', nargs='?', help='Creature name (optional)')
#
#         # Detailed stats command
#         subparsers.add_parser(
#             'stats', help='Show comprehensive simulation statistics')
#
#         # Feed all command
#         subparsers.add_parser(
#             'feed_all', help='Emergency feeding for all hungry creatures')
#
#         # Force reproduction command
#         reproduce_parser = subparsers.add_parser(
#             'reproduce', help='Force a creature to reproduce')
#         reproduce_parser.add_argument('creature_id', nargs='?',
#                                       help='Creature ID (will prompt if not provided)')
#
#         # Parse arguments
#         parsed_args = parser.parse_args(args)
#
#         # Execute commands
#         if parsed_args.command == 'status':
#             self.status()
#         elif parsed_args.command == 'list':
#             self.list_creatures()
#         elif parsed_args.command == 'network':
#             self.network_status()
#         elif parsed_args.command == 'add':
#             self.add_creature(parsed_args.name)
#         elif parsed_args.command == 'stats':
#             self.detailed_stats()
#         elif parsed_args.command == 'feed_all':
#             self.feed_all()
#         elif parsed_args.command == 'reproduce':
#             self.force_reproduce(parsed_args.creature_id)
#         else:
#             parser.print_help()

    def migration_status(self):
        """Show migration statistics"""
        if not self.daemon_client.is_daemon_running():
            print("Error: Daemon is not running. Start with: python daemon.py")
            return

        response = self.daemon_client.send_command("stats")
        if not response or "error" in response:
            print(f"Error getting migration stats: {
                  response.get('error', 'Unknown error')}")
            return

        print("=== Migration Status ===")

        # Show network connectivity
        network_response = self.daemon_client.send_command("network")
        if network_response and "error" not in network_response:
            print(f"Connected to {network_response['connected_peers']} peers")
            for peer in network_response['peers']:
                print(f"  - {peer}")
        else:
            print("No network connectivity")

    def force_migration(self, creature_name: str = None):
        """Force migration of a specific creature or random eligible creature"""
        if not self.daemon_client.is_daemon_running():
            print("Error: Daemon is not running. Start with: python daemon.py")
            return

        response = self.daemon_client.send_command(
            "force_migration", creature_name=creature_name)
        if not response or "error" in response:
            print(f"Error forcing migration: {
                  response.get('error', 'Unknown error')}")
            return

        if response.get('success'):
            print(f"Migration initiated: {response.get('message', 'Success')}")
        else:
            print(f"Migration failed: {
                  response.get('message', 'Unknown reason')}")

# Update the run method to include new commands
    def run(self, args: List[str]):
        """Main CLI entry point with enhanced network commands"""
        parser = argparse.ArgumentParser(
            description='Thronglet Virtual Pet Ecosystem',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Network Overview Commands:
  python main.py overview                  # Complete ecosystem overview
  python main.py map                       # Visual network map
  python main.py network                   # Basic network status
  
Standard Commands:
  python main.py status                    # Local machine status
  python main.py list                      # List local creatures
  python main.py add "Name"               # Add creature
  python main.py migrate [creature]       # Force migration
            """
        )

        subparsers = parser.add_subparsers(dest='command', help='Available commands')

        # Existing commands
        subparsers.add_parser('status', help='Show local population status')
        subparsers.add_parser('list', help='List all creatures')
        subparsers.add_parser('network', help='Show basic network status')
        
        # Enhanced network commands
        subparsers.add_parser('overview', help='Complete ecosystem overview')
        subparsers.add_parser('map', help='Visual network map')

        add_parser = subparsers.add_parser('add', help='Add new creature')
        add_parser.add_argument('name', nargs='?', help='Creature name')

        migrate_parser = subparsers.add_parser('migrate', help='Force creature migration')
        migrate_parser.add_argument('creature_name', nargs='?', help='Creature name to migrate')

        parsed_args = parser.parse_args(args)

        # Execute commands
        if parsed_args.command == 'status':
            self.status()
        elif parsed_args.command == 'list':
            self.list_creatures()
        elif parsed_args.command == 'network':
            self.network_status()
        elif parsed_args.command == 'overview':
            self.network_overview()
        elif parsed_args.command == 'map':
            self.ecosystem_map()
        elif parsed_args.command == 'add':
            self.add_creature(parsed_args.name)
        elif parsed_args.command == 'migrate':
            self.force_migration(parsed_args.creature_name)
        else:
            parser.print_help()
