from app.models.product import Product
from app.repositories.product import ProductRepository
from app.schemas.intelligence import ProductMatch, ResolvedProduct


class ProductMatcher:
    def __init__(
        self,
        repository: ProductRepository,
    ):
        self.repository = repository

    def find(
        self,
        product_text: str | None,
    ) -> Product | None:
        if not product_text:
            return None

        return self.repository.find_by_alias(product_text)

    def match(
        self,
        product_text: str | None,
    ) -> ProductMatch | None:
        product = self.find(product_text)

        if product is None:
            return None

        return ProductMatch(
            product=ResolvedProduct(
                id=product.id,
                name=product.name,
                confidence=1.0,
            ),
            match_type="exact_alias",
        )
