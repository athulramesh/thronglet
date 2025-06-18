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
