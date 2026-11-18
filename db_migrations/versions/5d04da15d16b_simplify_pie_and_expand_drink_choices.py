"""simplify_pie_and_expand_drink_choices

Revision ID: 5d04da15d16b
Revises: 00a49fb10ca8
"""
from typing import Sequence, Union

from alembic import op

revision: str = '5d04da15d16b'
down_revision: Union[str, Sequence[str], None] = '00a49fb10ca8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("SELECT id FROM recommended_item WHERE normalized_name IN ('roasted brussels sprouts', 'sparkling water & apple cider', 'pumpkin pie', 'apple pie', 'pie') ORDER BY id FOR UPDATE;\n\nUPDATE recommended_item AS item\nSET name = changes.new_name, normalized_name = lower(changes.new_name)\nFROM (VALUES\n    ('roasted brussels sprouts', 'Veggies'),\n    ('sparkling water & apple cider', 'Non-alcoholic drinks'),\n    ('pumpkin pie', 'Pie')\n) AS changes(old_name, new_name)\nWHERE item.normalized_name = changes.old_name\n  AND item.active = TRUE\n  AND NOT EXISTS (SELECT 1 FROM rsvp WHERE rsvp.recommended_item_id = item.id)\n  AND NOT EXISTS (SELECT 1 FROM recommended_item AS other WHERE other.normalized_name = lower(changes.new_name) AND other.id <> item.id)\n  AND (changes.old_name <> 'pumpkin pie' OR NOT EXISTS (\n      SELECT 1 FROM recommended_item AS other JOIN rsvp ON rsvp.recommended_item_id = other.id WHERE other.normalized_name = 'apple pie'\n  ));\n\nDELETE FROM recommended_item AS item\nWHERE item.normalized_name = 'apple pie'\n  AND item.active = TRUE\n  AND NOT EXISTS (SELECT 1 FROM rsvp WHERE rsvp.recommended_item_id = item.id)\n  AND EXISTS (\n      SELECT 1 FROM recommended_item AS other\n      WHERE other.normalized_name = 'pie'\n         OR (other.normalized_name = 'pumpkin pie' AND EXISTS (SELECT 1 FROM rsvp WHERE rsvp.recommended_item_id = other.id))\n  );\n\nDELETE FROM recommended_item AS item\nWHERE item.normalized_name = 'pumpkin pie'\n  AND item.active = TRUE\n  AND NOT EXISTS (SELECT 1 FROM rsvp WHERE rsvp.recommended_item_id = item.id)\n  AND EXISTS (\n      SELECT 1 FROM recommended_item AS other\n      WHERE other.normalized_name = 'pie'\n         OR (other.normalized_name = 'apple pie' AND EXISTS (SELECT 1 FROM rsvp WHERE rsvp.recommended_item_id = other.id))\n  );\n\nINSERT INTO recommended_item (name, normalized_name, active)\nVALUES ('Beer', 'beer', TRUE), ('Spirits', 'spirits', TRUE)\nON CONFLICT (normalized_name) DO NOTHING;")


def downgrade() -> None:
    pass
