import uvloop
import argparse
from time import asctime
import aiohttp
from aiohttp import web
import asyncio
import db_youtube as db
from aiopg.sa import create_engine

import logging
import logging.handlers
import json

from collections import OrderedDict, defaultdict
import copy

URL_CAPTURE_WATCHER = 'http://localhost/youtube/watcher/deletefile'


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

            # youtube uploader의 needRefresh를 호출합니다. websocket
            async with aiohttp.ClientSession() as sess:
                async with sess.get('http://192.168.1.204:9993/ws_refresh'):
                    log.info('call needRefresh')

        except:
            log.info(f'upload_complete::exception')

    return web.Response(text='ok')


async def report_loginjson_date(request):
    txt = await request.text()
    log.info(f'loginjson_date:: got::{txt}')
    app['login_json_date'] = txt

    # 받은 데이터를 db에 저장합니다
    try:
        engine = request.app['db']
        async with engine.acquire() as conn:
            async with conn.execute(db.tbl_loginjson.update()
                                    .where(db.tbl_loginjson.c.id == 1)
                                    .values(date=txt)):
                log.info(f'loginjson_date db inserted::{txt}')
    except Exception as e:
        log.info(f'report_loginjson_date::exception {e}')

    return web.Response(text='ok')


async def websocket_handler(request):
    # transport 를 굳이 쓰지 않아도 되게끔 변경했다고 합니다
    # eg)https://github.com/aio-libs/aiohttp/issues/4189
    # peer_info = request.transport.get_extra_info('peername')
    peer_info = request.get_extra_info('peername')
    # (host, port) = request.transport.get_extra_info('peername')
    remote = request.remote
    # forward = request.headers.get('X-FORWARDED-FOR', 2)
    # peer_info = f'{host}:{port}'
    peer_info = f'{peer_info[0]}:{peer_info[1]}'
    # peer_info = f'{remote}'
    # peer_info = f'{host}:{port},{remote},{forward}'
    log.info(f'came into websocket_handlers: {peer_info}')
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    request.app['websockets'][peer_info].add(ws)

    log.info(f'sockets dict:{app["websockets"]}')

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                log.info(f'ws msg:{msg.data}')
                await ws.send_str(msg.data + ':answer')
        elif msg.type == aiohttp.WSMsgType.ERROR:
            log.info(f'websocket msg type error: {ws.exception()})')

    log.info('websocket closed')

    return ws


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

        if (copying == 2):
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


async def deletejs(request):
    # 102 capture_watcher.py PC에 로컬,리모트 모두 삭제 명령을 전달합니다
    js = await request.json()
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.post(URL_CAPTURE_WATCHER, json=json.dumps({'timestamp': js['timestamp'],
                                                                       'filename': js['filename']})) as resp:
                rsp = await resp.text()
                log.info(f'response:{rsp}')

    except Exception as e:
        log.info(f'exception {e}')

    return web.Response(text='done')


async def updatejs(request):
    log.info(f'came into updatejs')
    js = await request.json()
    engine = request.app['db']
    key = js['timestamp']
    title = js['title'].strip()
    playlist = js['playlist']
    filename = ''

    y_queueing = 0 if len(title) == 0 else 1
    log.info(f'came into updatejs::{key}, {title}, {playlist}')

    res = ''
    r_dict = dict()

    try:
        # db title 컬럼을 업데이트한 후 해당 로우 결과를 받아와서 응답해줍니다.
        async with engine.acquire() as conn:
            log.info('connected')
            async with conn.execute(db.tbl_youtube_files.update()
                                    .where(db.tbl_youtube_files.c.timestamp == key)
                                    .values(title=title, youtube_queueing=y_queueing\
                                            , playlist=playlist)):
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
                # async with sess.post('http://192.168.1.204:9993/addque',
                async with sess.post('http://localhost/youtube/uploader/addque',
                                     json=json.dumps(
                                         {'file': filename,
                                            'title': title, \
                                            'playlist': playlist})):
                    log.info(
                        f'send to youtube_uploading:file:{filename}, title:{title}')
            # 또한 needRefresh 를 호출해줍니다. websocket
            # youtube uploader의 needRefresh를 호출합니다. websocket
            async with aiohttp.ClientSession() as sess:
                async with sess.get('http://192.168.1.204:9993/ws_refresh'):
                    log.info('call needRefresh')

    except:
        log.info('updatejs::db exceptioned')

    return web.json_response(r_dict)


async def listjs(request):
    # log.info('listjs')
    engine = request.app['db']
    files = []
    playlists = []
    async with engine.acquire() as conn:
        async for r in conn.execute(db.tbl_youtube_files.select()):
            # print(r[0])
            files.append(dict(r))
        async for r in conn.execute(db.tbl_youtube_playlists.select()):
            playlists.append(dict(r))

    # log.info(l)
    # 정렬해서 전달합니다
    files.sort(key=lambda x: int(x['timestamp']), reverse=True)

    playlists.sort(key=lambda x: x['index'])

    # return web.Response(text='하핫')
    return web.json_response(json.dumps({"json_date": request.app['login_json_date'],
                                         "files": files, 
                                         "playlists": playlists}))
    # return web.json_response(l)


async def handle(request):

    return web.Response(text='dddd')


async def create_bg_tasks(app):
    engine = await create_engine(host='192.168.1.203',
                                 user='postgres',
                                 password='sksmsqnwk11',
                                 database='youtube_db')
    app['db'] = engine
    try:
        # login_json_date를 db로부터 받아둡니다
        async with engine.acquire() as conn:
            condition = 0   # 데이터가 없을 경우를 위한 변수입니다
            async for r in conn.execute(db.tbl_loginjson.select()
                                        .where(db.tbl_loginjson.c.id == 1)):
                app['login_json_date'] = r[1]
                log.info(f'db date fetch:{r[1]}')
                condition = 1

            # 데이터가 없을 경우 최초로 삽입해줍니다
            if condition == 0:
                log.info('no date in db')
                async with conn.execute(db.tbl_loginjson.insert()
                                        .values(id=1,
                                                date=app['login_json_date'])):
                    log.info(
                        f'db date inserted first time:{app["login_json_date"]}')
    except Exception as e:
        log.info(f'create_bg_tasks::exception {e}')

if __name__ == '__main__':
    uvloop.install()

    # ArgumentParser
    parser = argparse.ArgumentParser(description='api_youtube')
    parser.add_argument('--port')
    parser.add_argument('--path')
    args = parser.parse_args()

    # loghandler = logging.FileHandler('/home/utylee/youtube_upload_backend')
    # '/tmp/youtube_upload_backend.log', maxBytes=5*1024*1024, backupCount=3)
    # '/home/utylee/youtube_upload_backend.log', maxBytes=5*1024*1024, backupCount=3)
    loghandler = logging.handlers.RotatingFileHandler(
        '/home/utylee/youtube_upload_backend.log', maxBytes=5*1024*1024, backupCount=3)
    loghandler.setFormatter(logging.Formatter('[%(asctime)s]-%(message)s'))
    log = logging.getLogger('log')
    log.addHandler(loghandler)
    # log.setLevel(logging.DEBUG)
    log.setLevel(logging.INFO)

    app = web.Application()
    app['youtube_queue'] = OrderedDict()
    app['websockets'] = defaultdict(set)
    app['login_json_date'] = '791031-21:00:00'

    log.info('api_youtube started')

    app.on_startup.append(create_bg_tasks)

    app.add_routes([
        web.get('/listjs', listjs),
        web.get('/gimme_que', gimme_que),
        web.post('/upload_complete', upload_complete),
        web.post('/updatejs', updatejs),
        web.post('/deletejs', deletejs),
        web.post('/report_loginjson_date', report_loginjson_date),
        # web.get('/ws', websocket_handler),
        web.get('/', handle)
    ])

    web.run_app(app, port=args.port, path=args.path)
