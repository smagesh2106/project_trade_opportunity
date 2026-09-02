"""Add UN Comtrade code to countries

Revision ID: 4c1d8e72b5a9
Revises: 0e3cc6443aec
Create Date: 2026-09-02 12:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4c1d8e72b5a9"
down_revision: Union[str, Sequence[str], None] = "0e3cc6443aec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable UN Comtrade M49 code to the country master."""
    op.add_column(
        "countries",
        sa.Column(
            "comtrade_code",
            sa.Integer(),
            nullable=True,
        ),
        schema="trade_opportunity",
    )

    op.create_unique_constraint(
        "uq_countries_comtrade_code",
        "countries",
        ["comtrade_code"],
        schema="trade_opportunity",
    )


def downgrade() -> None:
    """Remove the UN Comtrade M49 code from the country master."""
    op.drop_constraint(
        "uq_countries_comtrade_code",
        "countries",
        schema="trade_opportunity",
        type_="unique",
    )

    op.drop_column(
        "countries",
        "comtrade_code",
        schema="trade_opportunity",
    )
