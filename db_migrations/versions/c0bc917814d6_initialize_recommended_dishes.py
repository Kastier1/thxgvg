"""initialize_recommended_dishes

Revision ID: c0bc917814d6
Revises: b225c1ae3f3b
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'c0bc917814d6'
down_revision: Union[str, Sequence[str], None] = 'b225c1ae3f3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("INSERT INTO recommended_item (name, normalized_name, active) VALUES ('Mashed potatoes','mashed potatoes',true),('Stuffing','stuffing',true),('Cranberry sauce','cranberry sauce',true),('Roasted vegetables','roasted vegetables',true),('Pumpkin pie','pumpkin pie',true),('Apple pie','apple pie',true),('Drinks','drinks',true),('Bread & rolls','bread & rolls',true) ON CONFLICT (normalized_name) DO NOTHING;")


def downgrade() -> None:
    pass
