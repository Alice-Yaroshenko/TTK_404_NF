"""Initial migration (with User._is_active property)

Revision ID: af47e7298ec5
Revises: 
Create Date: 2025-04-05 04:19:04.764321

"""
from alembic import op
import sqlalchemy as sa


revision = 'af47e7298ec5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('login', sa.String(length=64), nullable=False),
    sa.Column('full_name', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('registration_date', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_is_active'), ['is_active'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_login'), ['login'], unique=True)

    op.create_table('article',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('last_editor_id', sa.Integer(), nullable=False),
    sa.Column('image_filename', sa.String(length=128), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=True),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['last_editor_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('article', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_article_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_article_deleted_at'), ['deleted_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_article_is_deleted'), ['is_deleted'], unique=False)
        batch_op.create_index(batch_op.f('ix_article_title'), ['title'], unique=False)
        batch_op.create_index(batch_op.f('ix_article_updated_at'), ['updated_at'], unique=False)

    op.create_table('article_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('article_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('changes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['article_id'], ['article.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('article_history', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_article_history_article_id'), ['article_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_article_history_event_type'), ['event_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_article_history_timestamp'), ['timestamp'], unique=False)
        batch_op.create_index(batch_op.f('ix_article_history_user_id'), ['user_id'], unique=False)



def downgrade():
    with op.batch_alter_table('article_history', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_article_history_user_id'))
        batch_op.drop_index(batch_op.f('ix_article_history_timestamp'))
        batch_op.drop_index(batch_op.f('ix_article_history_event_type'))
        batch_op.drop_index(batch_op.f('ix_article_history_article_id'))

    op.drop_table('article_history')
    with op.batch_alter_table('article', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_article_updated_at'))
        batch_op.drop_index(batch_op.f('ix_article_title'))
        batch_op.drop_index(batch_op.f('ix_article_is_deleted'))
        batch_op.drop_index(batch_op.f('ix_article_deleted_at'))
        batch_op.drop_index(batch_op.f('ix_article_created_at'))

    op.drop_table('article')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_login'))
        batch_op.drop_index(batch_op.f('ix_user_is_active'))

    op.drop_table('user')
