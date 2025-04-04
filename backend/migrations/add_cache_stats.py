"""
Migration script to add cache statistics columns to the settings table.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_cache_stats'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Add cache statistics columns"""
    op.add_column('settings', sa.Column('cache_size_mb', sa.Float, nullable=True, server_default='0'))
    op.add_column('settings', sa.Column('cache_file_count', sa.Integer, nullable=True, server_default='0'))

    # Set default values for existing rows
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE settings SET cache_size_mb = 0, cache_file_count = 0 WHERE cache_size_mb IS NULL"
        )
    )

    # Make columns non-nullable after setting defaults
    op.alter_column('settings', 'cache_size_mb', nullable=False)
    op.alter_column('settings', 'cache_file_count', nullable=False)

def downgrade():
    """Remove cache statistics columns"""
    op.drop_column('settings', 'cache_size_mb')
    op.drop_column('settings', 'cache_file_count')
