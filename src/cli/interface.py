#!/usr/bin/env python3
"""
Enhanced Thronglet CLI with rich formatting and better visual presentation
"""

import argparse
import sys
import time
import math
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Colors
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'


class ProgressBar:
    """Simple progress bar for terminal"""

    @staticmethod
    def create(value: int, max_value: int, width: int = 20,
               filled_char: str = '█', empty_char: str = '░') -> str:
        """Create a progress bar string"""
        if max_value == 0:
            percentage = 0
        else:
            percentage = min(100, max(0, (value / max_value) * 100))

        filled_length = int(width * percentage / 100)
        bar = filled_char * filled_length + \
            empty_char * (width - filled_length)
        return f"{bar} {percentage:5.1f}%"


class TableFormatter:
    """Simple table formatter for better data presentation"""

    @staticmethod
    def format_table(headers: List[str], rows: List[List[str]],
                     title: Optional[str] = None) -> str:
        """Format data as a table"""
        if not rows:
            return "No data to display"

        # Calculate column widths
        col_widths = [len(header) for header in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

        # Create separator
        separator = '+' + '+'.join('-' * (width + 2)
                                   for width in col_widths) + '+'

        # Build table
        result = []
        if title:
            result.append(f"\n{Colors.BOLD}{title}{Colors.RESET}")

        result.append(separator)

        # Headers
        header_row = '|'
        for i, header in enumerate(headers):
            header_row += f" {Colors.BOLD}{
                header:<{col_widths[i]}}{Colors.RESET} |"
        result.append(header_row)
        result.append(separator)

        # Data rows
        for row in rows:
            data_row = '|'
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    data_row += f" {str(cell):<{col_widths[i]}} |"
            result.append(data_row)

        result.append(separator)
        return '\n'.join(result)


class ThrongletCLI:
    """Enhanced CLI with rich formatting and better visual presentation"""

    def __init__(self):
        # Import the original daemon client
        from src.services.daemon_client import DaemonClient
        self.daemon_client = DaemonClient()

    def _print_header(self, title: str, subtitle: str = None):
        """Print a formatted header"""
        print(f"\n{Colors.CYAN}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{
              title.center(80)}{Colors.RESET}")
        if subtitle:
            print(f"{Colors.DIM}{subtitle.center(80)}{Colors.RESET}")
        print(f"{Colors.CYAN}{'=' * 80}{Colors.RESET}")

    def _print_section(self, title: str):
        """Print a section header"""
        print(f"\n{Colors.YELLOW}▶ {Colors.BOLD}{title}{Colors.RESET}")
        print(f"{Colors.YELLOW}{'─' * (len(title) + 2)}{Colors.RESET}")

    def _format_health_bar(self, value: int, max_value: int,
                           color_thresholds: List[tuple] = None) -> str:
        """Create a colored health/status bar"""
        if color_thresholds is None:
            color_thresholds = [(80, Colors.GREEN),
                                (50, Colors.YELLOW), (0, Colors.RED)]

        percentage = (value / max_value * 100) if max_value > 0 else 0

        # Choose color based on percentage
        color = Colors.RED
        for threshold, threshold_color in color_thresholds:
            if percentage >= threshold:
                color = threshold_color
                break

        bar = ProgressBar.create(value, max_value, width=15)
        return f"{color}{bar}{Colors.RESET} ({value}/{max_value})"

    def _get_creature_status_icon(self, creature: Dict[str, Any]) -> str:
        """Get an icon representing the creature's overall status"""
        happiness = creature.get('happiness', 50)
        energy = creature.get('energy', 50)
        state = creature.get('state', 'idle')

        if state == 'dying':
            return f"{Colors.RED}💀{Colors.RESET}"
        elif state == 'reproducing':
            return f"{Colors.MAGENTA}💕{Colors.RESET}"
        elif state == 'eating':
            return f"{Colors.GREEN}🍽️{Colors.RESET}"
        elif happiness > 80 and energy > 70:
            return f"{Colors.BRIGHT_GREEN}😄{Colors.RESET}"
        elif happiness > 60:
            return f"{Colors.GREEN}😊{Colors.RESET}"
        elif happiness < 30:
            return f"{Colors.RED}😢{Colors.RESET}"
        else:
            return f"{Colors.YELLOW}😐{Colors.RESET}"

    def status(self):
        """Enhanced status display with visual elements"""
        if not self.daemon_client.is_daemon_running():
            print(f"{Colors.RED}❌ Error: Daemon is not running.{Colors.RESET}")
            print(f"{Colors.CYAN}💡 Start with: python daemon.py{Colors.RESET}")
            return

        response = self.daemon_client.send_command("status")
        if not response or "error" in response:
            print(f"{Colors.RED}❌ Error getting status: {
                  response.get('error', 'Unknown error')}{Colors.RESET}")
            return

        self._print_header("🏠 LOCAL MACHINE STATUS",
                           f"Machine: {response['machine_id']}")

        # Resource status
        self._print_section("📊 Resources")
        pop_bar = self._format_health_bar(
            response['population'],
            response['max_population'],
            # Population is good when moderate
            [(80, Colors.YELLOW), (60, Colors.GREEN), (0, Colors.CYAN)]
        )
        food_bar = self._format_health_bar(
            response['food'], response['max_food'])

        print(f"  Population: {pop_bar}")
        print(f"  Food:       {food_bar}")
        print(f"  Temperature: {Colors.CYAN}{
              response['temperature']}°C{Colors.RESET}")

        # Creature states with icons
        self._print_section("🎭 Creature Activity")
        state_icons = {
            'idle': '😴', 'hungry': '🍽️', 'eating': '😋',
            'reproducing': '💕', 'dying': '💀'
        }

        total_creatures = sum(response['state_counts'].values())
        if total_creatures == 0:
            print(f"  {Colors.DIM}No creatures found{Colors.RESET}")
        else:
            for state, count in response['state_counts'].items():
                icon = state_icons.get(state, '❓')
                percentage = (count / total_creatures *
                              100) if total_creatures > 0 else 0
                bar = ProgressBar.create(count, total_creatures, width=10)
                print(f"  {icon} {state.capitalize():<12}: {
                      Colors.CYAN}{count:3d}{Colors.RESET} {bar}")

    def list_creatures(self):
        """Enhanced creature listing with better formatting"""
        if not self.daemon_client.is_daemon_running():
            print(f"{Colors.RED}❌ Error: Daemon is not running.{Colors.RESET}")
            return

        response = self.daemon_client.send_command("list")
        if not response or "error" in response:
            print(f"{Colors.RED}❌ Error listing creatures: {
                  response.get('error', 'Unknown error')}{Colors.RESET}")
            return

        creatures = response['creatures']
        self._print_header(f"🐾 CREATURE POPULATION ({response['count']})")

        if not creatures:
            print(f"\n{Colors.YELLOW}📭 No creatures found{Colors.RESET}")
            print(f"{Colors.CYAN}💡 Add some with: python main.py add [name]{
                  Colors.RESET}")
            return

        # Prepare table data
        headers = ["Status", "Name", "ID", "Age",
                   "Energy", "Hunger", "Happiness", "State"]
        rows = []

        for creature in sorted(creatures, key=lambda c: c['happiness'], reverse=True):
            status_icon = self._get_creature_status_icon(creature)
            age_str = f"{creature['age']}/{creature['max_age']}"

            # Color code the values
            energy_color = (Colors.GREEN if creature['energy'] > 70 else
                            Colors.YELLOW if creature['energy'] > 30 else Colors.RED)
            hunger_color = (Colors.RED if creature['hunger'] > 70 else
                            Colors.YELLOW if creature['hunger'] > 30 else Colors.GREEN)
            happiness_color = (Colors.GREEN if creature['happiness'] > 70 else
                               Colors.YELLOW if creature['happiness'] > 40 else Colors.RED)

            rows.append([
                status_icon,
                f"{Colors.BOLD}{creature['name']}{Colors.RESET}",
                f"{Colors.DIM}{creature['id'][:8]}{Colors.RESET}",
                age_str,
                f"{energy_color}{creature['energy']}{Colors.RESET}",
                f"{hunger_color}{creature['hunger']}{Colors.RESET}",
                f"{happiness_color}{creature['happiness']}{Colors.RESET}",
                creature['state']
            ])

        print(TableFormatter.format_table(headers, rows))

        # Summary statistics
        avg_happiness = sum(c['happiness'] for c in creatures) / len(creatures)
        avg_energy = sum(c['energy'] for c in creatures) / len(creatures)

        print(f"\n{Colors.CYAN}📈 Population Summary:{Colors.RESET}")
        print(f"  Average Happiness: {Colors.GREEN if avg_happiness > 60 else Colors.YELLOW if avg_happiness > 40 else Colors.RED}{
              avg_happiness:.1f}{Colors.RESET}")
        print(f"  Average Energy: {Colors.GREEN if avg_energy > 60 else Colors.YELLOW if avg_energy > 40 else Colors.RED}{
              avg_energy:.1f}{Colors.RESET}")

    def network_overview(self):
        """Enhanced network overview with rich visuals"""
        if not self.daemon_client.is_daemon_running():
            print(f"{Colors.RED}❌ Error: Daemon is not running.{Colors.RESET}")
            return

        response = self.daemon_client.send_command("network_overview")
        if not response or "error" in response:
            print(f"{Colors.RED}❌ Error getting network overview: {
                  response.get('error', 'Unknown error')}{Colors.RESET}")
            return

        ecosystem_data = response['ecosystem_data']
        self._print_header("🌐 THRONGLET ECOSYSTEM NETWORK",
                           "Distributed Virtual Pet Universe")

        # Ecosystem summary with visual elements
        total_machines = len(ecosystem_data)
        total_population = sum(machine['population']
                               for machine in ecosystem_data.values())
        total_food = sum(machine['food']
                         for machine in ecosystem_data.values())
        avg_temperature = sum(machine['temperature'] for machine in ecosystem_data.values(
        )) / total_machines if total_machines > 0 else 0

        self._print_section("🌍 Ecosystem Overview")

        # Create a visual ecosystem health indicator
        health_score = self._calculate_ecosystem_health(ecosystem_data)
        health_bar = ProgressBar.create(int(health_score * 100), 100, width=20)
        health_color = Colors.GREEN if health_score > 0.7 else Colors.YELLOW if health_score > 0.4 else Colors.RED

        print(f"  🖥️  Connected Machines: {Colors.BOLD}{
              Colors.CYAN}{total_machines}{Colors.RESET}")
        print(f"  👥 Total Population: {Colors.BOLD}{
              Colors.GREEN}{total_population}{Colors.RESET}")
        print(f"  🍎 Available Food: {Colors.BOLD}{
              Colors.YELLOW}{total_food}{Colors.RESET}")
        print(f"  🌡️  Average Temperature: {Colors.CYAN}{
              avg_temperature:.1f}°C{Colors.RESET}")
        print(f"  ❤️  Ecosystem Health: {
              health_color}{health_bar}{Colors.RESET}")

        # Machine details in a nice table
        self._print_section("🖥️ Machine Status")

        headers = ["Machine", "Population",
                   "Food", "Temp", "Status", "Last Seen"]
        rows = []

        for machine_id, data in sorted(ecosystem_data.items(), key=lambda x: x[1]['population'], reverse=True):
            is_local = data.get('is_local', False)

            # Status indicators
            pop_ratio = data['population'] / data.get('max_population', 50)
            food_ratio = data['food'] / data.get('max_food', 100)

            status_icons = []
            if is_local:
                status_icons.append(f"{Colors.BRIGHT_CYAN}⭐{Colors.RESET}")
            if pop_ratio > 0.8:
                status_icons.append(
                    f"{Colors.RED}🚨{Colors.RESET}")  # Overcrowded
            elif pop_ratio > 0.6:
                status_icons.append(
                    f"{Colors.GREEN}✅{Colors.RESET}")  # Healthy
            elif pop_ratio > 0:
                status_icons.append(f"{Colors.CYAN}🏠{Colors.RESET}")  # Active
            else:
                status_icons.append(f"{Colors.DIM}💤{Colors.RESET}")  # Empty

            if food_ratio < 0.2:
                status_icons.append(f"{Colors.RED}🪨{Colors.RESET}")  # Low food
            elif food_ratio > 0.7:
                status_icons.append(
                    f"{Colors.GREEN}🍎{Colors.RESET}")  # Rich food

            machine_name = f"{Colors.BOLD}{machine_id[:12]}{Colors.RESET}"
            if is_local:
                machine_name += f" {Colors.BRIGHT_CYAN}(LOCAL){Colors.RESET}"

            pop_display = f"{data['population']
                             }/{data.get('max_population', 50)}"
            food_display = f"{data['food']}/{data.get('max_food', 100)}"
            temp_display = f"{data['temperature']}°C"
            status_display = ''.join(status_icons)
            last_seen = self._format_last_seen(data.get('last_seen', 0))

            rows.append([machine_name, pop_display, food_display,
                        temp_display, status_display, last_seen])

        print(TableFormatter.format_table(headers, rows))

        # Migration activity
        migration_data = response.get('migration_activity', {})
        if migration_data and migration_data.get('total_migrations', 0) > 0:
            self._print_section("🔄 Migration Activity")
            print(f"  Total Migrations: {Colors.CYAN}{
                  migration_data.get('total_migrations', 0)}{Colors.RESET}")

            recent_migrations = migration_data.get('recent_migrations', [])
            if recent_migrations:
                print(f"  Recent Activity:")
                for migration in recent_migrations[-3:]:  # Show last 3
                    print(f"    {Colors.GREEN}→{Colors.RESET} {migration['creature_name']}: "
                          f"{Colors.CYAN}{migration['from']}{Colors.RESET} → "
                          f"{Colors.CYAN}{migration['to']}{Colors.RESET}")

        # Recommendations
        recommendations = self._generate_ecosystem_recommendations(
            ecosystem_data)
        if recommendations:
            self._print_section("💡 Ecosystem Recommendations")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {Colors.YELLOW}{i}.{Colors.RESET} {rec}")

    def ecosystem_map(self):
        """Visual ASCII map of the ecosystem"""
        if not self.daemon_client.is_daemon_running():
            print(f"{Colors.RED}❌ Error: Daemon is not running.{Colors.RESET}")
            return

        response = self.daemon_client.send_command("network_overview")
        if not response or "error" in response:
            print(f"{Colors.RED}❌ Error getting network data: {
                  response.get('error', 'Unknown error')}{Colors.RESET}")
            return

        ecosystem_data = response['ecosystem_data']
        self._print_header("🗺️ ECOSYSTEM NETWORK MAP",
                           "Visual Network Topology")

        # Create ASCII art map
        machines = list(ecosystem_data.items())

        if len(machines) == 1:
            # Single machine
            machine_id, data = machines[0]
            icon = f"{Colors.BRIGHT_CYAN}⭐{Colors.RESET}" if data.get(
                'is_local') else f"{Colors.CYAN}🖥️{Colors.RESET}"
            pop_icon = self._get_population_icon(data['population'])
            food_icon = self._get_food_icon(data['food'])

            print(f"""
                    {icon}
                ╭─────────────────╮
                │ {machine_id[:15]:<15} │
                │ {pop_icon} Pop: {data['population']:2d}      │
                │ {food_icon} Food: {data['food']:3d}    │
                ╰─────────────────╯
            """)
        else:
            # Multiple machines - create network diagram
            print("\n")
            for i, (machine_id, data) in enumerate(machines):
                is_local = data.get('is_local', False)
                icon = f"{Colors.BRIGHT_CYAN}⭐{Colors.RESET}" if is_local else f"{
                    Colors.CYAN}🖥️{Colors.RESET}"
                pop_icon = self._get_population_icon(data['population'])
                food_icon = self._get_food_icon(data['food'])

                # Machine box
                print(f"    {icon} ╭─────────────────╮")
                print(f"      │ {Colors.BOLD}{
                      machine_id[:15]:<15}{Colors.RESET} │")
                print(f"      │ {pop_icon} Pop: {
                      data['population']:2d}      │")
                print(f"      │ {food_icon} Food: {data['food']:3d}    │")
                print(f"      ╰─────────────────╯")

                # Connection line (except for last machine)
                if i < len(machines) - 1:
                    print(f"                {Colors.DIM}║{Colors.RESET}")
                    print(f"                {Colors.DIM}║{Colors.RESET}")

        # Legend
        print(f"\n{Colors.YELLOW}Legend:{Colors.RESET}")
        print(f"  {Colors.BRIGHT_CYAN}⭐{Colors.RESET} Your machine   {
              Colors.CYAN}🖥️{Colors.RESET} Remote machine")
        print(f"  🟢 Has creatures  ⚫ Empty machine")
        print(f"  🍎 Rich food (>50)  🥜 Some food (20-50)  🪨 Low food (<20)")

    def _get_population_icon(self, population: int) -> str:
        """Get icon representing population level"""
        if population == 0:
            return "⚫"
        elif population < 5:
            return f"{Colors.CYAN}🔵{Colors.RESET}"
        elif population < 15:
            return f"{Colors.GREEN}🟢{Colors.RESET}"
        elif population < 30:
            return f"{Colors.YELLOW}🟡{Colors.RESET}"
        else:
            return f"{Colors.RED}🔴{Colors.RESET}"

    def _get_food_icon(self, food: int) -> str:
        """Get icon representing food level"""
        if food < 20:
            return f"{Colors.RED}🪨{Colors.RESET}"
        elif food < 50:
            return f"{Colors.YELLOW}🥜{Colors.RESET}"
        else:
            return f"{Colors.GREEN}🍎{Colors.RESET}"

    def _calculate_ecosystem_health(self, ecosystem_data: Dict[str, Any]) -> float:
        """Calculate overall ecosystem health score (0.0 to 1.0)"""
        if not ecosystem_data:
            return 0.0

        health_factors = []
        for machine_data in ecosystem_data.values():
            pop_ratio = machine_data['population'] / \
                machine_data.get('max_population', 50)
            pop_health = 1.0 - \
                abs(0.6 - pop_ratio) if pop_ratio <= 1.0 else 0.5

            food_ratio = machine_data['food'] / \
                machine_data.get('max_food', 100)
            food_health = min(food_ratio * 2, 1.0)

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

        total_pop = sum(populations)
        if total_pop < 5:
            recommendations.append(
                "Low population - consider adding more creatures")

        return recommendations

    def _format_last_seen(self, timestamp: float) -> str:
        """Format last seen timestamp with colors"""
        if timestamp == 0:
            return f"{Colors.DIM}Never{Colors.RESET}"

        seconds_ago = time.time() - timestamp

        if seconds_ago < 30:
            return f"{Colors.GREEN}Just now{Colors.RESET}"
        elif seconds_ago < 60:
            return f"{Colors.GREEN}{int(seconds_ago)}s ago{Colors.RESET}"
        elif seconds_ago < 3600:
            return f"{Colors.YELLOW}{int(seconds_ago/60)}m ago{Colors.RESET}"
        else:
            return f"{Colors.RED}{int(seconds_ago/3600)}h ago{Colors.RESET}"

    def add_creature(self, name: str = None):
        """Enhanced creature addition with visual feedback"""
        if not self.daemon_client.is_daemon_running():
            print(f"{Colors.RED}❌ Error: Daemon is not running.{Colors.RESET}")
            return

        response = self.daemon_client.send_command("add", name=name)
        if not response or "error" in response:
            print(f"{Colors.RED}❌ Error adding creature: {
                  response.get('error', 'Unknown error')}{Colors.RESET}")
            return

        creature = response['creature']
        print(f"{Colors.GREEN}✅ Created creature:{Colors.RESET} {Colors.BOLD}{creature['name']}{Colors.RESET} "
              f"{Colors.DIM}({creature['id'][:8]}){Colors.RESET}")

        # Show a cute birth animation
        print(f"{Colors.MAGENTA}    🥚 → 🐣 → 🐥 Born!{Colors.RESET}")

    def network_status(self):
        """Show basic network connectivity"""
        if not self.daemon_client.is_daemon_running():
            print(f"{Colors.RED}❌ Error: Daemon is not running.{Colors.RESET}")
            return

        response = self.daemon_client.send_command("network")
        if not response or "error" in response:
            print(f"{Colors.RED}❌ Error getting network status: {
                  response.get('error', 'Unknown error')}{Colors.RESET}")
            return

        self._print_header("🌐 NETWORK STATUS")

        print(f"  Machine ID: {Colors.BOLD}{Colors.CYAN}{
              response['machine_id']}{Colors.RESET}")
        print(f"  Connected Peers: {Colors.GREEN}{
              response['connected_peers']}{Colors.RESET}")

        if response['peers']:
            print(f"\n  {Colors.YELLOW}Connected Machines:{Colors.RESET}")
            for peer in response['peers']:
                print(f"    • {peer}")
        else:
            print(f"\n  {Colors.DIM}No connected peers found{Colors.RESET}")
            print(f"  {Colors.CYAN}💡 Start daemon on other machines to enable networking{
                  Colors.RESET}")

    def detailed_stats(self):
        """Show comprehensive simulation statistics with enhanced formatting"""
        if not self.daemon_client.is_daemon_running():
            print(f"{Colors.RED}❌ Error: Daemon is not running.{Colors.RESET}")
            return

        response = self.daemon_client.send_command("stats")
        if not response or "error" in response:
            print(f"{Colors.RED}❌ Error getting stats: {
                  response.get('error', 'Unknown error')}{Colors.RESET}")
            return

        self._print_header("📊 DETAILED ECOSYSTEM STATISTICS",
                           "Comprehensive Analysis")

        # Runtime stats
        runtime = response['runtime']
        self._print_section("⏱️ Runtime Metrics")
        print(f"  Simulation Ticks: {Colors.CYAN}{
              runtime['tick_count']:,}{Colors.RESET}")
        print(f"  Births This Session: {Colors.GREEN}{
              runtime['births_this_session']}{Colors.RESET}")
        print(f"  Deaths This Session: {Colors.RED}{
              runtime['deaths_this_session']}{Colors.RESET}")

        net_growth = runtime['births_this_session'] - \
            runtime['deaths_this_session']
        growth_color = Colors.GREEN if net_growth > 0 else Colors.RED if net_growth < 0 else Colors.YELLOW
        print(f"  Net Population Growth: {growth_color}{
              net_growth:+d}{Colors.RESET}")

        # World stats
        world = response['world']
        self._print_section("🌍 World Environment")
        food_bar = self._format_health_bar(world['food'], world['max_food'])
        pop_bar = self._format_health_bar(
            world['population_count'], world['max_population'])

        print(f"  Food Supply: {food_bar}")
        print(f"  Population: {pop_bar}")
        print(f"  Temperature: {Colors.CYAN}{
              world['temperature']}°C{Colors.RESET}")

        # Creature demographics
        creatures = response['creatures']
        self._print_section("👥 Population Demographics")
        print(f"  Total Population: {Colors.BOLD}{Colors.GREEN}{
              creatures['total_population']}{Colors.RESET}")
        print(f"  Average Age: {Colors.CYAN}{
              creatures['average_age']}{Colors.RESET}")
        print(f"  Average Energy: {Colors.YELLOW}{
              creatures['average_energy']}{Colors.RESET}")
        print(f"  Average Happiness: {Colors.MAGENTA}{
              creatures['average_happiness']}{Colors.RESET}")
        print(f"  Average Hunger: {Colors.RED}{
              creatures['average_hunger']}{Colors.RESET}")

        # State distribution with visual bars
        self._print_section("🎭 Creature Activity States")
        state_icons = {'idle': '😴', 'hungry': '🍽️',
                       'eating': '😋', 'reproducing': '💕', 'dying': '💀'}
        total_pop = creatures['total_population']

        for state, count in creatures['state_distribution'].items():
            icon = state_icons.get(state, '❓')
            if total_pop > 0:
                percentage = count / total_pop * 100
                bar = ProgressBar.create(count, total_pop, width=15)
                print(f"  {icon} {state.capitalize():<12}: {
                      Colors.CYAN}{count:3d}{Colors.RESET} {bar}")

        # Age and happiness distributions
        self._print_section("📈 Demographics Breakdown")
        print(f"  {Colors.BOLD}Age Groups:{Colors.RESET}")
        age_emojis = {'young': '👶', 'adult': '🧑', 'old': '👴'}
        for age_group, count in creatures['age_distribution'].items():
            emoji = age_emojis.get(age_group, '❓')
            print(f"    {emoji} {age_group.capitalize()}: {
                  Colors.CYAN}{count}{Colors.RESET}")

        print(f"  {Colors.BOLD}Happiness Levels:{Colors.RESET}")
        happiness_emojis = {'miserable': '😢', 'sad': '😟',
                            'content': '😐', 'happy': '😊', 'ecstatic': '🤩'}
        for mood, count in creatures.get('happiness_distribution', {}).items():
            emoji = happiness_emojis.get(mood, '😐')
            print(f"    {emoji} {mood.capitalize()}: {
                  Colors.CYAN}{count}{Colors.RESET}")

        # Generation tracking
        if 'generations' in creatures and creatures['generations']:
            print(f"  {Colors.BOLD}Genetic Generations:{Colors.RESET}")
            for gen, count in creatures['generations'].items():
                gen_display = gen.replace('_', ' ').title()
                print(f"    🧬 {gen_display}: {
                      Colors.CYAN}{count}{Colors.RESET}")

        # Behavior transitions
        if response.get('behavior_transitions'):
            self._print_section("🔄 Behavioral Activity")
            # Top 5
            for transition, count in list(response['behavior_transitions'].items())[:5]:
                print(f"  {transition}: {Colors.YELLOW}{count}{Colors.RESET}")

    def feed_all(self):
        """Emergency feeding for all creatures with enhanced feedback"""
        if not self.daemon_client.is_daemon_running():
            print(f"{Colors.RED}❌ Error: Daemon is not running.{Colors.RESET}")
            return

        print(f"{Colors.YELLOW}🍎 Initiating emergency feeding...{Colors.RESET}")

        response = self.daemon_client.send_command("feed_all")
        if not response or "error" in response:
            print(f"{Colors.RED}❌ Error feeding creatures: {
                  response.get('error', 'Unknown error')}{Colors.RESET}")
            return

        fed_count = response.get('fed_count', 0)
        if fed_count > 0:
            print(f"{Colors.GREEN}✅ Emergency feeding complete!{Colors.RESET}")
            print(f"   Fed {Colors.BOLD}{fed_count}{
                  Colors.RESET} hungry creatures")
            print(f"   {Colors.CYAN}💡 Creatures should be happier now!{
                  Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}ℹ️ No creatures needed feeding{Colors.RESET}")

    def force_reproduce(self, creature_id: str = None):
        """Force a creature to reproduce with enhanced selection"""
        if not self.daemon_client.is_daemon_running():
            print(f"{Colors.RED}❌ Error: Daemon is not running.{Colors.RESET}")
            return

        if not creature_id:
            # Get list of creatures to choose from
            list_response = self.daemon_client.send_command("list")
            if not list_response or "error" in list_response:
                print(f"{Colors.RED}❌ Error: Could not get creature list{
                      Colors.RESET}")
                return

            creatures = list_response['creatures']
            if not creatures:
                print(f"{Colors.YELLOW}📭 No creatures available for reproduction{
                      Colors.RESET}")
                return

            print(f"{Colors.CYAN}🔍 Available creatures:{Colors.RESET}")
            for i, creature in enumerate(creatures):
                status_icon = self._get_creature_status_icon(creature)
                energy_color = Colors.GREEN if creature[
                    'energy'] > 50 else Colors.YELLOW if creature['energy'] > 30 else Colors.RED
                print(f"  {i+1}. {status_icon} {Colors.BOLD}{creature['name']}{Colors.RESET} "
                      f"(Age: {creature['age']}, Energy: {energy_color}{creature['energy']}{Colors.RESET})")

            try:
                choice = int(
                    input(f"\n{Colors.CYAN}Select creature number: {Colors.RESET}")) - 1
                if 0 <= choice < len(creatures):
                    creature_id = creatures[choice]['id']
                else:
                    print(f"{Colors.RED}❌ Invalid selection{Colors.RESET}")
                    return
            except (ValueError, KeyboardInterrupt):
                print(f"\n{Colors.YELLOW}Operation cancelled{Colors.RESET}")
                return

        response = self.daemon_client.send_command(
            "force_reproduce", creature_id=creature_id)
        if not response or "error" in response:
            print(f"{Colors.RED}❌ Error forcing reproduction: {
                  response.get('error', 'Unknown error')}{Colors.RESET}")
            return

        if response['success']:
            print(f"{Colors.GREEN}✅ {response['message']}{Colors.RESET}")
            print(f"{Colors.MAGENTA}💕 Romance is in the air!{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}⚠️ {response['message']}{Colors.RESET}")

    def force_migration(self, creature_name: str = None):
        """Force migration of a specific creature with enhanced feedback"""
        if not self.daemon_client.is_daemon_running():
            print(f"{Colors.RED}❌ Error: Daemon is not running.{Colors.RESET}")
            return

        print(f"{Colors.CYAN}🔄 Initiating creature migration...{Colors.RESET}")

        response = self.daemon_client.send_command(
            "force_migration", creature_name=creature_name)
        if not response or "error" in response:
            print(f"{Colors.RED}❌ Migration failed: {
                  response.get('error', 'Unknown error')}{Colors.RESET}")
            return

        if response.get('success'):
            print(f"{Colors.GREEN}✅ Migration successful!{Colors.RESET}")
            print(
                f"   {response.get('message', 'Creature migrated successfully')}")
            print(f"{Colors.CYAN}🌐 Check other machines to see the migrated creature{
                  Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}⚠️ Migration failed: {
                  response.get('message', 'Unknown reason')}{Colors.RESET}")

    def run(self, args: List[str]):
        """Complete main CLI entry point with all commands"""
        parser = argparse.ArgumentParser(
            description='🐾 Thronglet Virtual Pet Ecosystem',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=f"""
{Colors.CYAN}🌐 Network Commands:{Colors.RESET}
  python main.py overview                  # Complete ecosystem overview
  python main.py map                       # Visual network map
  python main.py network                   # Basic network status

{Colors.GREEN}🐾 Creature Management:{Colors.RESET}
  python main.py status                    # Local machine status
  python main.py list                      # List local creatures
  python main.py add "Name"               # Add new creature

{Colors.YELLOW}⚡ Actions:{Colors.RESET}
  python main.py migrate [creature]       # Force migration
  python main.py reproduce [id]           # Force reproduction
  python main.py feed_all                 # Emergency feeding
  python main.py stats                    # Detailed statistics
            """
        )

        subparsers = parser.add_subparsers(
            dest='command', help='Available commands')

        # Basic commands
        subparsers.add_parser('status', help='🏠 Show local machine status')
        subparsers.add_parser('list', help='📋 List all creatures with details')
        subparsers.add_parser('network', help='🌐 Show network connectivity')

        # Enhanced network commands
        subparsers.add_parser('overview', help='🌍 Complete ecosystem overview')
        subparsers.add_parser('map', help='🗺️ Visual network map')

        # Statistics and analysis
        subparsers.add_parser('stats', help='📊 Detailed statistics')

        # Creature management
        add_parser = subparsers.add_parser('add', help='➕ Add new creature')
        add_parser.add_argument(
            'name', nargs='?', help='Creature name (optional)')

        # Actions
        subparsers.add_parser(
            'feed_all', help='🍎 Emergency feeding for all creatures')

        reproduce_parser = subparsers.add_parser(
            'reproduce', help='💕 Force creature reproduction')
        reproduce_parser.add_argument(
            'creature_id', nargs='?', help='Creature ID (will prompt if not provided)')

        migrate_parser = subparsers.add_parser(
            'migrate', help='🔄 Force creature migration')
        migrate_parser.add_argument(
            'creature_name', nargs='?', help='Creature name to migrate')

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
        elif parsed_args.command == 'stats':
            self.detailed_stats()
        elif parsed_args.command == 'add':
            self.add_creature(parsed_args.name)
        elif parsed_args.command == 'feed_all':
            self.feed_all()
        elif parsed_args.command == 'reproduce':
            self.force_reproduce(parsed_args.creature_id)
        elif parsed_args.command == 'migrate':
            self.force_migration(parsed_args.creature_name)
        else:
            parser.print_help()


# Example usage
if __name__ == "__main__":
    cli = ThrongletCLI()
    cli.run(sys.argv[1:])
