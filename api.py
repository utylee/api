import asyncio
from aiohttp import web
import re
import json
import argparse
import random
import time
import uvloop
from aiopg.sa import create_engine
import db_memo as dm 

def deco_link(t):
    print(t)
    r = t
    m = re.search('://|magnet:',t.lower())
    if m:
        r = f'<a href=\'{t}\'>{t}</a>'
    return r

def check_type(arg):
    t = 0
    arg = arg.strip()
    # print(arg[:3].lower())
    # print(arg[:4].lower())
    if (arg[:4].lower() == 'http' or arg[:5].lower() == 'https'):
        t = 1
    elif (arg[:6].lower() == 'magnet'):
        t = 2

    return t

async def removejs(request):
    j = await request.json()
    l = app['clipboards']
    # print('옵니까')
    print(f'{j}')
    # print(f'{j['text']}')
    # del app['clipboards'][j['time']]

    # t = j['time']
    t = j['uid']
    # 두가지 방법 중 어떤 방법을 써도 됩니다
    #app['clipboards'] = [i for i in l if i['time'] != j['time']]
    for i in l:
        # if i['time'] == t:
        if i['uid'] == t:
            l.remove(i)
            # db에서도 삭제합니다
            await db_remove_memo(app['engine'], t)

    # print(f'{j["id"]}')
    print(app['clipboards'])
    return web.Response(text='kkk')

def create_uid():
    uid = round(random.random() * 10000000)

    return uid

async def addjs(request):
    l = app['clipboards']
    m = await request.json()
    #print(m)
    #return web.Response(text='')
    #return web.json_response(m)

    #a = request.match_info['content']

    dict = {}
    #dict['time'] = time.time()
    dict['time'] = m['time']
    dict['text'] = m['text']
    dict['type'] = check_type(m['text'])
    dict['uid'] = create_uid()
    #dict['type'] = 0
    
    l.append(dict)
    m = f'추가했습니다. 총 {len(l)}개의 항목이 있습니다\n\n'
    #m = f'추가했습니다. 총 {len(l)}개의 항목이 있습니다<br><br>'

    # db에 추가합니다
    await db_add_memo(request.app['engine'], dict)

    # 항목들도 다 보여주기로 합니다
    #for i in l:
    #    m += transl(i['text']) + '\n'
    #    #m += deco_link(i) + '<br>'

    return web.Response(text='0')

def transl(t):
    print(t)
    t = re.sub('_u_qa_', '?', t)                                                                    
    t = re.sub('_u_sp_', ' ', t)
    t = re.sub('_u_im_', '&', t)
    return t
'''
tbl_memo = sa.Table('memos', meta, 
        sa.Column('time', sa.Integer, primary_key=True),
        sa.Column('type', sa.Integer),
        sa.Column('text', sa.String(255))
        )
        '''
async def db_remove_memo(engine, id):
    async with engine.acquire() as conn:
        await conn.execute(dm.tbl_memo.delete().where(dm.tbl_memo.c.uid==id))
    return 0

async def db_add_memo(engine, dict):
    async with engine.acquire() as conn:
        await conn.execute(dm.tbl_memo.insert().values(time=dict['time'],
                                                    type=dict['type'],
                                                    uid=dict['uid'],
                                                    text=dict['text']))
    return 0

async def add(request):
    l = app['clipboards']
    a = request.match_info['content']

    dict = {}
    dict['time'] = round(time.time() * 1000)
    # dict['text'] = request.match_info['content']
    dict['text'] = a
    dict['type'] = check_type(a)
    # time을 key로 사용하니 겹치는 부분이 있어 따로 랜덤숫자를 생성하기로 합니다
    dict['uid'] = create_uid()
    
    l.append(dict)
    m = f'추가했습니다. 총 {len(l)}개의 항목이 있습니다\n\n'
    #m = f'추가했습니다. 총 {len(l)}개의 항목이 있습니다<br><br>'

    # db에 추가합니다
    await db_add_memo(request.app['engine'], dict)

    # 항목들도 다 보여주기로 합니다
    for i in l:
        m += transl(i['text']) + '\n'
        #m += deco_link(i) + '<br>'

    return web.Response(text=m)

async def list(request):
    #m = ''
    l = app['clipboards']
    m = f'총 {len(l)}개의 항목이 있습니다\n\n'
    for i in l:
        m += transl(i['text']) + '\n'

    return web.Response(text=m)

async def listjs(request):
    #ret = {}
    ret = []
    full = app['clipboards']
    # i = 0
    for l in full:
        # temp = {}
        # temp['text'] = l
        # ret.append(temp)
        # 굳이 오브젝트 형태로 재조립하여 보낼 필요가 없어졌습니다
        ret.append(l)
        print(f'update : {l}')
        #ret['text'] = l
        #i += 1
    # ret_json = json.dumps(ret)
    # print(f'return:{ret_json}')

    #return web.json_response(ret)
    return web.json_response(full)
    # return web.json_response(ret_json)

async def remove(request):
    l = app['clipboards']
    m = '삭제할 데이터가 없습니다\n'
    if len(l) > 0:
        # db에서도 삭제합니다
        await db_remove_memo(app['engine'], l[-1]['uid'])
        # db에서 먼저삭제후 pop을 하기로 순서를 바꿉니다
        l.pop()
        #m = f'삭제했습니다. {len(l)}개의 항목이 남았습니다<br><br>'
        m = f'삭제했습니다. {len(l)}개의 항목이 남았습니다\n\n'


        # 항목들도 다 보여주기로 합니다
        for i in l:
            #m += deco_link(i) + '<br>'
            m += transl(i['text']) + '\n'

    return web.Response(text=m)

async def init(app):
    app['engine'] = await create_engine(host='192.168.1.204',
                                        database='memo_db',
                                        user='utylee',
                                        password='sksmsqnwk11')

    app['clipboards'] = []
    await db_fetch_rows(app['clipboards'], app['engine'])

    app.add_routes([
                    # react용 리스트 반납 
                    web.get('/api/listjs', listjs), 
                    # 터미널용 리스트 반납 
                    web.get('/api/list', list), 

                    # react용 메모 추가
                    web.post('/api/addjs', addjs),
                    # 터미널용 메모 추가
                    web.get('/api/add/{content:.*}', add),

                    # react용 메모 제거
                    web.post('/api/removejs', removejs),
                    # 터미널용 메모 제거
                    web.get('/api/remove', remove)
                ])

    return app

async def db_fetch_rows(lt, engine):
    # app['clipboards'] = []
    async with engine.acquire() as conn:
        async for r in conn.execute(dm.tbl_memo.select()):
            dict = {}
            dict['uid'] = r.uid
            dict['time'] = r.time
            dict['type'] = r.type
            dict['text'] = r.text
            lt.append(dict)
    # app['clipboards'] = l 
    print(f'clipboard:{lt}')

    return 0

if __name__ == "__main__":
    # uvloop을 사용합니다
    uvloop.install()

    # --path 아큐먼트를 받는 부분입니다
    parser = argparse.ArgumentParser(description='api')
    parser.add_argument('--path')
    args = parser.parse_args()

    app = web.Application()


    # clipboarrd 구조 
    #       { time (_key값), text, type(0 or 1 : text or url ) }
    # app['clipboards'] = ['데헷', ['빵야빵야','핑크', '일자보지']]

    # app['clipboards'] = [ 
    #         { 'time': round(time.time()), 'text': '데헷', 'type': 0 },
    #         { 'time': round(time.time()), 'text': '빵야빵야', 'type': 0 },
    #         { 'time': round(time.time()), 'text': 'http://naver.com', 'type': 1 },
    #         { 'time': round(time.time()), 'text': '일자도끼', 'type': 2 },
    #         { 'time': round(time.time()), 'text': '하하하하하하하하', 'type': 0 }
    #         ]

    '''
    app['clipboards'] = [ 
            { 'time': 1640412852000, 'text': '데헷', 'type': 0 },
            { 'time': 1640412853000, 'text': '빵야빵야', 'type': 0 },
            { 'time': 1640412854000, 'text': 'http://naver.com', 'type': 1 },
            { 'time': 1640412855000, 'text': '일자도끼', 'type': 2 },
            { 'time': 1640412856000, 'text': '하하하하하하하하', 'type': 0 }
            ]
            '''

    # print(app['clipboards'][0]['text'])


    web.run_app(init(app), port=8080)
    # web.run_app(app, port=8080)
    #web.run_app(app, path='/tmp/api.sock')
    #web.run_app(app, path=args.path)
    #web.run_app(app, path='/tmp/api.sock', port=8080)

