from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ProcessingContext:
    """Stores context for chat processing."""
    person_index: int = 1
    person_map: Dict[str, str] = field(default_factory=dict)
    total_chars: int = 0
