"""Initial migration

Revision ID: 0001
Revises: 
Create Date: 2023-07-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create orgs table
    op.create_table(
        'orgs',
        sa.Column('id', UUID(), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'))
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('line_user_id', sa.String(64), nullable=False, unique=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'))
    )
    
    # Create designs table
    op.create_table(
        'designs',
        sa.Column('id', UUID(), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('org_id', UUID(), sa.ForeignKey('orgs.id', ondelete='CASCADE')),
        sa.Column('template_json', JSONB(), nullable=False),
        sa.Column('preview_url', sa.Text()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'))
    )
    
    # Create passes table
    op.create_table(
        'passes',
        sa.Column('id', UUID(), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('design_id', UUID(), sa.ForeignKey('designs.id', ondelete='SET NULL')),
        sa.Column('platform', sa.String(10)),
        sa.Column('serial', sa.String(32), nullable=False, unique=True),
        sa.Column('deep_link', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('issued_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_updated', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'))
    )
    
    # Add platform check constraint
    op.create_check_constraint(
        'platform_type_check',
        'passes',
        sa.text("platform IN ('apple', 'google')")
    )


def downgrade() -> None:
    op.drop_table('passes')
    op.drop_table('designs')
    op.drop_table('users')
    op.drop_table('orgs') 