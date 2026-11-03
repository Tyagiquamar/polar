"""index checkout_link_products product_id

Revision ID: 7c1e4b9a2d63
Revises: 2419b9b53df9
Create Date: 2026-11-03 14:00:00.000000

"""

from alembic import op

# Polar Custom Imports

# revision identifiers, used by Alembic.
revision = "7c1e4b9a2d63"
down_revision = "2419b9b53df9"
branch_labels: tuple[str] | None = None
depends_on: tuple[str] | None = None

INDEX = "ix_checkout_link_products_product_id"


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(
            INDEX,
            table_name="checkout_link_products",
            if_exists=True,
            postgresql_concurrently=True,
        )
        op.create_index(
            INDEX,
            "checkout_link_products",
            ["product_id"],
            unique=False,
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(
            INDEX,
            table_name="checkout_link_products",
            if_exists=True,
            postgresql_concurrently=True,
        )
