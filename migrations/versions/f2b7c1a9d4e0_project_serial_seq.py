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
