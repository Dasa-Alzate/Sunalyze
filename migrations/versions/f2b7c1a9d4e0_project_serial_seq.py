"""project serial_seq: correlativo de serie por organizacion

Anade `serial_seq` (Integer nullable) a `projects` y backfilla los proyectos existentes
numerandolos 1..N dentro de cada org en orden de `created_at` (incluye los borrados
logicamente, para que los numeros no se reutilicen). El prefijo se aplica al vuelo desde el
branding de la org; aqui solo se asigna el correlativo. Batch-safe.

Revision ID: f2b7c1a9d4e0
Revises: e7f8a9b0c1d2
Create Date: 2026-07-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'f2b7c1a9d4e0'
down_revision = 'e7f8a9b0c1d2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('serial_seq', sa.Integer(), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(
        sa.text('SELECT id, org_id FROM projects ORDER BY org_id, created_at, id')
    ).fetchall()
    counters = {}
    for row in rows:
        row_id, org_id = row[0], row[1]
        counters[org_id] = counters.get(org_id, 0) + 1
        conn.execute(
            sa.text('UPDATE projects SET serial_seq = :seq WHERE id = :id'),
            {'seq': counters[org_id], 'id': row_id},
        )


def downgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_column('serial_seq')
