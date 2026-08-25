from datetime import date

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import (
    Country,
    DataSource,
    HSCode,
    HSVersion,
    Product,
    ProductAlias,
    ProductHSCode,
    TradeData,
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
        existing = db.scalar(select(Country).where(Country.iso3 == data["iso3"]))

        if existing is None:
            db.add(Country(**data))

    db.flush()

    return {
        country.iso3: country
        for country in db.scalars(
            select(Country).where(
                Country.iso3.in_([data["iso3"] for data in countries])
            )
        ).all()
    }


def seed_hs_version(db):
    version = db.scalar(select(HSVersion).where(HSVersion.version == "2022"))

    if version is None:
        version = HSVersion(
            name="Harmonized System",
            version="2022",
            source="Development seed data",
        )

        db.add(version)
        db.flush()

    return version


def seed_data_source(db):
    source = db.scalar(
        select(DataSource).where(DataSource.name == "Development Trade Data")
    )

    if source is None:
        source = DataSource(
            name="Development Trade Data",
            provider="Project Trade Opportunity",
            source_type="synthetic",
            update_frequency="development",
            license_notes=(
                "Synthetic data for development and " "integration testing only."
            ),
        )

        db.add(source)
        db.flush()

    return source


def seed_hs_codes(db, hs_version):
    """
    Seed the initial HS 2022 hierarchy required by the
    electrical-equipment product catalog.

    Product-to-HS mappings are maintained separately
    in seed_products().

    Existing trade data continues to use HS 853710.
    """

    codes = [
        # ==================================================
        # Chapter 85
        # ==================================================
        {
            "code": "85",
            "description": ("Electrical machinery and equipment and parts thereof"),
            "level": 2,
            "parent_code": None,
        },
        # ==================================================
        # 85.04 - Transformers / static converters / inductors
        # ==================================================
        {
            "code": "8504",
            "description": (
                "Electrical transformers, static converters "
                "(for example, rectifiers) and inductors."
            ),
            "level": 4,
            "parent_code": "85",
        },
        {
            "code": "85041",
            "description": "Liquid dielectric transformers.",
            "level": 5,
            "parent_code": "8504",
        },
        {
            "code": "85042",
            "description": "Other liquid dielectric transformers.",
            "level": 5,
            "parent_code": "8504",
        },
        {
            "code": "85043",
            "description": "Other transformers.",
            "level": 5,
            "parent_code": "8504",
        },
        {
            "code": "85044",
            "description": "Static converters.",
            "level": 5,
            "parent_code": "8504",
        },
        {
            "code": "85045",
            "description": "Other inductors.",
            "level": 5,
            "parent_code": "8504",
        },
        {
            "code": "85049",
            "description": "Parts.",
            "level": 5,
            "parent_code": "8504",
        },
        {
            "code": "850410",
            "description": "Ballasts for discharge lamps or tubes.",
            "level": 6,
            "parent_code": "8504",
        },
        {
            "code": "850421",
            "description": (
                "Liquid dielectric transformers having a power "
                "handling capacity not exceeding 650 kVA."
            ),
            "level": 6,
            "parent_code": "8504",
        },
        {
            "code": "850422",
            "description": (
                "Liquid dielectric transformers having a power "
                "handling capacity exceeding 650 kVA but not "
                "exceeding 10,000 kVA."
            ),
            "level": 6,
            "parent_code": "8504",
        },
        {
            "code": "850423",
            "description": (
                "Liquid dielectric transformers having a power "
                "handling capacity exceeding 10,000 kVA."
            ),
            "level": 6,
            "parent_code": "8504",
        },
        {
            "code": "850431",
            "description": (
                "Other transformers having a power handling "
                "capacity not exceeding 1 kVA."
            ),
            "level": 6,
            "parent_code": "8504",
        },
        {
            "code": "850432",
            "description": (
                "Other transformers having a power handling "
                "capacity exceeding 1 kVA but not exceeding 16 kVA."
            ),
            "level": 6,
            "parent_code": "8504",
        },
        {
            "code": "850433",
            "description": (
                "Other transformers having a power handling "
                "capacity exceeding 16 kVA but not exceeding 500 kVA."
            ),
            "level": 6,
            "parent_code": "8504",
        },
        {
            "code": "850434",
            "description": (
                "Other transformers having a power handling "
                "capacity exceeding 500 kVA."
            ),
            "level": 6,
            "parent_code": "8504",
        },
        {
            "code": "850440",
            "description": "Static converters.",
            "level": 6,
            "parent_code": "8504",
        },
        {
            "code": "850450",
            "description": "Other inductors.",
            "level": 6,
            "parent_code": "8504",
        },
        {
            "code": "850490",
            "description": "Parts.",
            "level": 6,
            "parent_code": "8504",
        },
        # ==================================================
        # 85.35 - HV switching / protecting equipment
        # ==================================================
        {
            "code": "8535",
            "description": (
                "Electrical apparatus for switching or protecting "
                "electrical circuits, or for making connections to "
                "or in electrical circuits, for a voltage exceeding "
                "1,000 volts."
            ),
            "level": 4,
            "parent_code": "85",
        },
        {
            "code": "85351",
            "description": "Fuses.",
            "level": 5,
            "parent_code": "8535",
        },
        {
            "code": "85352",
            "description": "Automatic circuit breakers.",
            "level": 5,
            "parent_code": "8535",
        },
        {
            "code": "85353",
            "description": ("Isolating switches and make-and-break switches."),
            "level": 5,
            "parent_code": "8535",
        },
        {
            "code": "85354",
            "description": (
                "Lightning arresters, voltage limiters and " "surge suppressors."
            ),
            "level": 5,
            "parent_code": "8535",
        },
        {
            "code": "85359",
            "description": "Other apparatus.",
            "level": 5,
            "parent_code": "8535",
        },
        {
            "code": "853510",
            "description": "Fuses.",
            "level": 6,
            "parent_code": "8535",
        },
        {
            "code": "853521",
            "description": (
                "Automatic circuit breakers for a voltage " "of less than 72.5 kV."
            ),
            "level": 6,
            "parent_code": "8535",
        },
        {
            "code": "853529",
            "description": "Other automatic circuit breakers.",
            "level": 6,
            "parent_code": "8535",
        },
        {
            "code": "853530",
            "description": ("Isolating switches and make-and-break switches."),
            "level": 6,
            "parent_code": "8535",
        },
        {
            "code": "853540",
            "description": (
                "Lightning arresters, voltage limiters and " "surge suppressors."
            ),
            "level": 6,
            "parent_code": "8535",
        },
        {
            "code": "853590",
            "description": "Other apparatus.",
            "level": 6,
            "parent_code": "8535",
        },
        # ==================================================
        # 85.36 - LV switching / protecting equipment
        # ==================================================
        {
            "code": "8536",
            "description": (
                "Electrical apparatus for switching or protecting "
                "electrical circuits, or for making connections to "
                "or in electrical circuits, for a voltage not exceeding "
                "1,000 volts."
            ),
            "level": 4,
            "parent_code": "85",
        },
        {
            "code": "85361",
            "description": "Fuses.",
            "level": 5,
            "parent_code": "8536",
        },
        {
            "code": "85362",
            "description": "Automatic circuit breakers.",
            "level": 5,
            "parent_code": "8536",
        },
        {
            "code": "85363",
            "description": ("Other apparatus for protecting electrical circuits."),
            "level": 5,
            "parent_code": "8536",
        },
        {
            "code": "85364",
            "description": "Relays.",
            "level": 5,
            "parent_code": "8536",
        },
        {
            "code": "85365",
            "description": "Other switches.",
            "level": 5,
            "parent_code": "8536",
        },
        {
            "code": "85366",
            "description": "Lamp-holders, plugs and sockets.",
            "level": 5,
            "parent_code": "8536",
        },
        {
            "code": "85367",
            "description": (
                "Connectors for optical fibres, optical fibre " "bundles or cables."
            ),
            "level": 5,
            "parent_code": "8536",
        },
        {
            "code": "85369",
            "description": "Other apparatus.",
            "level": 5,
            "parent_code": "8536",
        },
        {
            "code": "853610",
            "description": "Fuses.",
            "level": 6,
            "parent_code": "8536",
        },
        {
            "code": "853620",
            "description": "Automatic circuit breakers.",
            "level": 6,
            "parent_code": "8536",
        },
        {
            "code": "853630",
            "description": ("Other apparatus for protecting electrical circuits."),
            "level": 6,
            "parent_code": "8536",
        },
        {
            "code": "853641",
            "description": ("Relays for a voltage not exceeding 60 V."),
            "level": 6,
            "parent_code": "8536",
        },
        {
            "code": "853649",
            "description": "Other relays.",
            "level": 6,
            "parent_code": "8536",
        },
        {
            "code": "853650",
            "description": "Other switches.",
            "level": 6,
            "parent_code": "8536",
        },
        {
            "code": "853661",
            "description": "Lamp-holders.",
            "level": 6,
            "parent_code": "8536",
        },
        {
            "code": "853669",
            "description": "Other plugs and sockets.",
            "level": 6,
            "parent_code": "8536",
        },
        {
            "code": "853670",
            "description": (
                "Connectors for optical fibres, optical fibre " "bundles or cables."
            ),
            "level": 6,
            "parent_code": "8536",
        },
        {
            "code": "853690",
            "description": "Other apparatus.",
            "level": 6,
            "parent_code": "8536",
        },
        # ==================================================
        # 85.37 - Control / distribution panels
        # ==================================================
        {
            "code": "8537",
            "description": (
                "Boards, panels, consoles, desks, cabinets and "
                "other bases, equipped with two or more apparatus "
                "of heading 85.35 or 85.36, for electric control "
                "or the distribution of electricity."
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
            "code": "85372",
            "description": "For a voltage exceeding 1,000 V",
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
            code_objects[data["code"]] = HSCode(
                code=data["code"],
                description=data["description"],
                level=data["level"],
                hs_version_id=hs_version.id,
                active=True,
            )

            db.add(code_objects[data["code"]])

        else:
            existing.description = data["description"]
            existing.level = data["level"]
            existing.active = True

            code_objects[data["code"]] = existing

    db.flush()

    # --------------------------------------------------
    # Resolve parent relationships
    # --------------------------------------------------

    for data in codes:
        parent_code = data["parent_code"]

        if parent_code is None:
            continue

        current = code_objects[data["code"]]
        parent = code_objects.get(parent_code)

        if parent is None:
            raise ValueError(
                f"Parent HS code {parent_code} "
                f"required by {data['code']} "
                f"was not seeded."
            )

        current.parent_id = parent.id

    db.flush()

    return code_objects


def seed_products(db, hs_codes):
    """
    Seed the electrical-equipment product catalog.

    Product
        ↓
    ProductAlias
        ↓
    ProductHSCode
        ↓
    HSCode
    """

    products = [
        {
            "name": "Electrical Control Panels",
            "description": ("Electrical control and distribution panel assemblies."),
            "category": "Control & Protection",
            "aliases": [
                "electrical panels",
                "control panels",
                "electrical control panels",
                "distribution panels",
            ],
            "hs_mappings": [
                {
                    "code": "853710",
                    "mapping_type": "candidate",
                    "confidence": 0.95,
                },
            ],
        },
        {
            "name": "HV Power Transformers",
            "description": (
                "High-voltage power transformers used in electrical "
                "transmission and high-voltage power systems."
            ),
            "category": "Transformers",
            "aliases": [
                "HV transformers",
                "HV power transformers",
                "high voltage transformers",
                "high voltage power transformers",
                "power transformers",
            ],
            "hs_mappings": [],
        },
        {
            "name": "MV Power Transformers",
            "description": (
                "Medium-voltage power transformers used in electrical "
                "distribution and industrial power systems."
            ),
            "category": "Transformers",
            "aliases": [
                "MV transformers",
                "MV power transformers",
                "medium voltage transformers",
                "medium voltage power transformers",
            ],
            "hs_mappings": [],
        },
        {
            "name": "Distribution Transformers",
            "description": (
                "Transformers used for electrical power distribution "
                "between distribution networks and consumers."
            ),
            "category": "Transformers",
            "aliases": [
                "distribution transformers",
                "distribution transformer",
                "DT transformers",
            ],
            "hs_mappings": [],
        },
        {
            "name": "LV Switchgear",
            "description": (
                "Low-voltage switchgear and associated equipment "
                "for electrical control, isolation and distribution."
            ),
            "category": "Switchgear",
            "aliases": [
                "LV switchgear",
                "low voltage switchgear",
                "low-voltage switchgear",
            ],
            "hs_mappings": [],
        },
        {
            "name": "MV Switchgear",
            "description": (
                "Medium-voltage switchgear used for electrical "
                "distribution and industrial power systems."
            ),
            "category": "Switchgear",
            "aliases": [
                "MV switchgear",
                "medium voltage switchgear",
                "medium-voltage switchgear",
            ],
            "hs_mappings": [],
        },
        {
            "name": "HV Switchgear",
            "description": (
                "High-voltage switchgear used for transmission "
                "and high-voltage electrical systems."
            ),
            "category": "Switchgear",
            "aliases": [
                "HV switchgear",
                "high voltage switchgear",
                "high-voltage switchgear",
            ],
            "hs_mappings": [],
        },
        {
            "name": "Protection Panels",
            "description": (
                "Electrical protection panels containing protection "
                "and associated control equipment."
            ),
            "category": "Control & Protection",
            "aliases": [
                "protection panels",
                "electrical protection panels",
                "protection relay panels",
            ],
            "hs_mappings": [],
        },
        {
            "name": "Relay Panels",
            "description": (
                "Panels containing protection, monitoring and "
                "control relays for electrical systems."
            ),
            "category": "Control & Protection",
            "aliases": [
                "relay panels",
                "protection relay panels",
                "electrical relay panels",
            ],
            "hs_mappings": [],
        },
        {
            "name": "Bus Ducts",
            "description": (
                "Bus duct and busway systems used for electrical " "power distribution."
            ),
            "category": "Busbar / Distribution",
            "aliases": [
                "bus ducts",
                "bus duct",
                "busways",
                "busway systems",
            ],
            "hs_mappings": [],
        },
        {
            "name": "Busbar Systems",
            "description": (
                "Busbar systems used for electrical power "
                "distribution and connection."
            ),
            "category": "Busbar / Distribution",
            "aliases": [
                "busbar systems",
                "busbar system",
                "bus bars",
                "busbars",
            ],
            "hs_mappings": [],
        },
        {
            "name": "Electric Motors",
            "description": (
                "Electric motors used in industrial, commercial "
                "and electrical equipment applications."
            ),
            "category": "Other Electrical Equipment",
            "aliases": [
                "electric motors",
                "electrical motors",
                "AC motors",
                "DC motors",
            ],
            "hs_mappings": [],
        },
        {
            "name": "Generators",
            "description": (
                "Electrical generators and generating equipment "
                "used to produce electrical power."
            ),
            "category": "Other Electrical Equipment",
            "aliases": [
                "generators",
                "electric generators",
                "electrical generators",
                "generator sets",
                "gensets",
            ],
            "hs_mappings": [],
        },
        {
            "name": "UPS Systems",
            "description": (
                "Uninterruptible power supply systems used to "
                "provide conditioned and backup electrical power."
            ),
            "category": "Other Electrical Equipment",
            "aliases": [
                "UPS",
                "UPS systems",
                "uninterruptible power supplies",
                "uninterruptible power supply",
            ],
            "hs_mappings": [],
        },
        {
            "name": "Power Distribution Equipment",
            "description": (
                "Electrical equipment used for power distribution "
                "within electrical networks and facilities."
            ),
            "category": "Other Electrical Equipment",
            "aliases": [
                "power distribution equipment",
                "electrical distribution equipment",
                "power distribution systems",
            ],
            "hs_mappings": [],
        },
    ]

    for data in products:

        # --------------------------------------------------
        # Product
        # --------------------------------------------------

        product = db.scalar(select(Product).where(Product.name == data["name"]))

        if product is None:
            product = Product(
                name=data["name"],
                description=data["description"],
                category=data["category"],
                active=True,
            )

            db.add(product)
            db.flush()

        else:
            product.description = data["description"]
            product.category = data["category"]
            product.active = True

        # --------------------------------------------------
        # Product aliases
        # --------------------------------------------------

        for alias in data["aliases"]:

            existing_alias = db.scalar(
                select(ProductAlias).where(
                    ProductAlias.product_id == product.id,
                    ProductAlias.alias == alias,
                )
            )

            if existing_alias is None:
                db.add(
                    ProductAlias(
                        product_id=product.id,
                        alias=alias,
                        language="en",
                        source="Development seed data",
                        confidence=1.0,
                    )
                )

        # --------------------------------------------------
        # Product → HS mappings
        # --------------------------------------------------

        for mapping_data in data["hs_mappings"]:

            hs_code = hs_codes.get(mapping_data["code"])

            if hs_code is None:
                raise ValueError(
                    f"HS code {mapping_data['code']} "
                    f"required by product "
                    f"{data['name']} was not seeded."
                )

            existing_mapping = db.scalar(
                select(ProductHSCode).where(
                    ProductHSCode.product_id == product.id,
                    ProductHSCode.hs_code_id == hs_code.id,
                )
            )

            if existing_mapping is None:
                db.add(
                    ProductHSCode(
                        product_id=product.id,
                        hs_code_id=hs_code.id,
                        mapping_type=mapping_data["mapping_type"],
                        confidence=mapping_data["confidence"],
                        source="Development seed data",
                    )
                )

        db.flush()


def seed_trade_data(
    db,
    countries,
    hs_codes,
    source,
):
    india = countries["IND"]
    saudi_arabia = countries["SAU"]
    uae = countries["ARE"]
    germany = countries["DEU"]
    usa = countries["USA"]

    # Existing synthetic trade dataset remains mapped
    # to Electrical Control Panels / HS 853710.

    hs_853710 = hs_codes["853710"]

    records = [
        # ==================================================
        # India imports - 2024
        # ==================================================
        {
            "reporter_country_id": india.id,
            "partner_country_id": germany.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2024, 1, 1),
            "period_end": date(2024, 12, 31),
            "period_type": "annual",
            "trade_flow": "import",
            "trade_value_usd": 9_000_000,
            "quantity": 900,
            "quantity_unit": "units",
        },
        {
            "reporter_country_id": india.id,
            "partner_country_id": usa.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2024, 1, 1),
            "period_end": date(2024, 12, 31),
            "period_type": "annual",
            "trade_flow": "import",
            "trade_value_usd": 7_000_000,
            "quantity": 700,
            "quantity_unit": "units",
        },
        {
            "reporter_country_id": india.id,
            "partner_country_id": uae.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2024, 1, 1),
            "period_end": date(2024, 12, 31),
            "period_type": "annual",
            "trade_flow": "import",
            "trade_value_usd": 3_500_000,
            "quantity": 350,
            "quantity_unit": "units",
        },
        {
            "reporter_country_id": india.id,
            "partner_country_id": saudi_arabia.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2024, 1, 1),
            "period_end": date(2024, 12, 31),
            "period_type": "annual",
            "trade_flow": "import",
            "trade_value_usd": 1_800_000,
            "quantity": 180,
            "quantity_unit": "units",
        },
        # ==================================================
        # India imports - 2025
        # ==================================================
        {
            "reporter_country_id": india.id,
            "partner_country_id": germany.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2025, 1, 1),
            "period_end": date(2025, 12, 31),
            "period_type": "annual",
            "trade_flow": "import",
            "trade_value_usd": 10_500_000,
            "quantity": 1000,
            "quantity_unit": "units",
        },
        {
            "reporter_country_id": india.id,
            "partner_country_id": usa.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2025, 1, 1),
            "period_end": date(2025, 12, 31),
            "period_type": "annual",
            "trade_flow": "import",
            "trade_value_usd": 8_200_000,
            "quantity": 800,
            "quantity_unit": "units",
        },
        {
            "reporter_country_id": india.id,
            "partner_country_id": uae.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2025, 1, 1),
            "period_end": date(2025, 12, 31),
            "period_type": "annual",
            "trade_flow": "import",
            "trade_value_usd": 4_600_000,
            "quantity": 450,
            "quantity_unit": "units",
        },
        {
            "reporter_country_id": india.id,
            "partner_country_id": saudi_arabia.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2025, 1, 1),
            "period_end": date(2025, 12, 31),
            "period_type": "annual",
            "trade_flow": "import",
            "trade_value_usd": 2_300_000,
            "quantity": 220,
            "quantity_unit": "units",
        },
        # ==================================================
        # Global exports - 2025
        # ==================================================
        {
            "reporter_country_id": germany.id,
            "partner_country_id": usa.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2025, 1, 1),
            "period_end": date(2025, 12, 31),
            "period_type": "annual",
            "trade_flow": "export",
            "trade_value_usd": 25_000_000,
            "quantity": 2400,
            "quantity_unit": "units",
        },
        {
            "reporter_country_id": usa.id,
            "partner_country_id": germany.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2025, 1, 1),
            "period_end": date(2025, 12, 31),
            "period_type": "annual",
            "trade_flow": "export",
            "trade_value_usd": 20_000_000,
            "quantity": 1900,
            "quantity_unit": "units",
        },
        {
            "reporter_country_id": uae.id,
            "partner_country_id": india.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2025, 1, 1),
            "period_end": date(2025, 12, 31),
            "period_type": "annual",
            "trade_flow": "export",
            "trade_value_usd": 12_000_000,
            "quantity": 1100,
            "quantity_unit": "units",
        },
        {
            "reporter_country_id": saudi_arabia.id,
            "partner_country_id": india.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2025, 1, 1),
            "period_end": date(2025, 12, 31),
            "period_type": "annual",
            "trade_flow": "export",
            "trade_value_usd": 7_000_000,
            "quantity": 650,
            "quantity_unit": "units",
        },
        # ==================================================
        # India exports - 2025
        # ==================================================
        {
            "reporter_country_id": india.id,
            "partner_country_id": germany.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2025, 1, 1),
            "period_end": date(2025, 12, 31),
            "period_type": "annual",
            "trade_flow": "export",
            "trade_value_usd": 14_000_000,
            "quantity": 1300,
            "quantity_unit": "units",
        },
        {
            "reporter_country_id": india.id,
            "partner_country_id": usa.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2025, 1, 1),
            "period_end": date(2025, 12, 31),
            "period_type": "annual",
            "trade_flow": "export",
            "trade_value_usd": 11_000_000,
            "quantity": 1000,
            "quantity_unit": "units",
        },
        {
            "reporter_country_id": india.id,
            "partner_country_id": uae.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2025, 1, 1),
            "period_end": date(2025, 12, 31),
            "period_type": "annual",
            "trade_flow": "export",
            "trade_value_usd": 6_000_000,
            "quantity": 550,
            "quantity_unit": "units",
        },
        {
            "reporter_country_id": india.id,
            "partner_country_id": saudi_arabia.id,
            "hs_code_id": hs_853710.id,
            "period_start": date(2025, 1, 1),
            "period_end": date(2025, 12, 31),
            "period_type": "annual",
            "trade_flow": "export",
            "trade_value_usd": 4_000_000,
            "quantity": 380,
            "quantity_unit": "units",
        },
    ]

    for data in records:

        existing = db.scalar(
            select(TradeData).where(
                TradeData.reporter_country_id == data["reporter_country_id"],
                TradeData.partner_country_id == data["partner_country_id"],
                TradeData.hs_code_id == data["hs_code_id"],
                TradeData.period_start == data["period_start"],
                TradeData.trade_flow == data["trade_flow"],
                TradeData.source_id == source.id,
            )
        )

        if existing is None:
            db.add(
                TradeData(
                    **data,
                    source_id=source.id,
                    source_record_id=(
                        f"DEV-{data['trade_flow']}-"
                        f"{data['reporter_country_id']}-"
                        f"{data['partner_country_id']}-"
                        f"{data['period_start'].year}"
                    ),
                    data_version="dev-1",
                )
            )

    db.flush()


def seed():
    db = SessionLocal()

    try:

        # --------------------------------------------------
        # 1. Countries
        # --------------------------------------------------

        countries = seed_countries(db)

        # --------------------------------------------------
        # 2. HS version
        # --------------------------------------------------

        hs_version = seed_hs_version(db)

        # --------------------------------------------------
        # 3. HS codes
        # --------------------------------------------------

        hs_codes = seed_hs_codes(
            db,
            hs_version,
        )

        # --------------------------------------------------
        # 4. Products and HS mappings
        # --------------------------------------------------

        seed_products(
            db,
            hs_codes,
        )

        # --------------------------------------------------
        # 5. Trade data source
        # --------------------------------------------------

        source = seed_data_source(db)

        # --------------------------------------------------
        # 6. Trade data
        # --------------------------------------------------

        seed_trade_data(
            db,
            countries,
            hs_codes,
            source,
        )

        # --------------------------------------------------
        # Commit everything together
        # --------------------------------------------------

        db.commit()

        print("Seed completed successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()
