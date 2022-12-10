import db_hydro as dh
import json
import uvloop
import aiohttp
from aiohttp import web
import asyncio
import re
import argparse
import random
import time
from aiopg.sa import create_engine


def create_uid():
    uid = round(random.random() * 10000000)

    return uid


async def updatejs(request):
    js = await request.json()
    print('updatejs:got js:{js}')
    result = await db_update_row(js, request.app['engine'])
    return web.json_response({'result': result})
    # return web.json_response(ret_json)


async def listjs(request):
    # ret = {}
    ret = []
    app['clipboards'] = await db_fetch_rows(app['clipboards'], app['engine'])

    full = app['clipboards']
    # i = 0
    for l in full:
        # temp = {}
        # temp['text'] = l
        # ret.append(temp)
        # 굳이 오브젝트 형태로 재조립하여 보낼 필요가 없어졌습니다
        ret.append(l)
        print(f'update : {l}')
        # ret['text'] = l
        # i += 1
    # ret_json = json.dumps(ret)
    # print(f'return:{ret_json}')

    return web.json_response(ret)
    # return web.json_response(full)
    # return web.json_response(ret_json)

# async def remove(request):
#    l = app['clipboards']
#    m = '삭제할 데이터가 없습니다\n'
#    if len(l) > 0:
#        # db에서도 삭제합니다
#        await db_remove_memo(app['engine'], l[-1]['uid'])
#        # db에서 먼저삭제후 pop을 하기로 순서를 바꿉니다
#        l.pop()
#        #m = f'삭제했습니다. {len(l)}개의 항목이 남았습니다<br><br>'
#        m = f'삭제했습니다. {len(l)}개의 항목이 남았습니다\n\n'


#        # 항목들도 다 보여주기로 합니다
#        for i in l:
#            #m += deco_link(i) + '<br>'
#            m += transl(i['text']) + '\n'

#    return web.Response(text=m)

async def init(app):
    # app['engine'] = await create_engine(host='192.168.1.204',
    #                           database='hydro_db',
    #                           user='utylee',
    #                           password='sksmsqnwk11')
    # print('start')
    # print(app['engine'])
    app['clipboards'] = []
    await db_fetch_rows(app['clipboards'], app['engine'])

    '''
        {
          id: 1,
          plantName: "신홍적축면",
          waterGauge: 85,
          waterDate: getDate(),
          warning: 0,
          growth: 65,
          pieces: [
            [1, 0, 1, 0],
            [0, 1, 1, 0],
            [1, 0, 1, 0],
          ],
          rootVolume: 10,
          waterRate: 1,
          rootRate: 1,
          growthRate: 1,
          imageUrl: '중엽쑥갓.png'
        },
    '''

    for i in app['clipboard']:
        print(i)

    return app


async def db_update_row(js, engine):
    result = 0
    async with engine.acquire() as conn:
        result = await conn.execute(dh.tbl_hydro.update().where(dh.tbl_hydro.c.id == js['id'])
                                    .values(plantname=js['plantName'],
                                            watergauge=js['waterGauge'],
                                            waterdate=js['waterDate'],
                                            warning=js['warning'],
                                            growthgauge=js['growthGauge'],
                                            pieces=js['pieces'],
                                            rootvolume=js['rootVolume'],
                                            waterrate=js['waterRate'],
                                            rootrate=js['rootRate'],
                                            growthrate=js['growthRate'],
                                            imageurl=js['imageUrl']))
    return result


async def db_fetch_rows(lt, engine):
    # app['clipboards'] = []
    lt = []
    async with engine.acquire() as conn:
        async for r in conn.execute(dh.tbl_hydro.select()):
            dict = {}
            dict['id'] = r.id
            dict['plantName'] = r.plantname
            dict['waterGauge'] = r.watergauge
            dict['waterDate'] = r.waterdate
            dict['warning'] = r.warning
            dict['growthGauge'] = r.growthgauge
            dict['pieces'] = r.pieces
            dict['rootVolume'] = r.rootvolume
            dict['waterRate'] = r.waterrate
            dict['rootRate'] = r.rootrate
            dict['growthRate'] = r.growthrate
            dict['imageUrl'] = r.imageurl
            lt.append(dict)
            # lt = dict
    # app['clipboards'] = lt
    for i in lt:
        print(f'{i}')
        # print(f'clipboard:{lt}')

    return lt


async def create_bg_tasks(app):
    app['engine'] = await create_engine(host='192.168.1.204',
                                        database='hydro_db',
                                        user='utylee',
                                        password='sksmsqnwk11')
    app['clipboards'] = []
    await db_fetch_rows(app['clipboards'], app['engine'])


async def clean_bg_tasks(app):
    pass


if __name__ == "__main__":
    # uvloop을 사용합니다
    uvloop.install()

    # --path 아큐먼트를 받는 부분입니다
    parser = argparse.ArgumentParser(description='api_hydro')
    parser.add_argument('--path')
    parser.add_argument('--port')
    args = parser.parse_args()

    app = web.Application()
    app['engine'] = []
    app.on_startup.append(create_bg_tasks)
    app.on_cleanup.append(clean_bg_tasks)

    app.add_routes([
        # react용 리스트 반납
        web.get('/hydro/api/listjs', listjs),

        # react용 메모 추가
        web.post('/hydro/api/updatejs', updatejs),
    ])

    # run_app의 첫번째 인자를 app을 넘겨주느냐 혹은 init(app)과 같은 함수로 넘겨주느냐
    #   에 따라 동작이 다릅니다. create_bg_tasks 방식을 사용할 경우 그냥 app을 넘겨줘야
    #   합니다
    # web.run_app(app, path=args.path)
    # print(args.port)
    web.run_app(app, port=args.port, path=args.path)
    # web.run_app(app, port=args.port)
    # web.run_app(app, port=8081)

    # web.run_app(init(app), path=args.path)
    # web.run_app(init(app), port=8081)
    # web.run_app(app, port=8080)
    # web.run_app(init(app), path='/tmp/api.sock')
    # web.run_app(app, path='/tmp/api.sock', port=8080)
