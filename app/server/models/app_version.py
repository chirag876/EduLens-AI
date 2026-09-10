from app.server.models.generic import BaseModel
from app.server.static.enums import VersionPlatform


class SemanticVersion(BaseModel):
    major: int
    minor: int
    patch: int


class VersionModel(BaseModel):
    sem_ver: SemanticVersion
    platform: VersionPlatform
    changelog: list[str]
    requires_logout: bool = False
