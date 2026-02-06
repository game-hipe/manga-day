"""add unique for GeneratedPdf

Revision ID: dbfd138731a1
Revises: 9600b2f75493
Create Date: 2026-02-06 13:42:14.268857

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dbfd138731a1'
down_revision: Union[str, Sequence[str], None] = '9600b2f75493'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Используем batch mode для SQLite
    with op.batch_alter_table('generated_pdf') as batch_op:
        batch_op.create_unique_constraint('uq_generated_pdf_id_manga', ['id_manga'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('generated_pdf') as batch_op:
        batch_op.drop_constraint('uq_generated_pdf_id_manga', type_='unique')