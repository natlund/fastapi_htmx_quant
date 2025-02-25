"""Create Tables

Revision ID: 4b1aece263e2
Revises: 
Create Date: 2025-02-25 21:41:22.963828

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '4b1aece263e2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('bull',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bull_code', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('bull_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('bull', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_bull_bull_code'), ['bull_code'], unique=False)

    op.create_table('farm',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('business_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('postcode', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('coordinates', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('address', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('contact_person', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('farm', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_farm_name'), ['name'], unique=False)

    op.create_table('technician',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('phone', sa.Integer(), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('postcode', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('address', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('technician', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_technician_name'), ['name'], unique=False)

    op.create_table('cow',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('farm_id', sa.Integer(), nullable=False),
    sa.Column('tag_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['farm_id'], ['farm.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('cow', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_cow_tag_id'), ['tag_id'], unique=False)

    op.create_table('job',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job_date', sa.Date(), nullable=False),
    sa.Column('farm_id', sa.Integer(), nullable=False),
    sa.Column('lead_technician_id', sa.Integer(), nullable=False),
    sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['farm_id'], ['farm.id'], ),
    sa.ForeignKeyConstraint(['lead_technician_id'], ['technician.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('insemination',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job_id', sa.Integer(), nullable=False),
    sa.Column('technician_id', sa.Integer(), nullable=False),
    sa.Column('bull_id', sa.Integer(), nullable=False),
    sa.Column('cow_id', sa.Integer(), nullable=False),
    sa.Column('days_since_last_insemination', sa.Integer(), nullable=True),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['bull_id'], ['bull.id'], ),
    sa.ForeignKeyConstraint(['cow_id'], ['cow.id'], ),
    sa.ForeignKeyConstraint(['job_id'], ['job.id'], ),
    sa.ForeignKeyConstraint(['technician_id'], ['technician.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('plannedinsemination',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job_id', sa.Integer(), nullable=False),
    sa.Column('technician_id', sa.Integer(), nullable=False),
    sa.Column('bull_id', sa.Integer(), nullable=False),
    sa.Column('cow_id', sa.Integer(), nullable=False),
    sa.Column('days_since_last_insemination', sa.Integer(), nullable=True),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['bull_id'], ['bull.id'], ),
    sa.ForeignKeyConstraint(['cow_id'], ['cow.id'], ),
    sa.ForeignKeyConstraint(['job_id'], ['job.id'], ),
    sa.ForeignKeyConstraint(['technician_id'], ['technician.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('plannedinsemination')
    op.drop_table('insemination')
    op.drop_table('job')
    with op.batch_alter_table('cow', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_cow_tag_id'))

    op.drop_table('cow')
    with op.batch_alter_table('technician', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_technician_name'))

    op.drop_table('technician')
    with op.batch_alter_table('farm', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_farm_name'))

    op.drop_table('farm')
    with op.batch_alter_table('bull', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_bull_bull_code'))

    op.drop_table('bull')
    # ### end Alembic commands ###
