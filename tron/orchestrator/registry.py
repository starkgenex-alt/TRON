from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from pathlib import Path
import json

@dataclass
class ArtifactMetadata:
    artifact_id: str
    module: str
    version: str
    adapter: str
    task_name: str
    metrics: Dict[str, float]
    size_bytes: int
    substrates: List[str]
    training_config: Dict[str, float]
    created_at: str

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ArtifactMetadata":
        return cls(
            artifact_id=data["artifact_id"],
            module=data["module"],
            version=data.get("version", ""),
            adapter=data.get("adapter", ""),
            task_name=data.get("task_name", ""),
            metrics=data.get("metrics", {}),
            size_bytes=int(data.get("size_bytes", 0)),
            substrates=list(data.get("substrates", [])),
            training_config=data.get("training_config", {}),
            created_at=data.get("created_at", ""),
        )

class ArtifactRegistry:
    def __init__(self, storage_path: Optional[str] = None):
        self._artifacts: Dict[str, ArtifactMetadata] = {}
        self.storage_path = Path(storage_path) if storage_path else None
        if self.storage_path and self.storage_path.exists():
            try:
                self.load(self.storage_path)
            except Exception:
                # Best-effort: ignore load errors and start with empty registry
                self._artifacts = {}

    def register(self, metadata: ArtifactMetadata) -> None:
        self._artifacts[metadata.artifact_id] = metadata

    def get(self, artifact_id: str) -> Optional[ArtifactMetadata]:
        return self._artifacts.get(artifact_id)

    def find_by_module(self, module: str) -> List[ArtifactMetadata]:
        return [a for a in self._artifacts.values() if a.module == module]

    def all_artifacts(self) -> List[ArtifactMetadata]:
        return list(self._artifacts.values())

    def save(self, path: Optional[Path] = None) -> None:
        p = Path(path) if path else self.storage_path
        if p is None:
            raise ValueError("No storage path configured for ArtifactRegistry")
        data = [a.to_dict() for a in self._artifacts.values()]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2))

    def load(self, path: Optional[Path] = None) -> None:
        p = Path(path) if path else self.storage_path
        if p is None or not p.exists():
            return
        raw = json.loads(p.read_text())
        self._artifacts = {d["artifact_id"]: ArtifactMetadata.from_dict(d) for d in raw}
