from app.models.product import Product
from app.repositories.product import ProductRepository


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
