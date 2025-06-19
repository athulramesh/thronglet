from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional
import uuid
import time


class CreatureState(Enum):
    IDLE = "idle"
    HUNGRY = "hungry"
    EATING = "eating"
    REPRODUCING = "reproducing"
    DYING = "dying"


@dataclass
class Creature:
    id: str
    name: str
    age: int = 0
    energy: int = 100
    happiness: int = 50
    hunger: int = 0
    current_machine: str = ""
    max_age: int = 1000
    state: CreatureState = CreatureState.IDLE
    traits: Dict = None
    last_fed: float = 0
    last_reproduced: float = 0

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.traits is None:
            self.traits = {}
        if not self.last_fed:
            self.last_fed = time.time()

    # ADD THESE MIGRATION METHODS:

    def can_migrate(self) -> bool:
        """Check if creature is eligible for migration"""
        return (
            self.state not in [CreatureState.DYING, CreatureState.REPRODUCING] and
            self.energy > 30 and
            self.age > 50  # Minimum age for migration
        )

    def prepare_for_migration(self) -> Dict[str, any]:
        """Serialize creature data for network transfer"""
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'energy': self.energy,
            'happiness': self.happiness,
            'hunger': self.hunger,
            'max_age': self.max_age,
            'state': self.state.value,
            'traits': self.traits,
            'last_fed': self.last_fed,
            'last_reproduced': self.last_reproduced
        }

    @classmethod
    def from_migration_data(cls, data: Dict[str, any], new_machine_id: str) -> 'Creature':
        """Create creature from migration data"""
        creature = cls(
            id=data['id'],
            name=data['name'],
            age=data['age'],
            energy=max(data['energy'] - 5, 10),  # Migration costs energy
            happiness=data['happiness'],
            hunger=min(data['hunger'] + 10, 100),  # Migration increases hunger
            current_machine=new_machine_id,
            max_age=data['max_age'],
            state=CreatureState(data['state']),
            traits=data['traits'],
            last_fed=data['last_fed'],
            last_reproduced=data['last_reproduced']
        )

        # Mark migration in traits
        creature.traits['last_migration'] = time.time()
        creature.traits['migration_count'] = creature.traits.get(
            'migration_count', 0) + 1

        return creature


@dataclass
class WorldState:
    food: int = 100
    max_food: int = 100
    temperature: int = 20
    population_count: int = 0
    max_population: int = 50
    food_regen_rate: int = 1
    last_update: float = 0

    def can_support_creature(self) -> bool:
        return self.population_count < self.max_population

    def has_food(self) -> bool:
        return self.food > 0

    def consume_food(self, amount: int = 1) -> bool:
        if self.food >= amount:
            self.food -= amount
            return True
        return False
