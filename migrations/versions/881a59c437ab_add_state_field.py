"""add state field

Revision ID: 881a59c437ab
Revises: 486bfffc2655
Create Date: 2021-02-21 01:02:49.634884

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '881a59c437ab'
down_revision = '486bfffc2655'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('property', 'condition',
               existing_type=sa.VARCHAR(length=30),
               nullable=True)
    op.alter_column('property', 'type',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('property', 'type',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    op.alter_column('property', 'condition',
               existing_type=sa.VARCHAR(length=30),
               nullable=True)
    # ### end Alembic commands ###
