from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ProcessingArgs(BaseModel):
    """Pydantic model for validated command-line arguments."""
    sys_prompt: str
    input: Optional[Path] = None
    output: Optional[Path] = None
    threshold: float = Field(0.7, ge=0, le=1)
    api_key: Optional[str]
    max_chars: int = Field(8000, gt=0)
    pairs: bool = Field(False)
    name: str
    no_mod: bool = False
    dir: Optional[Path] = None
    merge: bool = Field(default=False)

    @field_validator('dir', mode="before")
    def validate_dir(cls, v: Path) -> Optional[Path]:
        """Validate that the directory exists."""
        if not v:
            return None
        if isinstance(v, str):
            v = Path(v)
        if not v.is_dir():
            raise ValueError(f"Directory does not exist: {v}")
        return v

