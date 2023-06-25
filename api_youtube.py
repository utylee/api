from time import asctime
import aiohttp
from aiohttp import web
import asyncio
import db_youtube as db
from aiopg.sa import create_engine

import logging
import logging.handlers

async def updatejs(request):
    js = await request.json()
    engine = request.app['db']
    key = js['timestamp']
    title = js['title'].strip()
    
    y_queueing = 0 if len(title) == 0 else 1
    log.info(f'came into updatejs::{key}, {title}')

    res = '' 
    r_dict = dict()

    try:
        # db title 컬럼을 업데이트한 후 해당 로우 결과를 받아와서 응답해줍니다.
        async with engine.acquire() as conn:
            log.info('connected')
            async with conn.execute(db.tbl_youtube_files.update()
                    .where(db.tbl_youtube_files.c.timestamp==key)
                    .values(title=title, youtube_queueing=y_queueing)):
                pass
            async for r in conn.execute(db.tbl_youtube_files.select()
                    .where(db.tbl_youtube_files.c.timestamp==key)):
                if r is not None:

                    '''
                    [2023-06-24 17:26:53,503-result:](Heroes of the Storm 2023.06.24 - 03.50.09.13.mp4'', 'ㅎㅎㅎㅎ', None, 2, 2, 1, 0, 0, /mnt/c/Users/utylee/Videos/Heroes of the Storm/'', '/mnt/clark/4002/00-MediaWorld-4002/97-Capture', 0, 230624035017'')
                        sa.Column('filename', sa.String(255), primary_key=True),
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
                        sa.Column('timestamp', sa.String(255)))
                    '''

                    r_dict['filename'] = r[0]
                    r_dict['title'] = r[1]
                    r_dict['playlist'] = r[2]
                    r_dict['making'] = r[3]
                    r_dict['copying'] = r[4]
                    r_dict['uploading'] = r[5]
                    r_dict['local'] = r[6]
                    r_dict['remote'] = r[7]
                    r_dict['start_path'] = r[8]
                    r_dict['dest_path'] = r[9]
                    r_dict['queueing'] = r[10]
                    r_dict['youtube_queueing'] = r[11]
                    r_dict['timestamp'] = r[12]
                    res = r
                    log.info(f'result:{res}')
                    log.info(f'r_dict:{r_dict}')
                    break
                
    except:
        log.info('updatejs::db exceptioned')


    return web.json_response(r_dict)


async def listjs(request):
    engine = request.app['db']
    l = []
    async with engine.acquire() as conn:
        async for r in conn.execute(db.tbl_youtube_files.select()):
            # print(r[0])
            l.append(dict(r))

    # log.info(l)
    # 정렬해서 전달합니다
    l.sort(key=lambda x:int(x['timestamp']), reverse=True)

    # return web.Response(text='하핫')
    return web.json_response(l)


async def handle(request):

    return web.Response(text='dddd')


async def create_bg_tasks(app):
    app['db'] = await create_engine(host='192.168.1.203',
                                    user='postgres',
                                    password='sksmsqnwk11',
                                    database='youtube_db')

if __name__ == '__main__':

    # loghandler = logging.FileHandler('/home/utylee/youtube_upload_backend')
    loghandler = logging.handlers.RotatingFileHandler(
        '/home/utylee/youtube_upload_backend.log', maxBytes=5*1024*1024, backupCount=3)
    loghandler.setFormatter(logging.Formatter('[%(asctime)s]-%(message)s'))
    log = logging.getLogger('log')
    log.addHandler(loghandler)
    log.setLevel(logging.DEBUG)

    app = web.Application()

    log.info('ㅎㅎㅎㅎ')

    app.on_startup.append(create_bg_tasks)

    app.add_routes([
        web.get('/listjs', listjs),
        web.post('/updatejs', updatejs),
        web.get('/', handle)
    ])

    web.run_app(app, port=9992)
