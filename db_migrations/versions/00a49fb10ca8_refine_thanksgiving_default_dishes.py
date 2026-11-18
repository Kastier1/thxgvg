"""refine_thanksgiving_default_dishes

Revision ID: 00a49fb10ca8
Revises: c0bc917814d6
"""
from typing import Sequence, Union

from alembic import op

revision: str = '00a49fb10ca8'
down_revision: Union[str, Sequence[str], None] = 'c0bc917814d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("SELECT id FROM recommended_item WHERE normalized_name IN ('roasted vegetables', 'bread & rolls', 'drinks') ORDER BY id FOR UPDATE;\n\nUPDATE recommended_item AS item\nSET name = changes.new_name, normalized_name = lower(changes.new_name)\nFROM (VALUES\n    ('roasted vegetables', 'Roasted Brussels sprouts'),\n    ('bread & rolls', 'Dinner rolls & butter'),\n    ('drinks', 'Sparkling water & apple cider')\n) AS changes(old_name, new_name)\nWHERE item.normalized_name = changes.old_name\n  AND item.active = TRUE\n  AND NOT EXISTS (SELECT 1 FROM rsvp WHERE rsvp.recommended_item_id = item.id)\n  AND NOT EXISTS (SELECT 1 FROM recommended_item AS other WHERE other.normalized_name = lower(changes.new_name) AND other.id <> item.id);\n\nINSERT INTO recommended_item (name, normalized_name, active)\nVALUES ('Turkey gravy', 'turkey gravy', TRUE), ('Green beans', 'green beans', TRUE)\nON CONFLICT (normalized_name) DO NOTHING;")


def downgrade() -> None:
    pass
