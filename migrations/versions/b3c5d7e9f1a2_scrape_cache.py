from alembic import op
import sqlalchemy as sa

revision = 'b3c5d7e9f1a2'
down_revision = 'a7b9c1d3e5f7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'scrape_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('url_hash', sa.String(length=64), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('etag', sa.String(length=200), nullable=True),
        sa.Column('last_modified', sa.String(length=120), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=True),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('scrape_cache', schema=None) as batch_op:
        batch_op.create_index('ix_scrape_cache_url_hash', ['url_hash'], unique=True)


def downgrade():
    with op.batch_alter_table('scrape_cache', schema=None) as batch_op:
        batch_op.drop_index('ix_scrape_cache_url_hash')
    op.drop_table('scrape_cache')
