"""empty message

Revision ID: f208ebcca81a
Revises: 1cee1127ae59
Create Date: 2024-08-12 15:05:01.997864

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f208ebcca81a'
down_revision = '1cee1127ae59'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ad_request', schema=None) as batch_op:
        batch_op.alter_column('status',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=15),
               existing_nullable=True)

    with op.batch_alter_table('campaign', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_flagged', sa.Boolean(), nullable=True))

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_flagged', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('is_flagged')

    with op.batch_alter_table('campaign', schema=None) as batch_op:
        batch_op.drop_column('is_flagged')

    with op.batch_alter_table('ad_request', schema=None) as batch_op:
        batch_op.alter_column('status',
               existing_type=sa.String(length=15),
               type_=sa.VARCHAR(length=50),
               existing_nullable=True)

    # ### end Alembic commands ###
