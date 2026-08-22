"""Correct HS hierarchy to WCO structure
Revision ID: b61f7a7282d3
Revises: f4af954581bd
Create Date: 2026-08-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b61f7a7282d3"
down_revision: Union[str, Sequence[str], None] = "f4af954581bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing development hierarchy:
    #
    # 85
    # └── 853
    #     └── 8537
    #         └── 853710
    #
    # Correct WCO hierarchy:
    #
    # 85
    # └── 8537
    #     ├── 85371
    #     │   └── 853710
    #     └── 85372
    #         └── 853720

    # Re-purpose existing row 2 instead of deleting it.
    # This preserves the existing product_hs_codes reference
    # to 853710 (row 4).
    op.execute(
        """
        UPDATE hs_codes
        SET
            code = '85371',
            description = 'For a voltage not exceeding 1,000 V',
            level = 5,
            parent_id = 3,
            updated_at = now()
        WHERE id = 2
        """
    )

    # Make 8537 a direct child of Chapter 85.
    op.execute(
        """
        UPDATE hs_codes
        SET
            parent_id = 1,
            updated_at = now()
        WHERE id = 3
        """
    )

    # 853710 becomes child of the 5-digit 85371 node.
    op.execute(
        """
        UPDATE hs_codes
        SET
            parent_id = 2,
            updated_at = now()
        WHERE id = 4
        """
    )

    # Add the second 5-digit subheading.
    op.execute(
        """
        INSERT INTO hs_codes (
            hs_version_id,
            code,
            description,
            level,
            parent_id,
            active
        )
        VALUES (
            1,
            '85372',
            'For a voltage exceeding 1,000 V',
            5,
            3,
            TRUE
        )
        """
    )

    # Add its 6-digit child.
    op.execute(
        """
        INSERT INTO hs_codes (
            hs_version_id,
            code,
            description,
            level,
            parent_id,
            active
        )
        VALUES (
            1,
            '853720',
            'For a voltage exceeding 1,000 V',
            6,
            (
                SELECT id
                FROM hs_codes
                WHERE hs_version_id = 1
                  AND code = '85372'
            ),
            TRUE
        )
        """
    )


def downgrade() -> None:
    # Remove the newly introduced WCO branch.
    op.execute(
        """
        DELETE FROM hs_codes
        WHERE code IN ('853720', '85372')
          AND hs_version_id = 1
        """
    )

    # Restore 853710's original parent.
    op.execute(
        """
        UPDATE hs_codes
        SET
            parent_id = 3,
            updated_at = now()
        WHERE id = 4
        """
    )

    # Restore 8537's original parent.
    op.execute(
        """
        UPDATE hs_codes
        SET
            parent_id = 2,
            updated_at = now()
        WHERE id = 3
        """
    )

    # Restore the original development row.
    op.execute(
        """
        UPDATE hs_codes
        SET
            code = '853',
            description = 'Electrical apparatus for switching or protecting electrical circuits',
            level = 3,
            parent_id = 1,
            updated_at = now()
        WHERE id = 2
        """
    )
