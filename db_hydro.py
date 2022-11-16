import sqlalchemy as sa

meta = sa.MetaData()

#time, type, text
tbl_hydro = sa.Table('hydro', meta, 
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('plantname', sa.String(1024)),
        sa.Column('watergauge', sa.Integer),
        sa.Column('waterdate', sa.String(1024)),
        sa.Column('warning', sa.Boolean),
        sa.Column('growth', sa.Integer),
        sa.Column('pieces', sa.String(1024)),
        sa.Column('rootvolume', sa.Integer),
        sa.Column('waterrate', sa.Integer),
        sa.Column('rootrate', sa.Integer),
        sa.Column('growthrate', sa.Integer),
        )

