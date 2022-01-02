import sqlalchemy as sa

meta = sa.MetaData()

#time, type, text
tbl_memo = sa.Table('memos', meta, 
        sa.Column('uid', sa.Integer, primary_key=True),
        # sa.Column('uid', sa.String(255), primary_key=True),
        sa.Column('time', sa.String(1024)),
        sa.Column('type', sa.Integer),
        sa.Column('text', sa.String(1024))
        )



