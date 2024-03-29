"""todos table

Revision ID: c60c1b91e743
Revises: 61d0a8548cec
Create Date: 2024-02-04 11:01:25.320368

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c60c1b91e743'
down_revision = '61d0a8548cec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('to_do',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.String(length=140), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('recurrence', sa.Boolean(), nullable=False),
    sa.Column('recurrence_rythm', sa.Integer(), nullable=False),
    sa.Column('completed', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('to_do', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_to_do_timestamp'), ['timestamp'], unique=False)
        batch_op.create_index(batch_op.f('ix_to_do_user_id'), ['user_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('to_do', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_to_do_user_id'))
        batch_op.drop_index(batch_op.f('ix_to_do_timestamp'))

    op.drop_table('to_do')
    # ### end Alembic commands ###
