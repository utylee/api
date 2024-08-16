import sqlalchemy as sa
from sqlalchemy.types import Integer

meta = sa.MetaData()

# time, type, text
tbl_print = sa.Table('prints', meta,
                     sa.Column('uid', sa.Integer, primary_key=True),
                     # sa.Column('uid', sa.String(255), primary_key=True),
                     # sa.Column('font_size', sa.String(1024)),
                     # sa.Column('type', sa.Integer),
                     sa.Column('font_size', sa.Integer),
                     sa.Column('time', sa.String(1024)),
                     sa.Column('text', sa.String(1024)),
                     sa.Column('clone', sa.Integer)
                     )
