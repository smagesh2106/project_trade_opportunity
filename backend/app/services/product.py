from app.models import Product
from app.repositories.product import ProductRepository
from app.schemas.product import (
    ProductAliasResponse,
    ProductHSCodeResponse,
    ProductResponse,
)


class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def get_all(self) -> list[ProductResponse]:
        products = self.repository.get_all()

        return [self._to_response(product) for product in products]

    def get_by_id(
        self,
        product_id: int,
    ) -> ProductResponse | None:
        product = self.repository.get_by_id(product_id)

        if product is None:
            return None

        return self._to_response(product)

    @staticmethod
    def _to_response(product: Product) -> ProductResponse:
        aliases = [
            ProductAliasResponse.model_validate(alias) for alias in product.aliases
        ]

        hs_codes = [
            ProductHSCodeResponse(
                id=mapping.hs_code.id,
                code=mapping.hs_code.code,
                description=mapping.hs_code.description,
                level=mapping.hs_code.level,
                mapping_type=mapping.mapping_type,
                confidence=mapping.confidence,
                source=mapping.source,
            )
            for mapping in product.hs_mappings
        ]

        return ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            category=product.category,
            active=product.active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            aliases=aliases,
            hs_codes=hs_codes,
        )
