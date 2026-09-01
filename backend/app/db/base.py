from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


TRADE_OPPORTUNITY_SCHEMA = "trade_opportunity"


class Base(DeclarativeBase):
    metadata = MetaData(schema=TRADE_OPPORTUNITY_SCHEMA)
