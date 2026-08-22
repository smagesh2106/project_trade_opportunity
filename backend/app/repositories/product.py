from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Product, ProductHSCode, ProductAlias


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Product]:
        statement = (
            select(Product)
            .options(
                joinedload(Product.aliases),
                joinedload(Product.hs_mappings).joinedload(ProductHSCode.hs_code),
            )
            .where(Product.active.is_(True))
            .order_by(Product.name)
        )

        return list(self.db.execute(statement).unique().scalars().all())

    def get_by_id(self, product_id: int) -> Product | None:
        statement = (
            select(Product)
            .options(
                joinedload(Product.aliases),
                joinedload(Product.hs_mappings).joinedload(ProductHSCode.hs_code),
            )
            .where(
                Product.id == product_id,
                Product.active.is_(True),
            )
        )

        return self.db.execute(statement).unique().scalar_one_or_none()

    def find_by_alias(
        self,
        alias: str,
    ) -> Product | None:
        normalized_alias = " ".join(alias.lower().strip().split())

        statement = (
            select(Product)
            .join(Product.aliases)
            .where(
                Product.active.is_(True),
                func.lower(ProductAlias.alias) == normalized_alias,
            )
            .options(
                joinedload(Product.aliases),
                joinedload(Product.hs_mappings).joinedload(ProductHSCode.hs_code),
            )
        )

        return self.db.execute(statement).unique().scalar_one_or_none()
