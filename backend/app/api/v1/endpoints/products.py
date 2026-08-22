from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.repositories.product import ProductRepository
from app.schemas.product import ProductResponse
from app.services.product import ProductService

router = APIRouter(
    prefix="/products",
)


def get_product_service(
    db: Session = Depends(get_db),
) -> ProductService:
    repository = ProductRepository(db)
    return ProductService(repository)


@router.get(
    "",
    response_model=list[ProductResponse],
)
def get_products(
    service: ProductService = Depends(get_product_service),
):
    return service.get_all()


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
):
    product = service.get_by_id(product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )

    return product
