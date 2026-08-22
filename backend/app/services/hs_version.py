from app.models import HSVersion
from app.repositories.hs_version import HSVersionRepository


class HSVersionService:
    def __init__(self, repository: HSVersionRepository):
        self.repository = repository

    def get_all(self) -> list[HSVersion]:
        return self.repository.get_all()

    def get_by_id(self, version_id: int) -> HSVersion | None:
        return self.repository.get_by_id(version_id)