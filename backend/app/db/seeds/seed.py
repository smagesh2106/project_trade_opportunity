from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import (
    Country,
    HSCode,
    HSVersion,
    Product,
    ProductAlias,
    ProductHSCode,
)


def seed_countries(db):
    countries = [
        {
            "iso2": "IN",
            "iso3": "IND",
            "name": "India",
            "official_name": "Republic of India",
            "region": "Asia",
            "subregion": "Southern Asia",
        },
        {
            "iso2": "SA",
            "iso3": "SAU",
            "name": "Saudi Arabia",
            "official_name": "Kingdom of Saudi Arabia",
            "region": "Asia",
            "subregion": "Western Asia",
        },
        {
            "iso2": "AE",
            "iso3": "ARE",
            "name": "United Arab Emirates",
            "official_name": "United Arab Emirates",
            "region": "Asia",
            "subregion": "Western Asia",
        },
        {
            "iso2": "DE",
            "iso3": "DEU",
            "name": "Germany",
            "official_name": "Federal Republic of Germany",
            "region": "Europe",
            "subregion": "Western Europe",
        },
        {
            "iso2": "US",
            "iso3": "USA",
            "name": "United States",
            "official_name": "United States of America",
            "region": "Americas",
            "subregion": "Northern America",
        },
    ]

    for data in countries:
        existing = db.scalar(
            select(Country).where(Country.iso3 == data["iso3"])
        )

        if existing is None:
            db.add(Country(**data))

    db.flush()


def seed_hs_version(db):
    version = db.scalar(
        select(HSVersion).where(HSVersion.version == "2022")
    )

    if version is None:
        version = HSVersion(
            name="Harmonized System",
            version="2022",
            source="Development seed data",
        )
        db.add(version)
        db.flush()

    return version


def seed_hs_codes(db, hs_version):
    codes = [
        {
            "code": "85",
            "description": "Electrical machinery and equipment and parts thereof",
            "level": 2,
            "parent_code": None,
        },
        {
            "code": "8537",
            "description": (
                "Boards, panels, consoles, desks, cabinets and other bases, "
                "equipped with two or more apparatus of heading 85.35 or 85.36, "
                "for electric control or the distribution of electricity, "
                "including those incorporating instruments or apparatus of "
                "Chapter 90, and numerical control apparatus, other than "
                "switching apparatus of heading 85.17."
            ),
            "level": 4,
            "parent_code": "85",
        },
        {
            "code": "85371",
            "description": "For a voltage not exceeding 1,000 V",
            "level": 5,
            "parent_code": "8537",
        },
        {
            "code": "853710",
            "description": "For a voltage not exceeding 1,000 V",
            "level": 6,
            "parent_code": "85371",
        },
        {
            "code": "85372",
            "description": "For a voltage exceeding 1,000 V",
            "level": 5,
            "parent_code": "8537",
        },
        {
            "code": "853720",
            "description": "For a voltage exceeding 1,000 V",
            "level": 6,
            "parent_code": "85372",
        },
    ]    

    code_objects = {}

    for data in codes:
        existing = db.scalar(
            select(HSCode).where(
                HSCode.hs_version_id == hs_version.id,
                HSCode.code == data["code"],
            )
        )

        if existing is None:
            parent = (
                code_objects.get(data["parent_code"])
                if data["parent_code"]
                else None
            )

            if parent is None and data["parent_code"]:
                parent = db.scalar(
                    select(HSCode).where(
                        HSCode.hs_version_id == hs_version.id,
                        HSCode.code == data["parent_code"],
                    )
                )

            existing = HSCode(
                hs_version_id=hs_version.id,
                code=data["code"],
                description=data["description"],
                level=data["level"],
                parent_id=parent.id if parent else None,
            )

            db.add(existing)
            db.flush()

        code_objects[data["code"]] = existing

    return code_objects


def seed_products(db, hs_codes):
    product = db.scalar(
        select(Product).where(
            Product.name == "Electrical Control Panels"
        )
    )

    if product is None:
        product = Product(
            name="Electrical Control Panels",
            description="Electrical control and distribution panel assemblies.",
            category="Electrical Equipment",
        )
        db.add(product)
        db.flush()

    aliases = [
        "electrical panels",
        "control panels",
        "distribution panels",
    ]

    for alias in aliases:
        existing = db.scalar(
            select(ProductAlias).where(
                ProductAlias.product_id == product.id,
                ProductAlias.alias == alias,
            )
        )

        if existing is None:
            db.add(
                ProductAlias(
                    product_id=product.id,
                    alias=alias,
                    language="en",
                    source="Development seed data",
                    confidence=1.0,
                )
            )

    hs_code = hs_codes["853710"]

    mapping = db.scalar(
        select(ProductHSCode).where(
            ProductHSCode.product_id == product.id,
            ProductHSCode.hs_code_id == hs_code.id,
        )
    )

    if mapping is None:
        db.add(
            ProductHSCode(
                product_id=product.id,
                hs_code_id=hs_code.id,
                mapping_type="candidate",
                confidence=0.95,
                source="Development seed data",
            )
        )

    db.flush()


def seed():
    db = SessionLocal()

    try:
        seed_countries(db)

        hs_version = seed_hs_version(db)
        hs_codes = seed_hs_codes(db, hs_version)

        seed_products(db, hs_codes)

        db.commit()

        print("Seed completed successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()