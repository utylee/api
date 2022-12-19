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
import math
import copy
from aiopg.sa import create_engine


def create_uid():
    uid = round(random.random() * 10000000)

    return uid


async def updatejs(request):
    js = await request.json()
    print(f'updatejs::{js}')

    # result 반환은 따로 없는 것 같습니다 예제를 보니
    # result = await db_update_row(js, request.app['engine'])
    await db_update_row(js, request.app['engine'])
    # print(f'result:{result}')

    return web.json_response({'result': 1})
    # return web.json_response(ret_json)


async def listjs(request):
    # ret = {}
    ret = []
    # app['clipboards'] = await db_fetch_rows(app['clipboards'], app['engine'])
    # app['db_boards'] = await db_fetch_rows(app['db_boards'], app['engine'])
    await db_fetch_rows(app['db_boards'], app['engine'])

    temp_boards = prepare_serialize(app['db_boards'])

    # full = app['clipboards']
    full = []
    for i in range(1, 9):
        # full.append(app['db_boards'][i])
        full.append(temp_boards[i])

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
    # app['clipboards'] = []
    app['db_boards'] = []
    # await db_fetch_rows(app['clipboards'], app['engine'])
    await db_fetch_rows(app['db_boards'], app['engine'])

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

    # for i in app['clipboard']:
    for i in app['db_boards']:
        print(i)

    return app


async def db_update_row(js, engine):
    result = 0
    # print(f'db_update_row: js : {js}')
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
    # lt = []
    async with engine.acquire() as conn:
        async for r in conn.execute(dh.tbl_hydro.select()):
            dt = {}
            dt['id'] = r.id
            dt['plantName'] = r.plantname
            dt['waterGauge'] = r.watergauge
            dt['waterDate'] = r.waterdate
            dt['warning'] = r.warning
            dt['growthGauge'] = r.growthgauge
            dt['pieces'] = r.pieces
            dt['rootVolume'] = r.rootvolume
            dt['waterRate'] = r.waterrate
            dt['rootRate'] = r.rootrate
            dt['growthRate'] = r.growthrate
            dt['imageUrl'] = r.imageurl
            # lt.append(dict)

            # 저장될 자료형 형식은 아래와 같습니다
            # {1: {id: xxx, plantName: xxx ..}, 2: { xxx}}
            lt[dt['id']] = dt
            # lt[dt['id']].append(dt)
            # lt.update({dt['id']: dt})
            # lt = dict

    # app['db_boards'] = lt

    # id:8 발아판 게이지를 growth root게이지를 각각 활용하므로
    # 배열로 변환할 필요가 없습니다
    # 이후 id:8 발아판은 워터게이지를 변환해서 각 배열로 갖고 있게 합니다
    # t1 = math.floor(lt[8]['waterGauge'] / 10000)
    # t2 = lt[8]['waterGauge'] % 10000
    # t3 = t2 % 100
    # t2 = math.floor(t2 / 100)

    # print(f'clipboard:{lt}')

    # for i in lt:
    #     print(f'{i}')
    # print(f'clipboard:{lt}')

    # return lt


def calc_each_row(app):
    lt = app['db_boards']
    element = app['calc_divide_element']

    # print(f'calc_each_row:')
    # print(f'full: {lt}')

    # 일반과 씨앗발아를 별개로 계산해줍니다
    # 일반판
    for i in range(1, 8):
        # 소수셋째자리까지만 구합니다
        water_delta = round(lt[i]['waterRate'] / element, 3) * 1000
        # print(f'water_delta: {water_delta}')
        lt[i]['waterGauge'] -= water_delta
        if lt[i]['waterGauge'] < 0:
            lt[i]['waterGauge'] = 0

        root_delta = round(lt[i]['rootRate'] / element, 3) * 1000
        # print(f'root_delta: {root_delta}')
        lt[i]['rootVolume'] += root_delta
        # 100 * 1000: 계산편의상 100%에서 0세개를 더 추가해줍니다
        if lt[i]['rootVolume'] > 100000:
            lt[i]['rootVolume'] = 100000

        growth_delta = round(lt[i]['growthRate'] / element, 3) * 1000
        # print(f'growth_delta: {growth_delta}')
        lt[i]['growthGauge'] += growth_delta
        if lt[i]['growthGauge'] > 100000:
            lt[i]['growthGauge'] = 100000

    # 씨앗발아판
    # t1 = math.floor(lt[8]['waterGauge'] / 10000)
    # t2 = lt[8]['waterGauge'] % 10000
    # t3 = t2 % 100
    # t2 = math.floor(t2 / 100)

    gem_delta = round(lt[8]['waterRate'] / element, 3) * 1000
    # print(f'gem_delta: {gem_delta}')
    # print(f'gem.waterGauge: ', lt[8]['waterGauge'] )
    lt[8]['waterGauge'] -= gem_delta
    # print(f'gem.waterGauge: ', lt[8]['waterGauge'] )
    if lt[8]['waterGauge'] < 0:
        lt[8]['waterGauge'] = 0
    lt[8]['growthGauge'] -= gem_delta
    if lt[8]['growthGauge'] < 0:
        lt[8]['growthGauge'] = 0
    lt[8]['rootVolume'] -= gem_delta
    if lt[8]['rootVolume'] < 0:
        lt[8]['rootVolume'] = 0
    # print('ok')

    # for i in range(0, 3):
    #     # lt[8]['waterGauge'][i] -= gem_delta
    #     lt[8]['waterGauge'][i] = lt[8]['waterGauge'][i] - gem_delta
    #     print(lt[8]['waterGauge'][i])
    #     if lt[8]['waterGauge'][i] < 0:
    #         lt[8]['waterGauge'][i] = 0

    # print(lt[8]['waterGauge'])
    # print(f'{lt}')


async def insert_calc_result(app):
    lt = app['db_boards']

    temp_boards = prepare_serialize(lt)
    # print(f'before inserting temp_boards: {temp_boards}')

    # 각 Gauge를 정수화한 값을 db에 넣어줍니다
    # temp_boards = copy.deepcopy(lt)

    # for i in range(1, 8):
    #     temp_boards[i]['waterGauge'] = round(temp_boards[i]['waterGauge'])
    #     temp_boards[i]['growthGauge'] = round(temp_boards[i]['growthGauge'])
    #     temp_boards[i]['rootVolume'] = round(temp_boards[i]['rootVolume'])

    # # id: 8 발아판 waterGauge를 통합합니다
    # temp_boards[8]['waterGauge'] = round(temp_boards[8]['waterGauge'][0] * 10000) \
    #     + round(temp_boards[8]['waterGauge'][1]) * 100 \
    #     + round(temp_boards[8]['waterGauge'][2])

    # 각 id 한 row씩 db에 넣어줍니다
    for i in range(1, 9):
        await db_update_row(temp_boards[i], app['engine'])


# db에 insert하거나 listjs 에 반납하기 위해 gem배열을 묶고 각 게이지값을 정수화합니다
def prepare_serialize(lt):
    # 각 Gauge를 정수화한 값을 db에 넣어줍니다
    temp_boards = copy.deepcopy(lt)

    for i in range(1, 9):
        temp_boards[i]['waterGauge'] = round(temp_boards[i]['waterGauge'])
        temp_boards[i]['growthGauge'] = round(temp_boards[i]['growthGauge'])
        temp_boards[i]['rootVolume'] = round(temp_boards[i]['rootVolume'])

    # 안합니다
    # id: 8 발아판 waterGauge를 통합합니다
    # temp_boards[8]['waterGauge'] = round(temp_boards[8]['waterGauge'][0]) * 10000 \
    #     + round(temp_boards[8]['waterGauge'][1]) * 100 \
    #     + round(temp_boards[8]['waterGauge'][2])

    return temp_boards


async def timer_proc(app):
    while True:
        try:
            # 계산을 행하기 전 최신 db 값을 항상 받아옵니다
            await db_fetch_rows(app['db_boards'], app['engine'])
            calc_each_row(app)
            await insert_calc_result(app)

        except:
            print('!!except')
            pass

            # 30분에 한 번 씩 업데이트 합니다
        await asyncio.sleep(1800)
        # await asyncio.sleep(1)


async def create_bg_tasks(app):
    app['engine'] = await create_engine(host='192.168.1.204',
                                        database='hydro_db',
                                        user='utylee',
                                        password='sksmsqnwk11')
    # db데이터 관리변수입니다
    # app['db_boards'] = []
    app['db_boards'] = {}
    await db_fetch_rows(app['db_boards'], app['engine'])

    # 게이지 프로시져 시작
    # deprecated error
    # app['timer_proc'] = app.loop.create_task(timer_proc(app))
    app['timer_proc'] = asyncio.create_task(timer_proc(app))


async def clean_bg_tasks(app):
    app['timer_proc'].cancel()
    await app['timer_proc']


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
    # 각 rate는 일주일 동안 몇 프로이냐이고
    #  타이머는 30분에 한번씩 돌아가는 것을 고려한 유닛설정입니다
    # 7 * 24 * 2 = 336
    app['calc_divide_element'] = 7 * 24 * 2
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
