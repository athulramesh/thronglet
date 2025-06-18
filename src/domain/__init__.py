"""
Domain layer - Core business models and behavior logic.

Contains the fundamental entities and rules of the Thronglet ecosystem:
- Creature models and lifecycle
- World state and environment
- Behavior state machines
"""

from .creature import Creature, CreatureState, WorldState
from .behavior import BehaviorFSM, BehaviorState

__all__ = [
    "Creature",
    "CreatureState",
    "WorldState",
    "BehaviorFSM",
    "BehaviorState"
]
