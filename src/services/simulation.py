import time
import threading
import uuid
import random
from typing import List, Dict
import logging
from ..domain.creature import Creature, CreatureState, WorldState
from ..domain.behavior import BehaviorFSM, process_pending_offspring, get_creature_statistics
from ..infrastructure.repository import FileRepository


class SimulationEngine:
    def __init__(self, tick_rate: float = 5.0):
        self.tick_rate = tick_rate
        self.running = False
        self.creatures: Dict[str, Creature] = {}
        self.world_state = WorldState()
        self.behavior_fsm = BehaviorFSM()
        self.repository = FileRepository()
        self.logger = logging.getLogger(__name__)
        self._tick_thread = None
        self._tick_count = 0

        # Statistics
        self._last_stats_update = time.time()
        self._births_this_session = 0
        self._deaths_this_session = 0

    def start(self):
        """Start the simulation loop"""
        if self.running:
            return

        self.running = True
        self.load_state()
        self._tick_thread = threading.Thread(target=self._simulation_loop)
        self._tick_thread.daemon = True
        self._tick_thread.start()
        self.logger.info("Simulation started")

    def stop(self):
        """Stop the simulation loop"""
        self.running = False
        if self._tick_thread:
            self._tick_thread.join()
        self.save_state()
        self.logger.info("Simulation stopped")

    def _simulation_loop(self):
        """Main simulation tick loop"""
        while self.running:
            try:
                self.tick()
                time.sleep(self.tick_rate)
            except Exception as e:
                self.logger.error(f"Simulation tick error: {e}")

    def tick(self):
        """Single simulation update"""
        self._tick_count += 1

        # Update world state first
        self._update_world()

        # Process all creatures
        creatures_to_remove = []
        for creature_id, creature in self.creatures.items():
            self._update_creature(creature)

            # Mark dying creatures for removal
            if creature.state == CreatureState.DYING:
                creatures_to_remove.append(creature_id)

        # Remove dead creatures
        for creature_id in creatures_to_remove:
            dead_creature = self.creatures[creature_id]
            self.logger.info(f"Creature {dead_creature.name} died at age {dead_creature.age} "
                             f"(cause: {dead_creature.traits.get(
                                 'death_cause', 'unknown')}) "
                             f"Final happiness: {dead_creature.happiness}")
            del self.creatures[creature_id]
            self.world_state.population_count -= 1
            self._deaths_this_session += 1

        # Process reproduction - create new creatures
        new_creatures = process_pending_offspring(
            self.creatures, self.world_state)
        for new_creature in new_creatures:
            self.creatures[new_creature.id] = new_creature
            self.world_state.population_count += 1
            self._births_this_session += 1
            self.logger.info(f"New creature born: {new_creature.name} "
                             f"(parent: {new_creature.traits.get(
                                 'parent_id', 'unknown')[:8]}) "
                             f"Starting happiness: {new_creature.happiness}")

        # Periodic logging and saves
        if self._tick_count % 12 == 0:  # Every minute (12 ticks * 5 seconds)
            self._log_population_status()

        if self._tick_count % 6 == 0:  # Every 30 seconds
            self.save_state()

    def _update_world(self):
        """Update world resources and environment"""
        # Regenerate food
        if self.world_state.food < self.world_state.max_food:
            self.world_state.food = min(
                self.world_state.max_food,
                self.world_state.food + self.world_state.food_regen_rate
            )

        # Random environmental changes occasionally
        if self._tick_count % 60 == 0:  # Every 5 minutes
            # Small temperature fluctuations
            temp_change = random.randint(-2, 2)
            self.world_state.temperature = max(
                10, min(30, self.world_state.temperature + temp_change))

            # Occasional food abundance or scarcity
            if random.random() < 0.1:  # 10% chance
                if random.random() < 0.5:
                    # Food abundance - makes all creatures happier
                    self.world_state.food = min(
                        self.world_state.max_food, self.world_state.food + 20)
                    self.logger.info("Environmental event: Food abundance!")
                    # Boost happiness for all creatures
                    for creature in self.creatures.values():
                        creature.happiness = min(
                            100, creature.happiness + random.randint(5, 10))
                else:
                    # Food scarcity - makes creatures less happy
                    self.world_state.food = max(0, self.world_state.food - 15)
                    self.logger.info("Environmental event: Food scarcity!")
                    # Reduce happiness for all creatures
                    for creature in self.creatures.values():
                        creature.happiness = max(
                            0, creature.happiness - random.randint(3, 8))

        # Update population count
        self.world_state.population_count = len(self.creatures)
        self.world_state.last_update = time.time()

    def _update_creature(self, creature: Creature):
        """Update single creature using FSM"""
        # Age and natural processes
        creature.age += 1
        # Get hungrier over time
        creature.hunger = min(100, creature.hunger + 2)

        # Environmental happiness effects
        # Temperature affects happiness
        if self.world_state.temperature < 15 or self.world_state.temperature > 25:
            # Uncomfortable temperature
            creature.happiness = max(
                0, creature.happiness - random.randint(0, 2))
        elif 18 <= self.world_state.temperature <= 22:
            # Perfect temperature
            creature.happiness = min(
                100, creature.happiness + random.randint(0, 1))

        # Social happiness - creatures are happier when there are others around
        population_ratio = len(self.creatures) / \
            self.world_state.max_population
        if population_ratio > 0.8:
            # Overcrowding stress
            creature.happiness = max(
                0, creature.happiness - random.randint(1, 2))
        elif 0.3 <= population_ratio <= 0.7:
            # Good social balance
            creature.happiness = min(
                100, creature.happiness + random.randint(0, 1))
        elif population_ratio < 0.1:
            # Loneliness
            creature.happiness = max(
                0, creature.happiness - random.randint(0, 1))

        # Age-related happiness changes
        age_ratio = creature.age / creature.max_age
        if age_ratio > 0.9:
            # Very old - declining happiness
            creature.happiness = max(
                0, creature.happiness - random.randint(1, 3))
        elif age_ratio > 0.8:
            # Old age starting to affect happiness
            creature.happiness = max(
                0, creature.happiness - random.randint(0, 2))
        elif 0.2 <= age_ratio <= 0.6:
            # Prime of life - naturally happy
            creature.happiness = min(
                100, creature.happiness + random.randint(0, 1))

        # Energy affects happiness
        if creature.energy < 20:
            # Low energy makes creatures sad
            creature.happiness = max(
                0, creature.happiness - random.randint(2, 4))
        elif creature.energy > 80:
            # High energy makes creatures happy
            creature.happiness = min(
                100, creature.happiness + random.randint(0, 2))

        # Apply FSM behavior (which will also modify happiness)
        self.behavior_fsm.update_creature(creature, self.world_state)

    def _log_population_status(self):
        """Log current population status"""
        stats = get_creature_statistics(self.creatures)
        happiness_dist = stats.get('happiness_distribution', {})
        happy_count = happiness_dist.get(
            'happy', 0) + happiness_dist.get('ecstatic', 0)
        sad_count = happiness_dist.get(
            'miserable', 0) + happiness_dist.get('sad', 0)

        self.logger.info(f"Population: {stats['total_population']}, "
                         f"Avg Age: {stats['average_age']}, "
                         f"Avg Energy: {stats['average_energy']}, "
                         f"Avg Happiness: {stats['average_happiness']}, "
                         f"Happy: {happy_count}, Sad: {sad_count}, "
                         f"Food: {self.world_state.food}, "
                         f"Births: {self._births_this_session}, "
                         f"Deaths: {self._deaths_this_session}")

    def add_creature(self, name: str = None) -> Creature:
        """Add new creature to simulation"""
        if not self.world_state.can_support_creature():
            raise ValueError("Cannot add creature: Population limit reached")

        if not name:
            name = f"Thronglet-{len(self.creatures):04d}"

        # Random starting happiness (but not too extreme)
        starting_happiness = random.randint(40, 60)

        creature = Creature(
            id=str(uuid.uuid4()),
            name=name,
            happiness=starting_happiness,
            current_machine=self.get_machine_id(),
            traits={'generation': 0, 'birth_time': time.time()}
        )

        self.creatures[creature.id] = creature
        self.world_state.population_count += 1
        self.logger.info(f"Creature added: {creature.name} ({creature.id[:8]}) "
                         f"Starting happiness: {creature.happiness}")
        return creature

    def remove_creature(self, creature_id: str) -> bool:
        """Remove creature from simulation"""
        if creature_id in self.creatures:
            creature = self.creatures[creature_id]
            del self.creatures[creature_id]
            self.world_state.population_count -= 1
            self.logger.info(f"Creature removed: {creature.name}")
            return True
        return False

    def get_machine_id(self) -> str:
        """Get unique machine identifier"""
        import socket
        return socket.gethostname()

    def get_simulation_stats(self) -> Dict:
        """Get comprehensive simulation statistics"""
        creature_stats = get_creature_statistics(self.creatures)
        fsm_stats = self.behavior_fsm.get_transition_stats()

        return {
            'runtime': {
                'tick_count': self._tick_count,
                'uptime_seconds': (time.time() - self._last_stats_update) if self._last_stats_update else 0,
                'births_this_session': self._births_this_session,
                'deaths_this_session': self._deaths_this_session
            },
            'world': {
                'food': self.world_state.food,
                'max_food': self.world_state.max_food,
                'temperature': self.world_state.temperature,
                'population_count': self.world_state.population_count,
                'max_population': self.world_state.max_population
            },
            'creatures': creature_stats,
            'behavior_transitions': fsm_stats
        }

    def load_state(self):
        """Load simulation state from files"""
        self.creatures = self.repository.load_creatures()
        self.world_state = self.repository.load_world_state()

        # Initialize generation tracking for loaded creatures
        for creature in self.creatures.values():
            if 'generation' not in creature.traits:
                creature.traits['generation'] = 0
            # Ensure happiness is within bounds for loaded creatures
            creature.happiness = max(0, min(100, creature.happiness))

        self.logger.info(
            f"Loaded {len(self.creatures)} creatures from storage")

    def save_state(self):
        """Save simulation state to files"""
        try:
            self.repository.save_creatures(self.creatures)
            self.repository.save_world_state(self.world_state)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def force_reproduction(self, creature_id: str) -> bool:
        """Force a creature to reproduce (for testing)"""
        if creature_id not in self.creatures:
            return False

        creature = self.creatures[creature_id]
        if (creature.energy > 20 and
            self.world_state.can_support_creature() and
                creature.state != CreatureState.DYING):

            creature.state = CreatureState.REPRODUCING
            self.logger.info(f"Forced reproduction for {
                             creature.name} (happiness: {creature.happiness})")
            return True
        return False

    def feed_all_creatures(self):
        """Emergency feeding for all creatures (for testing)"""
        fed_count = 0
        for creature in self.creatures.values():
            if creature.hunger > 50:
                creature.hunger = max(0, creature.hunger - 40)
                creature.energy = min(100, creature.energy + 10)
                # Emergency feeding makes creatures happy
                creature.happiness = min(
                    100, creature.happiness + random.randint(5, 15))
                fed_count += 1

        self.logger.info(f"Emergency feeding: {
                         fed_count} creatures fed and made happier")
        return fed_count
