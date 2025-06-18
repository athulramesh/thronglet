from abc import ABC, abstractmethod
from typing import Dict, Type, Optional
import time
import uuid
from .creature import Creature, CreatureState, WorldState


class BehaviorState(ABC):
    @abstractmethod
    def enter(self, creature: Creature, world: WorldState) -> None:
        pass

    @abstractmethod
    def update(self, creature: Creature, world: WorldState) -> Optional[CreatureState]:
        pass

    @abstractmethod
    def exit(self, creature: Creature, world: WorldState) -> None:
        pass


class IdleState(BehaviorState):
    def enter(self, creature: Creature, world: WorldState) -> None:
        # Minimal energy consumption
        creature.energy = max(0, creature.energy - 1)

    def update(self, creature: Creature, world: WorldState) -> Optional[CreatureState]:
        # Check death conditions first
        if creature.age >= creature.max_age or creature.energy <= 0:
            return CreatureState.DYING

        # Check hunger
        if creature.hunger > 70 and world.has_food():
            return CreatureState.HUNGRY

        # Check reproduction conditions
        if (creature.age > 100 and
            creature.energy > 50 and
            creature.happiness > 60 and
            world.can_support_creature() and
                time.time() - creature.last_reproduced > 300):  # 5 minutes cooldown
            return CreatureState.REPRODUCING

        return None

    def exit(self, creature: Creature, world: WorldState) -> None:
        pass


class HungryState(BehaviorState):
    def enter(self, creature: Creature, world: WorldState) -> None:
        creature.happiness = max(0, creature.happiness - 5)
        # Higher energy consumption when hungry
        creature.energy = max(0, creature.energy - 2)

    def update(self, creature: Creature, world: WorldState) -> Optional[CreatureState]:
        # Check death conditions first
        if creature.age >= creature.max_age or creature.energy <= 0:
            return CreatureState.DYING

        # If food is available, start eating
        if world.has_food():
            return CreatureState.EATING

        # If not hungry anymore (somehow), go back to idle
        if creature.hunger <= 30:
            return CreatureState.IDLE

        return None

    def exit(self, creature: Creature, world: WorldState) -> None:
        pass


class EatingState(BehaviorState):
    def enter(self, creature: Creature, world: WorldState) -> None:
        # Consume food from the world
        if world.consume_food(1):
            # Successful eating
            # Reduce hunger significantly
            creature.hunger = max(0, creature.hunger - 30)
            # Restore some energy
            creature.energy = min(100, creature.energy + 10)
            # Eating makes creatures happy
            creature.happiness = min(100, creature.happiness + 5)
            creature.last_fed = time.time()
        else:
            # No food available, this shouldn't happen but handle gracefully
            creature.happiness = max(0, creature.happiness - 10)

    def update(self, creature: Creature, world: WorldState) -> Optional[CreatureState]:
        # Check death conditions
        if creature.age >= creature.max_age or creature.energy <= 0:
            return CreatureState.DYING

        # Eating is a quick action, return to idle after one tick
        return CreatureState.IDLE

    def exit(self, creature: Creature, world: WorldState) -> None:
        pass


class ReproducingState(BehaviorState):
    def enter(self, creature: Creature, world: WorldState) -> None:
        # Reproduction is energy-intensive
        creature.energy = max(0, creature.energy - 20)
        # Reproduction increases happiness
        creature.happiness = min(100, creature.happiness + 15)
        creature.last_reproduced = time.time()

    def update(self, creature: Creature, world: WorldState) -> Optional[CreatureState]:
        # Check death conditions
        if creature.age >= creature.max_age or creature.energy <= 0:
            return CreatureState.DYING

        # Create offspring if world can support it
        if world.can_support_creature():
            self._create_offspring(creature, world)

        # Reproduction is complete, return to idle
        return CreatureState.IDLE

    def exit(self, creature: Creature, world: WorldState) -> None:
        pass

    def _create_offspring(self, parent: Creature, world: WorldState) -> None:
        """Create a new creature as offspring"""
        # This is a bit of a hack - we need access to the simulation engine
        # For now, we'll create the offspring data and rely on the simulation
        # engine to pick it up via a special mechanism

        # Generate offspring with inherited traits
        offspring_name = f"{parent.name}-Jr-{int(time.time() % 1000)}"

        # Basic inheritance - offspring gets some traits from parent
        inherited_max_age = parent.max_age + \
            (-50 + (hash(parent.id) % 100))  # Slight variation
        # Start with good energy
        inherited_energy = min(100, parent.energy + 10)

        # Store offspring data in parent's traits for simulation engine to pick up
        if 'pending_offspring' not in parent.traits:
            parent.traits['pending_offspring'] = []

        offspring_data = {
            'name': offspring_name,
            'max_age': max(500, inherited_max_age),  # Ensure minimum viability
            'energy': inherited_energy,
            'parent_id': parent.id,
            'created_at': time.time()
        }

        parent.traits['pending_offspring'].append(offspring_data)


class DyingState(BehaviorState):
    def enter(self, creature: Creature, world: WorldState) -> None:
        # Creature is dying, all stats drop
        creature.energy = 0
        creature.happiness = max(0, creature.happiness - 20)

        # Mark death time
        creature.traits['death_time'] = time.time()
        creature.traits['death_cause'] = self._determine_death_cause(creature)

    def update(self, creature: Creature, world: WorldState) -> Optional[CreatureState]:
        # Death is final - stay in dying state
        # The simulation engine will remove the creature
        return None

    def exit(self, creature: Creature, world: WorldState) -> None:
        # Final cleanup before removal
        pass

    def _determine_death_cause(self, creature: Creature) -> str:
        """Determine why the creature is dying"""
        if creature.age >= creature.max_age:
            return "old_age"
        elif creature.energy <= 0:
            return "starvation"
        else:
            return "unknown"


class BehaviorFSM:
    def __init__(self):
        self.states: Dict[CreatureState, BehaviorState] = {
            CreatureState.IDLE: IdleState(),
            CreatureState.HUNGRY: HungryState(),
            CreatureState.EATING: EatingState(),
            CreatureState.REPRODUCING: ReproducingState(),
            CreatureState.DYING: DyingState()
        }

        # Track state transition statistics
        self.transition_counts = {}

    def update_creature(self, creature: Creature, world: WorldState) -> None:
        """Update creature behavior using finite state machine"""
        current_state = self.states[creature.state]
        new_state = current_state.update(creature, world)

        if new_state and new_state != creature.state:
            # Record transition for statistics
            transition = f"{creature.state.value} -> {new_state.value}"
            self.transition_counts[transition] = self.transition_counts.get(
                transition, 0) + 1

            # Execute state transition
            current_state.exit(creature, world)
            creature.state = new_state
            self.states[new_state].enter(creature, world)

    def get_transition_stats(self) -> Dict[str, int]:
        """Get statistics about state transitions"""
        return self.transition_counts.copy()

    def reset_stats(self) -> None:
        """Reset transition statistics"""
        self.transition_counts.clear()

# Additional helper functions for the simulation engine


def process_pending_offspring(creatures: Dict[str, Creature], world: WorldState) -> list:
    """
    Process any pending offspring from reproduction.
    Returns list of new creatures to add to simulation.
    """
    new_creatures = []

    for creature in creatures.values():
        if 'pending_offspring' in creature.traits and creature.traits['pending_offspring']:
            for offspring_data in creature.traits['pending_offspring']:
                if world.can_support_creature():
                    # Create new creature
                    new_creature = Creature(
                        id=str(uuid.uuid4()),
                        name=offspring_data['name'],
                        max_age=offspring_data['max_age'],
                        energy=offspring_data['energy'],
                        current_machine=creature.current_machine,
                        traits={
                            'parent_id': offspring_data['parent_id'],
                            'birth_time': time.time(),
                            'generation': creature.traits.get('generation', 0) + 1
                        }
                    )
                    new_creatures.append(new_creature)

            # Clear processed offspring
            creature.traits['pending_offspring'] = []

    return new_creatures


def get_creature_statistics(creatures: Dict[str, Creature]) -> Dict[str, any]:
    """
    Generate statistics about the creature population.
    """
    if not creatures:
        return {
            'total_population': 0,
            'average_age': 0,
            'average_energy': 0,
            'average_happiness': 0,
            'state_distribution': {},
            'age_distribution': {},
            'generations': {}
        }

    total_age = sum(c.age for c in creatures.values())
    total_energy = sum(c.energy for c in creatures.values())
    total_happiness = sum(c.happiness for c in creatures.values())

    # State distribution
    state_dist = {}
    for creature in creatures.values():
        state = creature.state.value
        state_dist[state] = state_dist.get(state, 0) + 1

    # Age distribution (buckets)
    age_dist = {'young': 0, 'adult': 0, 'old': 0}
    for creature in creatures.values():
        if creature.age < 200:
            age_dist['young'] += 1
        elif creature.age < 700:
            age_dist['adult'] += 1
        else:
            age_dist['old'] += 1

    # Generation tracking
    generations = {}
    for creature in creatures.values():
        gen = creature.traits.get('generation', 0)
        generations[f"gen_{gen}"] = generations.get(f"gen_{gen}", 0) + 1

    return {
        'total_population': len(creatures),
        'average_age': total_age // len(creatures),
        'average_energy': total_energy // len(creatures),
        'average_happiness': total_happiness // len(creatures),
        'state_distribution': state_dist,
        'age_distribution': age_dist,
        'generations': generations
    }
