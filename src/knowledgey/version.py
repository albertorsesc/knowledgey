from dataclasses import dataclass
from importlib.metadata import version as distribution_version

DISTRIBUTION_NAME = "knowledgey"


@dataclass(frozen=True)
class VersionInfo:
    name: str
    version: str

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "version": self.version}

def get_version() -> VersionInfo:
    return VersionInfo(name=DISTRIBUTION_NAME, version=distribution_version(DISTRIBUTION_NAME))