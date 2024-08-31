import sqlalchemy as sa
from sqlalchemy.types import Integer

meta = sa.MetaData()

# time, type, text
tbl_property = sa.Table('properties', meta,
                        sa.Column('uid', sa.Integer, primary_key=True),
                        # sa.Column('uid', sa.String(255), primary_key=True),
                        # sa.Column('font_size', sa.String(1024)),
                        # sa.Column('type', sa.Integer),
                        sa.Column('apartment', sa.String(1024)),
                        sa.Column('room_no', sa.String(1024)),
                        sa.Column('floor', sa.Integer),
                        sa.Column('occupant_name', sa.String(1024)),
                        sa.Column('contract_period', sa.Integer),
                        sa.Column('contract_type', sa.String(1024)),
                        sa.Column('reserved_pay', sa.Integer),
                        sa.Column('monthly_pay', sa.Integer),
                        sa.Column('non_pay_continues', sa.Integer),
                        sa.Column('contract_startdate', sa.Integer),
                        sa.Column('contract_remains', sa.Integer),
                        sa.Column('updatedtime', sa.Integer),
                        sa.Column('description', sa.String(1024)),
                        sa.Column('payday', sa.Integer),
                        sa.Column('occupant_id', sa.Integer)
                        )

tbl_sms = sa.Table('sms', meta,
                   sa.Column('uid', sa.Integer, primary_key=True),
                   sa.Column('name', sa.String(1024)),
                   sa.Column('pay', sa.Integer),
                   sa.Column('processed', sa.Integer),
                   sa.Column('msg_original', sa.String(1024)),
                   sa.Column('time', sa.String(1024)),
                   )
