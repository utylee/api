import sqlalchemy as sa
from sqlalchemy.types import Integer

meta = sa.MetaData()

# time, type, text
tbl_property = sa.Table('properties', meta,
                        sa.Column('uid', sa.Integer, primary_key=True),
                        sa.Column('apartment', sa.String(1024)),
                        sa.Column('room_no', sa.Integer),
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
                        sa.Column('defectiveness', sa.Integer),
                        sa.Column('cars', sa.Integer),
                        sa.Column('pets', sa.Integer),
                        sa.Column('has_issue', sa.Integer),
                        sa.Column('occupant_id', sa.Integer)
                        )

tbl_room = sa.Table('rooms', meta,
                    sa.Column('uid', sa.Integer, primary_key=True),
                    sa.Column('room_no', sa.Integer),
                    sa.Column('apartment', sa.String(1024)),
                    sa.Column('floor', sa.Integer),
                    sa.Column('sq_footage', sa.Integer),
                    sa.Column('defects', sa.String(1024)),
                    sa.Column('defects_history', sa.String(1024)),
                    sa.Column('description', sa.Text),
                    sa.Column('occupied', sa.Integer),
                    sa.Column('occupant_id', sa.Integer),
                    sa.Column('occupant_name', sa.String(1024)),
                    sa.Column('deposit_history', sa.Text),
                    sa.Column('room_type', sa.String(1024))
                    )

tbl_occupant = sa.Table('occupants', meta,
                        sa.Column('uid', sa.Integer, primary_key=True),
                        sa.Column('name', sa.String(1024)),
                        sa.Column('sex', sa.String(1024)),
                        sa.Column('age', sa.String(1024)),
                        sa.Column('height', sa.Integer),
                        sa.Column('shape', sa.String(1024)),
                        sa.Column('impression', sa.String(1024)),
                        sa.Column('defectiveness', sa.String(1024)),
                        sa.Column('cars', sa.Integer),
                        sa.Column('pets', sa.Integer),
                        sa.Column('description', sa.Text),
                        sa.Column('phone', sa.String(1024)),
                        sa.Column('deposit_history', sa.Text),
                        sa.Column('complaints', sa.Text)
                        )

tbl_sms = sa.Table('sms', meta,
                   sa.Column('uid', sa.Integer, primary_key=True),
                   sa.Column('name', sa.String(1024)),
                   sa.Column('pay', sa.Integer),
                   sa.Column('processed', sa.Integer),
                   sa.Column('msg_original', sa.String(1024)),
                   sa.Column('time', sa.String(1024)),
                   )
