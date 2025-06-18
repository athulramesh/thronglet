import json
import os
import time
from typing import Dict, List
from pathlib import Path
from ..domain.creature import Creature, CreatureState, WorldState


class FileRepository:
    def __init__(self, data_dir: str = "/opt/thronglet/data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.creatures_file = self.data_dir / "creatures.json"
        self.world_file = self.data_dir / "world_state.json"
        self.peers_file = self.data_dir / "network_peers.json"

    def save_creatures(self, creatures: Dict[str, Creature]):
        """Save creatures to JSON file"""
        serialized = {}
        for creature_id, creature in creatures.items():
            serialized[creature_id] = {
                'id': creature.id,
                'name': creature.name,
                'age': creature.age,
                'energy': creature.energy,
                'happiness': creature.happiness,
                'hunger': creature.hunger,
                'current_machine': creature.current_machine,
                'max_age': creature.max_age,
                'state': creature.state.value,
                'traits': creature.traits,
                'last_fed': creature.last_fed,
                'last_reproduced': creature.last_reproduced
            }

        with open(self.creatures_file, 'w') as f:
            json.dump(serialized, f, indent=2)

    def load_creatures(self) -> Dict[str, Creature]:
        """Load creatures from JSON file"""
        if not self.creatures_file.exists():
            return {}

        with open(self.creatures_file, 'r') as f:
            data = json.load(f)

        creatures = {}
        for creature_id, creature_data in data.items():
            creature = Creature(
                id=creature_data['id'],
                name=creature_data['name'],
                age=creature_data['age'],
                energy=creature_data['energy'],
                happiness=creature_data['happiness'],
                hunger=creature_data['hunger'],
                current_machine=creature_data['current_machine'],
                max_age=creature_data['max_age'],
                state=CreatureState(creature_data['state']),
                traits=creature_data['traits'],
                last_fed=creature_data['last_fed'],
                last_reproduced=creature_data['last_reproduced']
            )
            creatures[creature_id] = creature

        return creatures

    def save_world_state(self, world_state: WorldState):
        """Save world state to JSON file"""
        data = {
            'food': world_state.food,
            'max_food': world_state.max_food,
            'temperature': world_state.temperature,
            'population_count': world_state.population_count,
            'max_population': world_state.max_population,
            'food_regen_rate': world_state.food_regen_rate,
            'last_update': world_state.last_update
        }

        with open(self.world_file, 'w') as f:
            json.dump(data, f, indent=2)

    def load_world_state(self) -> WorldState:
        """Load world state from JSON file"""
        if not self.world_file.exists():
            return WorldState()

        with open(self.world_file, 'r') as f:
            data = json.load(f)

        return WorldState(**data)
