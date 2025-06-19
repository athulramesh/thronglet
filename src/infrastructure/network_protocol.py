from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum
import time
import json


class MessageType(Enum):
    DISCOVERY = "discovery"
    DISCOVERY_RESPONSE = "discovery_response"
    HEARTBEAT = "heartbeat"
    CREATURE_MIGRATION = "creature_migration"
    CREATURE_MIGRATION_ACK = "creature_migration_ack"
    RESOURCE_SHARE = "resource_share"
    WORLD_STATE_SYNC = "world_state_sync"


@dataclass
class NetworkMessage:
    message_type: MessageType
    sender_id: str
    recipient_id: Optional[str]
    timestamp: float
    payload: Dict[str, Any]
    message_id: str

    def to_json(self) -> str:
        return json.dumps({
            'message_type': self.message_type.value,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'timestamp': self.timestamp,
            'payload': self.payload,
            'message_id': self.message_id
        })

    @classmethod
    def from_json(cls, json_str: str) -> 'NetworkMessage':
        data = json.loads(json_str)
        return cls(
            message_type=MessageType(data['message_type']),
            sender_id=data['sender_id'],
            recipient_id=data['recipient_id'],
            timestamp=data['timestamp'],
            payload=data['payload'],
            message_id=data['message_id']
        )


@dataclass
class CreatureMigrationData:
    creature_data: Dict[str, Any]
    migration_reason: str = "random_walk"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'creature_data': self.creature_data,
            'migration_reason': self.migration_reason
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CreatureMigrationData':
        return cls(
            creature_data=data['creature_data'],
            migration_reason=data.get('migration_reason', 'random_walk')
        )
