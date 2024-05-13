"""setup models

Revision ID: 9f36e0ac7da2
Revises: 
Create Date: 2024-05-13 18:26:20.565803

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f36e0ac7da2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=256), nullable=True),
    sa.Column('about_me', sa.String(length=140), nullable=True),
    sa.Column('last_seen', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_last_seen'), ['last_seen'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=True)

    op.create_table('category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=20), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('height', sa.Integer(), nullable=False),
    sa.Column('depth', sa.Integer(), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['category.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('followers',
    sa.Column('follower_id', sa.Integer(), nullable=False),
    sa.Column('followed_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['followed_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('follower_id', 'followed_id')
    )
    op.create_table('gid_gud',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.String(length=140), nullable=False),
    sa.Column('timestamp', sa.String(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('recurrence_rhythm', sa.Integer(), nullable=False),
    sa.Column('time_unit', sa.Enum('minutes', 'hours', 'days', 'weeks', 'months'), nullable=True),
    sa.Column('next_occurrence', sa.String(), nullable=True),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('unit', sa.String(length=10), nullable=True),
    sa.Column('times', sa.Integer(), nullable=False),
    sa.Column('completed', sa.String(), nullable=True),
    sa.Column('archived', sa.Boolean(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['category.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('gid_gud', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_gid_gud_completed'), ['completed'], unique=False)
        batch_op.create_index(batch_op.f('ix_gid_gud_next_occurrence'), ['next_occurrence'], unique=False)
        batch_op.create_index(batch_op.f('ix_gid_gud_timestamp'), ['timestamp'], unique=False)
        batch_op.create_index(batch_op.f('ix_gid_gud_user_id'), ['user_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('gid_gud', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_gid_gud_user_id'))
        batch_op.drop_index(batch_op.f('ix_gid_gud_timestamp'))
        batch_op.drop_index(batch_op.f('ix_gid_gud_next_occurrence'))
        batch_op.drop_index(batch_op.f('ix_gid_gud_completed'))

    op.drop_table('gid_gud')
    op.drop_table('followers')
    op.drop_table('category')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_username'))
        batch_op.drop_index(batch_op.f('ix_user_last_seen'))
        batch_op.drop_index(batch_op.f('ix_user_email'))

    op.drop_table('user')
    # ### end Alembic commands ###
