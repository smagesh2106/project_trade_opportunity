from app.models import HSCode
from app.repositories.hs_code import HSCodeRepository


class HSCodeService:
    def __init__(self, repository: HSCodeRepository):
        self.repository = repository

    def get_all(
        self,
        hs_version_id: int | None = None,
        level: int | None = None,
        parent_id: int | None = None,
    ) -> list[HSCode]:
        return self.repository.get_all(
            hs_version_id=hs_version_id,
            level=level,
            parent_id=parent_id,
        )

    def get_by_id(
        self,
        hs_code_id: int,
    ) -> HSCode | None:
        return self.repository.get_by_id(hs_code_id)

    def get_by_code(
        self,
        code: str,
        hs_version_id: int | None = None,
    ) -> HSCode | None:
        return self.repository.get_by_code(
            code=code,
            hs_version_id=hs_version_id,
        )