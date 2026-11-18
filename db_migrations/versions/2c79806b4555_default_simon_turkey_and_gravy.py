"""default_simon_turkey_and_gravy

Revision ID: 2c79806b4555
Revises: 5d04da15d16b
"""
from typing import Sequence, Union

from alembic import op

revision: str = '2c79806b4555'
down_revision: Union[str, Sequence[str], None] = '5d04da15d16b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("SELECT id FROM recommended_item WHERE normalized_name IN ('turkey', 'turkey & gravy', 'turkey gravy') ORDER BY id FOR UPDATE;\nSELECT id FROM rsvp WHERE lower(trim(guest_name)) IN ('ingrid', 'simon') OR recommended_item_id IN (SELECT id FROM recommended_item WHERE normalized_name IN ('turkey', 'turkey & gravy', 'turkey gravy')) ORDER BY id FOR UPDATE;\n\nUPDATE recommended_item AS item\nSET name = 'Turkey & Gravy', normalized_name = 'turkey & gravy'\nWHERE item.normalized_name = 'turkey'\n  AND item.active = TRUE\n  AND NOT EXISTS (SELECT 1 FROM recommended_item AS other WHERE other.normalized_name = 'turkey & gravy')\n  AND NOT EXISTS (SELECT 1 FROM rsvp WHERE rsvp.recommended_item_id = item.id AND lower(trim(rsvp.guest_name)) NOT IN ('ingrid', 'simon'));\n\nINSERT INTO recommended_item (name, normalized_name, active)\nSELECT 'Turkey & Gravy', 'turkey & gravy', TRUE\nWHERE NOT EXISTS (SELECT 1 FROM recommended_item WHERE normalized_name = 'turkey')\nON CONFLICT (normalized_name) DO NOTHING;\n\nUPDATE rsvp AS guest\nSET guest_name = 'Simon', contribution = 'Turkey & Gravy'\nWHERE lower(trim(guest.guest_name)) = 'ingrid'\n  AND guest.recommended_item_id IN (SELECT id FROM recommended_item WHERE normalized_name = 'turkey & gravy')\n  AND NOT EXISTS (SELECT 1 FROM rsvp AS other WHERE lower(trim(other.guest_name)) = 'simon');\n\nINSERT INTO rsvp (guest_name, recommended_item_id, contribution)\nSELECT 'Simon', item.id, 'Turkey & Gravy'\nFROM recommended_item AS item\nWHERE item.normalized_name = 'turkey & gravy' AND item.active = TRUE\n  AND NOT EXISTS (SELECT 1 FROM rsvp WHERE lower(trim(guest_name)) = 'simon')\n  AND NOT EXISTS (SELECT 1 FROM rsvp WHERE recommended_item_id = item.id)\nON CONFLICT (recommended_item_id) DO NOTHING;\n\nUPDATE rsvp AS guest\nSET contribution = 'Turkey & Gravy'\nWHERE lower(trim(guest.guest_name)) = 'simon'\n  AND guest.recommended_item_id IN (SELECT id FROM recommended_item WHERE normalized_name = 'turkey & gravy');\n\nDELETE FROM recommended_item AS item\nWHERE item.normalized_name = 'turkey gravy' AND item.active = TRUE\n  AND NOT EXISTS (SELECT 1 FROM rsvp WHERE rsvp.recommended_item_id = item.id)\n  AND EXISTS (\n    SELECT 1 FROM rsvp JOIN recommended_item AS combined ON combined.id = rsvp.recommended_item_id\n    WHERE lower(trim(rsvp.guest_name)) = 'simon' AND combined.normalized_name = 'turkey & gravy'\n  );")


def downgrade() -> None:
    pass
