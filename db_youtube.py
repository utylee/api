import sqlalchemy as sa

meta = sa.MetaData()

# filename, title, playlist, status, timestamp

tbl_youtube_files = sa.Table('files', meta,
                             sa.Column('filename', sa.String(
                                 255), primary_key=True),
                             sa.Column('title', sa.String(255)),
                             sa.Column('playlist', sa.String(255)),
                             sa.Column('making', sa.Integer),
                             sa.Column('copying', sa.Integer),
                             sa.Column('uploading', sa.Integer),
                             sa.Column('local', sa.Integer),
                             sa.Column('remote', sa.Integer),
                             sa.Column('start_path', sa.String(255)),
                             sa.Column('dest_path', sa.String(255)),
                             sa.Column('queueing', sa.Integer),
                             sa.Column('youtube_queueing', sa.Integer),
                             sa.Column('timestamp', sa.String(255)),
                             sa.Column('upscaled', sa.Integer),
                             sa.Column('video_id', sa.String(255)),
                             sa.Column('upscale_pct', sa.Integer)
                             # sa.Column('status', sa.String(255)),
                             # sa.Column('timestamp', sa.Integer))
                             )

tbl_loginjson = sa.Table('loginjson', meta,
                         sa.Column('id', sa.Integer, primary_key=True),
                         sa.Column('date', sa.String(255))
                         )

tbl_youtube_uploading = sa.Table('uploading', meta,
                                 sa.Column('filename', sa.String(255))
                                 )

tbl_youtube_playlists = sa.Table('playlists', meta,
                                 sa.Column('name', sa.String(255)),
                                 sa.Column('nickname', sa.String(255)),
                                 sa.Column('index', sa.Integer),
                                 sa.Column('playlist_id', sa.String(
                                     255), primary_key=True),
                                 sa.Column('description', sa.String(255)))
