#!/usr/bin/env python3
"""
Real-time Thronglet Ecosystem Dashboard
A continuously updating terminal dashboard for monitoring the ecosystem
"""

import time
import os
import sys
import threading
from typing import Dict, Any, List
from datetime import datetime


class TerminalDashboard:
    """Real-time terminal dashboard for monitoring Thronglet ecosystem"""

    def __init__(self):
        from src.services.daemon_client import DaemonClient
        self.daemon_client = DaemonClient()
        self.running = False
        self.refresh_rate = 2.0  # seconds
        self.last_update = None

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def get_terminal_size(self):
        """Get terminal dimensions"""
        try:
            size = os.get_terminal_size()
            return size.columns, size.lines
        except:
            return 80, 24  # Default size

    def draw_box(self, width: int, height: int, title: str = "") -> List[str]:
        """Draw a box with optional title"""
        lines = []

        # Top border
        if title:
            title_line = f"┌─ {title} " + "─" * (width - len(title) - 4) + "┐"
            lines.append(title_line[:width])
        else:
            lines.append("┌" + "─" * (width - 2) + "┐")

        # Side borders
        for _ in range(height - 2):
            lines.append("│" + " " * (width - 2) + "│")

        # Bottom border
        lines.append("└" + "─" * (width - 2) + "┘")

        return lines

    def create_sparkline(self, values: List[float], width: int = 20) -> str:
        """Create a simple sparkline chart"""
        if not values or len(values) < 2:
            return "─" * width

        min_val, max_val = min(values), max(values)
        if min_val == max_val:
            return "─" * width

        # Unicode block characters for sparkline
        chars = [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

        sparkline = ""
        for i in range(width):
            if i < len(values):
                normalized = (values[i] - min_val) / (max_val - min_val)
                char_index = int(normalized * (len(chars) - 1))
                sparkline += chars[char_index]
            else:
                sparkline += " "

        return sparkline[:width]

    def format_uptime(self, start_time: float) -> str:
        """Format uptime duration"""
        uptime = time.time() - start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def render_ecosystem_summary(self, ecosystem_data: Dict[str, Any], width: int) -> List[str]:
        """Render ecosystem summary panel"""
        lines = []

        total_machines = len(ecosystem_data)
        total_population = sum(machine['population']
                               for machine in ecosystem_data.values())
        total_food = sum(machine['food']
                         for machine in ecosystem_data.values())
        avg_temp = sum(machine['temperature']
                       for machine in ecosystem_data.values()) / max(total_machines, 1)

        lines.append(f"🌐 Machines: {total_machines:2d}  👥 Population: {
                     total_population:3d}")
        lines.append(f"🍎 Food: {total_food:4d}      🌡️  Temperature: {
                     avg_temp:4.1f}°C")

        # Health indicator
        health_score = self._calculate_health(ecosystem_data)
        health_bar = "█" * int(health_score * 10) + "░" * \
            (10 - int(health_score * 10))
        health_color = "🟢" if health_score > 0.7 else "🟡" if health_score > 0.4 else "🔴"
        lines.append(f"❤️  Health: {health_color} {
                     health_bar} {health_score*100:4.1f}%")

        return lines

    def render_machine_grid(self, ecosystem_data: Dict[str, Any], width: int, height: int) -> List[str]:
        """Render machines in a grid layout"""
        lines = []
        machines = list(ecosystem_data.items())

        # Calculate grid dimensions
        cols = min(3, len(machines))  # Max 3 columns
        rows = (len(machines) + cols - 1) // cols

        machine_width = (width - 4) // cols - 1

        for row in range(rows):
            # Machine names
            name_line = ""
            pop_line = ""
            food_line = ""
            state_line = ""

            for col in range(cols):
                idx = row * cols + col
                if idx < len(machines):
                    machine_id, data = machines[idx]
                    is_local = data.get('is_local', False)

                    # Machine info
                    icon = "⭐" if is_local else "🖥️"
                    name = f"{icon} {machine_id[:machine_width-3]}"
                    pop_info = f"👥{data['population']:2d}/{data.get('max_population', 50):2d}"
                    food_info = f"🍎{data['food']:3d}/{data.get('max_food', 100):3d}"

                    # State distribution
                    states = data.get('state_counts', {})
                    state_icons = ""
                    # Show top 3 states
                    for state, count in list(states.items())[:3]:
                        state_emoji = {'idle': '😴', 'hungry': '🍽️', 'eating': '😋','reproducing': '💕', 'dying': '💀'}.get(state, '❓')
                        if count > 0:
                            state_icons += f"{state_emoji}{count}"

                    name_line += f"{name:<{machine_width}} "
                    pop_line += f"{pop_info:<{machine_width}} "
                    food_line += f"{food_info:<{machine_width}} "
                    state_line += f"{state_icons:<{machine_width}} "
                else:
                    name_line += " " * (machine_width + 1)
                    pop_line += " " * (machine_width + 1)
                    food_line += " " * (machine_width + 1)
                    state_line += " " * (machine_width + 1)

            lines.extend([name_line.rstrip(), pop_line.rstrip(),
                         food_line.rstrip(), state_line.rstrip(), ""])

        return lines

    def render_activity_feed(self, width: int, height: int) -> List[str]:
        """Render recent activity feed"""
        lines = []

        # This would ideally read from activity logs
        # For now, show placeholder activity
        activities = [
            "🐣 Creature born: Fluffy-Jr-123",
            "🔄 Migration: Buddy → Machine-B",
            "🍽️ Feeding event on Machine-A",
            "💕 Reproduction: Happy + Lucky",
            "💀 Death: Elderly (age 950)",
            "🌡️ Temperature change: 21°C",
            "🎯 Population milestone: 25 creatures"
        ]

        current_time = datetime.now()

        for i, activity in enumerate(activities[:height-2]):
            timestamp = current_time.strftime("%H:%M:%S")
            line = f"{timestamp} {activity}"
            lines.append(line[:width-2])

        return lines

    def render_population_chart(self, width: int, height: int) -> List[str]:
        """Render population trend chart"""
        lines = []

        # Mock population data - in real implementation, this would come from logs
        population_history = [15, 18, 22, 25, 23, 28, 31, 29, 33, 35, 32, 30]

        chart_width = width - 10
        chart_height = height - 4

        if not population_history:
            lines.append("No population data available")
            return lines

        max_pop = max(population_history)
        min_pop = min(population_history)

        # Draw Y-axis labels and chart
        for y in range(chart_height):
            y_value = max_pop - (y * (max_pop - min_pop) / (chart_height - 1))
            y_label = f"{y_value:4.0f} │"

            # Draw data points
            chart_line = ""
            for x in range(chart_width):
                if x < len(population_history):
                    data_y = (
                        population_history[x] - min_pop) / (max_pop - min_pop) * (chart_height - 1)
                    if abs(data_y - (chart_height - 1 - y)) < 0.5:
                        chart_line += "●"
                    else:
                        chart_line += " "
                else:
                    chart_line += " "

            lines.append(y_label + chart_line)

        # X-axis
        x_axis = "     └" + "─" * chart_width
        lines.append(x_axis)

        # Sparkline summary
        sparkline = self.create_sparkline(population_history, chart_width)
        lines.append(f"Trend: {sparkline}")

        return lines

    def _calculate_health(self, ecosystem_data: Dict[str, Any]) -> float:
        """Calculate ecosystem health score"""
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

    def render_dashboard(self):
        """Render the complete dashboard"""
        if not self.daemon_client.is_daemon_running():
            self.clear_screen()
            print("🔴 Thronglet Daemon Not Running")
            print("Start with: python daemon.py")
            return

        # Get data
        response = self.daemon_client.send_command("network_overview")
        if not response or "error" in response:
            self.clear_screen()
            print(f"❌ Error getting data: {response.get(
                'error', 'Unknown error') if response else 'No response'}")
            return

        ecosystem_data = response['ecosystem_data']

        # Get terminal size
        width, height = self.get_terminal_size()

        self.clear_screen()

        # Header
        header_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = f"🐾 THRONGLET ECOSYSTEM DASHBOARD - {header_time}"
        print(f"\033[1;36m{title.center(width)}\033[0m")
        print("═" * width)

        # Calculate panel dimensions
        panel_width = width // 2 - 2
        panel_height = (height - 6) // 2

        # Top row: Ecosystem Summary + Machine Grid
        print(f"\033[1;33m┌─ 🌐 ECOSYSTEM OVERVIEW {
              ' ' * (panel_width - 22)}┐\033[0m", end="")
        print(f" \033[1;33m┌─ 🖥️ MACHINES {' ' * (panel_width - 12)}┐\033[0m")

        summary_lines = self.render_ecosystem_summary(
            ecosystem_data, panel_width)
        machine_lines = self.render_machine_grid(
            ecosystem_data, panel_width, panel_height)

        max_lines = max(len(summary_lines), len(machine_lines))
        for i in range(max_lines):
            left_line = summary_lines[i] if i < len(summary_lines) else ""
            right_line = machine_lines[i] if i < len(machine_lines) else ""

            left_padded = f"│ {left_line:<{panel_width-2}} │"
            right_padded = f" │ {right_line:<{panel_width-2}} │"
            print(f"{left_padded}{right_padded}")

        # Close top panels
        print(f"└{'─' * (panel_width-1)}┘ └{'─' * (panel_width-1)}┘")

        # Bottom row: Activity Feed + Population Chart
        print(f"\033[1;33m┌─ 📊 ACTIVITY FEED {
              ' ' * (panel_width - 17)}┐\033[0m", end="")
        print(f" \033[1;33m┌─ 📈 POPULATION TREND {
              ' ' * (panel_width - 20)}┐\033[0m")

        activity_lines = self.render_activity_feed(panel_width, panel_height)
        chart_lines = self.render_population_chart(panel_width, panel_height)

        max_lines = max(len(activity_lines), len(chart_lines))
        for i in range(max_lines):
            left_line = activity_lines[i] if i < len(activity_lines) else ""
            right_line = chart_lines[i] if i < len(chart_lines) else ""

            left_padded = f"│ {left_line:<{panel_width-2}} │"
            right_padded = f" │ {right_line:<{panel_width-2}} │"
            print(f"{left_padded}{right_padded}")

        # Close bottom panels
        print(f"└{'─' * (panel_width-1)}┘ └{'─' * (panel_width-1)}┘")

        # Footer
        print("═" * width)
        footer = f"🔄 Auto-refresh: {self.refresh_rate}s | Press Ctrl+C to exit"
        print(f"\033[2m{footer.center(width)}\033[0m")

        self.last_update = time.time()

    def run(self):
        """Run the dashboard in real-time mode"""
        self.running = True
        print("🚀 Starting Thronglet Dashboard...")
        print("Press Ctrl+C to exit")
        time.sleep(2)

        try:
            while self.running:
                self.render_dashboard()
                time.sleep(self.refresh_rate)
        except KeyboardInterrupt:
            self.clear_screen()
            print("\n👋 Dashboard stopped")
            self.running = False
        except Exception as e:
            self.clear_screen()
            print(f"❌ Dashboard error: {e}")
            self.running = False


def main():
    """Main entry point for dashboard"""
    dashboard = TerminalDashboard()

    if len(sys.argv) > 1 and sys.argv[1] == "--refresh-rate":
        try:
            dashboard.refresh_rate = float(sys.argv[2])
        except (IndexError, ValueError):
            print("Usage: python dashboard.py --refresh-rate <seconds>")
            sys.exit(1)

    dashboard.run()


if __name__ == "__main__":
    main()
