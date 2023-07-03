from time import asctime
import aiohttp
from aiohttp import web
import asyncio
import db_youtube as db
from aiopg.sa import create_engine

import logging
import logging.handlers
import json

from collections import OrderedDict
import copy


async def upload_complete(request):
    js_ = await request.json()
    log.info(f'upload_complete::js_ is {js_}')

    # 업로드 성공 플래그일 경우
    if js_['result'] == 0:
        engine = request.app['db']
        file = js_['file']

        try:
            async with engine.acquire() as conn:
                async with conn.execute(db.tbl_youtube_files.update()
                                        .where(db.tbl_youtube_files.c.filename == file)
                                        .values(uploading=3)):
                    log.info(f'upload_complete::changed uploading to 3')
        except:
            log.info(f'upload_complete::exception')

    return web.Response(text='ok')


async def gimme_que(request):
    # 달라는 요청을 받았으므로 OrderedDict 에서 첫번째 항목을 꺼내서 전달해줍니다
    # 그리고 db의 업로드 상태를 변경합니다
    log.info('came into gimme_que')
    log.info(request.app['youtube_queue'])
    queue = request.app['youtube_queue']
    resp = (0, 0)
    if (len(queue) > 0):
        # queue 를 popitem 하면 변경되므로 복사해서 db 의 copying 플래그를 가져옵니다
        queue_c = copy.deepcopy(queue)
        resp_c = queue_c.popitem(last=False)
        log.info(f'resp_c(,) is {resp_c}')

        # db 복사상태 가져오기
        engine = request.app['db']
        copying = 0

        try:
            async with engine.acquire() as conn:
                async for r in conn.execute(db.tbl_youtube_files.select()
                                    .where(db.tbl_youtube_files.c.filename == resp_c[0])):
                    copying = int(r[4])
                    log.info('gimme_que::current copying flag is {copying}')
        except:
            log.info('gimme_que::db select exception')

        if(copying == 2):
            resp = queue.popitem(last=False)
            log.info(f'resp(,) is {resp}')
            # log.info(f'response:: file:{resp[0]}, title:{resp[1]}')

            # db 업로드 상태 변경
            engine = request.app['db']
            try:
                async with engine.acquire() as conn:
                    async with conn.execute(db.tbl_youtube_files.update()
                                            .where(db.tbl_youtube_files.c.filename == resp[0])
                                            .values(uploading=2)):

                        log.info(f'file {resp[0]} db to uploading=2')
            except:
                log.info('gimme_que::excepted')

    # return web.json_response(json.dumps({"file": f'{resp[0]}', "title": f'{resp[1]}'}))
    # return web.Response(text=json.dumps({"file": f'{resp[0]}', "title": f'{resp[1]}'}))
    log.info(f'response:: file:{resp[0]}, title:{resp[1]}')
    return web.json_response(json.dumps({"file": resp[0], "title": resp[1]}))
    # return web.json_response({"file": f'{resp[0]}', "title": f'{resp[1]}'})

'''
    # next = request.app['youtube_queue'].popitem(last=False)
    # log.info(f'will send to youtube uploader:file:{next[0]}, title:{next[1]}')
    try:
        # youtube uploader 에 post 합니다
        async with aiohttp.ClientSession() as sess:
            async with sess.post('http://192.168.1.204:9993/file',
                                 json=json.dumps(
                                     {'file': next[0],
                                         'title': next[1]})):
                pass
    except:
        log.info('gimme_que::exception')

    return web.Response(text='ok')
'''


async def updatejs(request):
    js = await request.json()
    engine = request.app['db']
    key = js['timestamp']
    title = js['title'].strip()
    filename = ''

    y_queueing = 0 if len(title) == 0 else 1
    log.info(f'came into updatejs::{key}, {title}')

    res = ''
    r_dict = dict()

    try:
        # db title 컬럼을 업데이트한 후 해당 로우 결과를 받아와서 응답해줍니다.
        async with engine.acquire() as conn:
            log.info('connected')
            async with conn.execute(db.tbl_youtube_files.update()
                                    .where(db.tbl_youtube_files.c.timestamp == key)
                                    .values(title=title, youtube_queueing=y_queueing)):
                pass
            async for r in conn.execute(db.tbl_youtube_files.select()
                                        .where(db.tbl_youtube_files.c.timestamp == key)):
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

                    filename = r[0]

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

        # 빈 제목이 아니라면 wsl2의 youtube_uploading에 post합니다
        # xxxx빈 제목이 아니라면 youtube_que 에 넣습니다
        if y_queueing == 1:
            # app['youtube_queue'].update({filename: title})
            log.info('y_queueing == 1')
            # log.info('youtube_queue inserted')
            # log.info(request.app['youtube_queue'])
            async with aiohttp.ClientSession() as sess:
                async with sess.post('http://192.168.1.204:9993/addque',
                                     json=json.dumps(
                                         {'file': filename,
                                             'title': title})):
                    log.info(
                        f'send to youtube_uploading:file:{filename}, title:{title}')

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
    l.sort(key=lambda x: int(x['timestamp']), reverse=True)

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
    app['youtube_queue'] = OrderedDict()

    log.info('api_youtube started')

    app.on_startup.append(create_bg_tasks)

    app.add_routes([
        web.get('/listjs', listjs),
        web.get('/gimme_que', gimme_que),
        web.post('/upload_complete', upload_complete),
        web.post('/updatejs', updatejs),
        web.get('/', handle)
    ])

    web.run_app(app, port=9992)
