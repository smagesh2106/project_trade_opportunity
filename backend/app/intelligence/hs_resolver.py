from app.models.product import Product
from app.schemas.intelligence import ResolvedHSCode


class HSResolver:
    def resolve(
        self,
        product: Product | None,
    ) -> list[ResolvedHSCode]:
        if product is None:
            return []

        resolved_codes: list[ResolvedHSCode] = []

        for mapping in product.hs_mappings:
            hs_code = mapping.hs_code

            if hs_code is None:
                continue

            if not hs_code.active:
                continue

            resolved_codes.append(
                ResolvedHSCode(
                    id=hs_code.id,
                    code=hs_code.code,
                    description=hs_code.description,
                    level=hs_code.level,
                    confidence=(
                        float(mapping.confidence)
                        if mapping.confidence is not None
                        else 0.0
                    ),
                    mapping_type=mapping.mapping_type,
                    source=mapping.source,
                )
            )

        return resolved_codes
