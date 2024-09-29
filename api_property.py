import asyncio
from aiohttp import web
import re
import json
import argparse
import random
import time
import uvloop
from aiopg.sa import create_engine
from sqlalchemy import and_
from psycopg2.extras import Json
import db_property as dp

import logging
import logging.handlers


def deco_link(t):
    print(t)
    r = t
    m = re.search('://|magnet:', t.lower())
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


def parse_sms(s):
    name = ''
    pay = 0

    # print(f'parse_sms::s is {s}')

    # example sms:
    # '예금주:이태윤\n 200,000원 입금되었습니다'
    result = re.search(
        r'예금주:[\s\t]*([ㄱ-ㅎ가-힣]+)\n[\s\t]*([0-9,]+)원', s, flags=re.I)
    # print(f'parse_sms::result is {result}')

    try:
        if (result):
            name = result.group(1)
            # print(f'name: {name}')
            pay = result.group(2)
            # print(f'pay 추출: {pay}')
            pay = pay.replace(',', '')
            # print(f'pay , 제거: {pay}')
            pay = int(pay)
            # print(f'pay int화: {pay}')
    except Exception as e:
        print(f'exception occurred in parse_sms: {e}]')
        pass

    return name, pay


async def db_fetch_roominfo(engine, js):
    apart = js['apartment']
    room_no = js['room_no']
    ret = {}
    async with engine.acquire() as conn:
        async for r in conn.execute(dp.tbl_room.select()
                                    .where(and_(dp.tbl_room.c.apartment == apart,
                                                dp.tbl_room.c.room_no == room_no))):
            ret['uid'] = r['uid']
            ret['room_no'] = r['room_no']
            ret['apartment'] = r['apartment']
            ret['floor'] = r['floor']
            ret['sq_footage'] = r['sq_footage']
            ret['defects'] = r['defects']
            ret['defects_history'] = r['defects_history']
            ret['description'] = r['description']
            ret['occupied'] = r['occupied']
            ret['occupant_id'] = r['occupant_id']
            ret['occupant_name'] = r['occupant_name']
            ret['deposit_history'] = r['deposit_history']
            ret['room_type'] = r['room_type']

            print(r)
            print(ret)

    # 입금내역 및 설명을 파싱하여 배열에 담아 리턴합니다
    # 입금내역 구분자는 외부 ? 및 내부 | 입니다
    # 설명 구분자는  | 입니다
    try:
        history = ret['deposit_history']
        temp_history = history.split('?')
        ret['deposit_history'] = [t.split('|') for t in temp_history]

        # ret['description'] =  ret['description'].split('|')
    except Exception as e:
        print(f'exception {e} on db_fetch_roominfo::deposit_history parsing..')

    return ret


async def db_fetch_property(engine, js):
    uid = js['uid']
    print(uid)
    ret = {}
    async with engine.acquire() as conn:
        async for r in conn.execute(dp.tbl_property.select()
                                    .where(dp.tbl_property.c.uid == uid)):
            ret['uid'] = r['uid']
            ret['apartment'] = r['apartment']
            ret['room_no'] = r['room_no']
            ret['floor'] = r['floor']
            ret['occupant_name'] = r['occupant_name']
            ret['contract_period'] = r['contract_period']
            ret['contract_type'] = r['contract_type']
            ret['reserved_pay'] = r['reserved_pay']
            ret['monthly_pay'] = r['monthly_pay']
            ret['non_pay_continues'] = r['non_pay_continues']
            ret['contract_startdate'] = r['contract_startdate']
            ret['contract_remains'] = r['contract_remains']
            ret['updatedtime'] = r['updatedtime']
            ret['description'] = r['description']
            ret['payday'] = r['payday']
            ret['defectiveness'] = r['defectiveness']
            ret['cars'] = r['cars']
            ret['pets'] = r['pets']
            ret['has_issue'] = r['has_issue']
            ret['occupant_id'] = r['occupant_id']

            print(r)
            print(ret)

    return ret


async def db_fetch_occupantinfo(engine, js):
    uid = js['uid']
    print(uid)
    ret = {}
    async with engine.acquire() as conn:
        async for r in conn.execute(dp.tbl_occupant.select()
                                    .where(dp.tbl_occupant.c.uid == uid)):
            # ret = r
            ret['uid'] = r['uid']
            ret['name'] = r['name']
            ret['sex'] = r['sex']
            ret['age'] = r['age']
            ret['height'] = r['height']
            ret['shape'] = r['shape']
            ret['impression'] = r['impression']
            ret['defectiveness'] = r['defectiveness']
            ret['cars'] = r['cars']
            ret['pets'] = r['pets']
            ret['description'] = r['description']
            ret['phone'] = r['phone']
            ret['deposit_history'] = r['deposit_history']

            ret['complaints'] = r['complaints']

            print(r)
            print(ret)

    # 입금내역 및 설명을 파싱하여 배열에 담아 리턴합니다
    # 해당 room뿐 아니라 세입자occupant에도 저장해놓아 장기보존하도록 합니다
    # 입금내역 구분자는 외부 ? 및 내부 | 입니다
    # 설명 구분자는  | 입니다
    try:
        history = ret['deposit_history']
        temp_history = history.split('?')
        ret['deposit_history'] = [t.split('|') for t in temp_history]

        # ret['description'] =  ret['description'].split('|')
    except Exception as e:
        print(f'exception {e} on db_fetch_roominfo::deposit_history parsing..')

    return ret


async def db_update_occupantinfo(engine, js):
    uid = js['uid']
    print(uid)
    ret = {}

    # 입금내역 및 설명을 다시구조화하여 넣습니다
    # 해당 room뿐 아니라 세입자occupant에도 저장해놓아 장기보존하도록 합니다
    # 입금내역 구분자는 외부 ? 및 내부 | 입니다
    # 설명 구분자는  | 입니다

    final = ''
    temp = []
    try:
        print(js['deposit_history'])
        history = js['deposit_history']
        for h in history:
            temp.append('|'.join(h))
        final = '?'.join(temp)
        print(final)

        # ret['description'] =  ret['description'].split('|')
    except Exception as e:
        print(
            f'exception {e} on db_update_occupantinfo::deposit_history string making..')

    async with engine.acquire() as conn:
        ret = await conn.execute(dp.tbl_occupant.update()
                                 .where(dp.tbl_occupant.c.uid == uid)
                                 .values(name=js['name'],
                                         sex=js['sex'],
                                         age=js['age'],
                                         height=js['height'],
                                         shape=js['shape'],
                                         impression=js['impression'],
                                         defectiveness=js['defectiveness'],
                                         cars=js['cars'],
                                         pets=js['pets'],
                                         description=js['description'],
                                         phone=js['phone'],
                                         deposit_history=final,
                                         complaints=js['complaints']))
        print(ret)

    return ret


async def db_update_property(engine, js):
    uid = js['uid']
    # apart = js['apartment']
    # room_no = js['room_no']
    print(f'db_update_roominfo::uid:{uid}')
    ret = {}

    async with engine.acquire() as conn:
        ret = await conn.execute(dp.tbl_property.update()
                                 .where(dp.tbl_property.c.uid == uid)
                                 .values(apartment=js['apartment'],
                                         room_no=js['room_no'],
                                         floor=js['floor'],
                                         occupant_name=js['occupant_name'],
                                         contract_period=js['contract_period'],
                                         contract_type=js['contract_type'],
                                         reserved_pay=js['reserved_pay'],
                                         monthly_pay=js['monthly_pay'],
                                         non_pay_continues=js['non_pay_continues'],
                                         contract_startdate=js['contract_startdate'],
                                         contract_remains=js['contract_remains'],
                                         updatedtime=js['updatedtime'],
                                         description=js['description'],
                                         payday=js['payday'],
                                         defectiveness=js['defectiveness'],
                                         cars=js['cars'],
                                         pets=js['pets'],
                                         has_issue=js['has_issue'],
                                         occupant_id=js['occupant_id']))

        print(ret)

    return ret


async def db_update_roominfo(engine, js):
    # uid = js['uid']
    apart = js['apartment']
    room_no = js['room_no']
    print(f'db_update_roominfo::apart:{apart}, room_no:{room_no}')
    ret = {}

    # 입금내역 및 설명을 다시구조화하여 넣습니다
    # 해당 room뿐 아니라 세입자occupant에도 저장해놓아 장기보존하도록 합니다
    # 입금내역 구분자는 외부 ? 및 내부 | 입니다
    # 설명 구분자는  | 입니다

    final = ''
    temp = []
    try:
        print(f'db_update_roominfo::{js["deposit_history"]}')
        history = js['deposit_history']
        for h in history:
            temp.append('|'.join(h))
        final = '?'.join(temp)
        print(f'db_update_roominfo::final:{final}')

        # ret['description'] =  ret['description'].split('|')
    except Exception as e:
        print(
            f'exception {e} on db_update_roominfo::deposit_history string making..')

    async with engine.acquire() as conn:
        ret = await conn.execute(dp.tbl_room.update()
                                 .where(and_(dp.tbl_room.c.apartment == apart,
                                        dp.tbl_room.c.room_no == room_no))
                                 .values(uid=js['uid'],
                                         room_no=js['room_no'],
                                         floor=js['floor'],
                                         sq_footage=js['sq_footage'],
                                         defects=js['defects'],
                                         defects_history=js['defects_history'],
                                         description=js['description'],
                                         occupied=js['occupied'],
                                         occupant_id=js['occupant_id'],
                                         occupant_name=js['occupant_name'],
                                         deposit_history=final,
                                         room_type=js['room_type']))

        print(ret)

    return ret


async def fetch_roominfo(request):
    print('came into fetch_roominfo')
    # l = request.app['cipboards']
    m = await request.json()
    log.info(f'came into fetch_roominfo(): m is {m}')
    print(f'came into fetch_roominfo(): m is {m}')

    js = None
    if (('room_no' in m.keys()) and ('apartment' in m.keys())):
        js = await db_fetch_roominfo(app['engine'], m)
    return web.json_response(js)


async def fetch_property(request):
    print('came into fetch_property')
    # l = request.app['clipboards']
    m = await request.json()
    log.info(f'came into fetch_property(): m is {m}')
    print(f'came into fetch_property(): m is {m}')

    js = None
    if 'uid' in m.keys():
        js = await db_fetch_property(app['engine'], m)
    return web.json_response(js)


async def fetch_occupantinfo(request):
    print('came into fetch_occupantinfo')
    # l = request.app['clipboards']
    m = await request.json()
    log.info(f'came into fetch_occupantinfo(): m is {m}')
    print(f'came into fetch_occupantinfo(): m is {m}')

    js = None
    if 'uid' in m.keys():
        js = await db_fetch_occupantinfo(app['engine'], m)
    return web.json_response(js)


async def update_occupantinfo(request):
    print('came into update_occupantinfo')
    # l = request.app['clipboards']
    m = await request.json()
    log.info(f'came into update_occupantinfo(): m is {m}')
    print(f'came into update_occupantinfo(): m is {m}')

    js = await db_update_occupantinfo(app['engine'], m)
    # return web.json_response(js)
    return web.Response(text='1')


async def update_roominfo(request):
    print('came into update_roominfo')
    # l = request.app['clipboards']
    m = await request.json()
    log.info(f'came into update_roominfo(): m is {m}')
    print(f'came into update_roominfo(): m is {m}')

    js = await db_update_roominfo(app['engine'], m)
    # return web.json_response(js)
    return web.Response(text='1')


async def update_property(request):
    print('came into update_property')
    # l = request.app['clipboards']
    m = await request.json()
    log.info(f'came into update_property(): m is {m}')
    print(f'came into update_property(): m is {m}')

    js = await db_update_property(app['engine'], m)
    # return web.json_response(js)
    return web.Response(text='1')


async def deliver_sms(request):
    print('came into deliver_sms')
    l = request.app['clipboards']
    m = await request.json()
    log.info(f'came into deliver_sms(): m is {m}')
    print(f'came into deliver_sms(): m is {m}')
    # return web.Response(text='')
    # return web.json_response(m)

    # a = request.match_info['content']

    dict = {}
    dict['msg'] = m['msg']
    dict['time'] = m['time']

    print(f'msg is {m["msg"]}')
    print(f'time is {m["time"]}')

    # 메세지에서 이름과 금액을 분리합니다
    name, pay = parse_sms(dict['msg'])

    print(f'잘 받았습니다. {name} 의 {pay}원')

    dict['name'] = name
    dict['pay'] = pay
    dict['processed'] = 0               # 일단 현재는 가공하지 않으므로 0을 넣어줍니다
    dict['uid'] = create_uid()

    print(f'해당 sms를 db에 삽입합니다')
    print(f'dict is {dict}')
    await db_add_sms(request.app['engine'], dict)

    # 받은 sms의 이름과 금액을 기준으로 세입자를 판단후 property db들을 수정해줍니다
    # ...
    # ...
    # 구현예정..
    #

    return web.Response(text='1')


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
    # app['clipboards'] = [i for i in l if i['time'] != j['time']]
    for i in l:
        # if i['time'] == t:
        if i['uid'] == t:
            l.remove(i)
            # db에서도 삭제합니다
            # await db_remove_memo(app['engine'], t)
            await db_remove_property(app['engine'], t)

    # print(f'{j["id"]}')
    print(app['clipboards'])
    return web.Response(text='kkk')


def create_uid():
    uid = round(random.random() * 10000000)

    return uid


async def addjs(request):
    l = request.app['clipboards']
    m = await request.json()
    print(f'came into addjs(): m is {m}')
    # print(m)
    # return web.Response(text='')
    # return web.json_response(m)

    # a = request.match_info['content']

    dict = {}
    dict['apartment'] = m['apartment']
    dict['updatedtime'] = m['updatedtime']
    dict['uid'] = m['uid']
    dict['room_no'] = m['room_no']
    dict['floor'] = m['floor']
    dict['occupant_name'] = m['occupant_name']
    dict['contract_period'] = m['contract_period']
    dict['contract_type'] = m['contract_type']
    dict['reserved_pay'] = m['reserved_pay']
    dict['monthly_pay'] = m['monthly_pay']
    dict['non_pay_continues'] = m['non_pay_continues']
    dict['contract_startdate'] = m['contract_startdate']
    dict['contract_remains'] = m['contract_remains']
    dict['payday'] = m['payday']
    dict['description'] = m['description']
    dict['text'] = m['text']

    # dict['uid'] = create_uid()
    # dict['type'] = 0

    l.append(dict)
    m = f'추가했습니다. 총 {len(l)}개의 항목이 있습니다\n\n'
    # m = f'추가했습니다. 총 {len(l)}개의 항목이 있습니다<br><br>'

    # db에 추가합니다
    await db_add_property(request.app['engine'], dict)

    # 항목들도 다 보여주기로 합니다
    # for i in l:
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


async def db_add_sms(engine, dict):
    async with engine.acquire() as conn:
        await conn.execute(dp.tbl_sms.insert()
                           .values(uid=dict['uid'],
                                   name=dict['name'],
                                   pay=dict['pay'],
                                   processed=dict['processed'],
                                   msg_original=dict['msg'],
                                   time=dict['time']))
    return 0


async def db_remove_property(engine, id):
    async with engine.acquire() as conn:
        await conn.execute(dp.tbl_property.delete().where(dp.tbl_property.c.uid == id))
    return 0


async def db_add_property(engine, dict):
    async with engine.acquire() as conn:
        await conn.execute(dp.tbl_property.insert()
                           .values(apartment=dict['apartment'],
                                   updatedtime=dict['updatedtime'],
                                   uid=dict['uid'],
                                   roomt_no=dict['room_no'],
                                   floor=dict['floor'],
                                   occupant_name=dict['occupant_name'],
                                   contract_period=dict['contract_period'],
                                   contract_type=dict['contract_type'],
                                   reserved_pay=dict['reserved_pay'],
                                   monthly_pay=dict['monthly_pay'],
                                   non_pay_continues=dict['non_pay_continues'],
                                   contract_startdate=dict['contract_startdate'],
                                   contract_remains=dict['contract_remains'],
                                   payday=dict['payday'],
                                   description=dict['description'],
                                   occupant_id=dict['text']))

    # dict['type'] = 0

    return 0


async def add(request):
    l = app['clipboards']
    a = request.match_info['content']

    dict = {}
    dict['time'] = round(time.time() * 1000)
    dict['font_size'] = 10  # default
    dict['clone'] = 3  # default
    # dict['text'] = request.match_info['content']
    dict['text'] = a
    # dict['type'] = check_type(a)
    # time을 key로 사용하니 겹치는 부분이 있어 따로 랜덤숫자를 생성하기로 합니다
    dict['uid'] = create_uid()

    l.append(dict)
    m = f'추가했습니다. 총 {len(l)}개의 항목이 있습니다\n\n'
    # m = f'추가했습니다. 총 {len(l)}개의 항목이 있습니다<br><br>'

    # db에 추가합니다
    await db_add_property(request.app['engine'], dict)

    # 항목들도 다 보여주기로 합니다
    for i in l:
        m += transl(i['text']) + '\n'
        # m += deco_link(i) + '<br>'

    return web.Response(text=m)


async def list(request):
    # m = ''
    l = app['clipboards']
    m = f'총 {len(l)}개의 항목이 있습니다\n\n'
    for i in l:
        m += transl(i['text']) + '\n'

    return web.Response(text=m)


async def listsms(request):
    # ret = {}
    ret = []

    await db_fetch_sms(app['sms'], app['engine'])

    full = app['sms']
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

    # return web.json_response(ret)
    return web.json_response(full)


async def listjs(request):
    # ret = {}
    ret = []
    temp_dict = {}
    # temp_dict['maxvill'] = [[], [], []]
    temp_dict['richvill'] = [[], [], []]
    temp_dict['dochon'] = [[], [], [], []]

    app['clipboards'] = []
    await db_fetch_rows(app['clipboards'], app['engine'])

    full = app['clipboards']
    for l in full:
        # temp = {}
        # temp['text'] = l
        # ret.append(temp)
        # 굳이 오브젝트 형태로 재조립하여 보낼 필요가 없어졌습니다

        floor = l['floor']
        # if (l['apartment'] == 'maxvill'):
        if (l['apartment'] == 'richvill'):
            # 맥스빌은 2,3,4층 이므로 해당배열 0,1,2는 2씩 빼주기로 합니다
            # temp_dict['maxvill'][floor - 2].append(l)
            temp_dict['richvill'][floor - 2].append(l)

        elif (l['apartment'] == 'dochon'):
            # 도촌동은 1,2,3,4층 이므로 해당배열 0,1,2,3은 1씩 빼주기로 합니다
            temp_dict['dochon'][floor - 1].append(l)
            # temp_dict['dochon'].append(l)

        ret.append(l)
        # print(f'listjs : {l}')
        # ret['text'] = l
        # i += 1
    # 결과를 sort 합니다
    for i in range(0, 3):
        # temp_dict['maxvill'][i].sort(key=lambda x: x['room_no'])
        temp_dict['richvill'][i].sort(key=lambda x: x['room_no'])

    for i in range(0, 4):
        temp_dict['dochon'][i].sort(key=lambda x: x['room_no'])

    # ret_json = json.dumps(ret)
    # print(f'return:{ret_json}')

    # return web.json_response(ret)
    # return web.json_response(ret_json)
    # return web.json_response(full)
    return web.json_response(temp_dict)


async def remove(request):
    l = app['clipboards']
    m = '삭제할 데이터가 없습니다\n'
    if len(l) > 0:
        # db에서도 삭제합니다
        await db_remove_property(app['engine'], l[-1]['uid'])
        # db에서 먼저삭제후 pop을 하기로 순서를 바꿉니다
        l.pop()
        # m = f'삭제했습니다. {len(l)}개의 항목이 남았습니다<br><br>'
        m = f'삭제했습니다. {len(l)}개의 항목이 남았습니다\n\n'

        # 항목들도 다 보여주기로 합니다
        for i in l:
            # m += deco_link(i) + '<br>'
            m += transl(i['text']) + '\n'

    return web.Response(text=m)


async def init(app):
    app['engine'] = await create_engine(host='192.168.1.204',
                                        database='property_db',
                                        user='utylee',
                                        password='sksmsqnwk11')

    app['clipboards'] = []
    app['sms'] = []
    await db_fetch_rows(app['clipboards'], app['engine'])

    app.add_routes([
        web.get('/property/api/listjs', listjs),
        web.get('/property/api/listsms', listsms),
        web.post('/property/api/fetch_roominfo', fetch_roominfo),
        web.post('/property/api/fetch_occupantinfo', fetch_occupantinfo),
        web.post('/property/api/fetch_property', fetch_property),
        web.post('/property/api/update_occupantinfo', update_occupantinfo),
        web.post('/property/api/update_roominfo', update_roominfo),
        web.post('/property/api/update_property', update_property),
        # 안드로이드로부터 수신한 sms를 전달받습니다
        web.post('/property/api/deliversms', deliver_sms),

        web.post('/property/api/addjs', addjs),
        web.post('/property/api/removejs', removejs),
    ])

    return app


async def db_fetch_sms(lt, engine):
    print('came into db_fetch_sms')
    # app['clipboards'] = []
    async with engine.acquire() as conn:
        async for r in conn.execute(dp.tbl_sms.select()):
            dict = {}
            dict['uid'] = r['uid']
            dict['name'] = r['name']
            dict['pay'] = r['pay']
            dict['processed'] = r['processed']
            dict['msg_original'] = r['msg_original']
            dict['time'] = r['time']

            lt.append(dict)

    # app['clipboards'] = l
    # print(f'clipboard:{lt}')

    return 0


async def db_fetch_rows(lt, engine):
    print('came into db_fetch_rows')
    # app['clipboards'] = []
    async with engine.acquire() as conn:
        async for r in conn.execute(dp.tbl_property.select()):
            dict = {}
            dict['apartment'] = r['apartment']
            dict['updatedtime'] = r['updatedtime']
            dict['uid'] = r['uid']
            dict['room_no'] = r['room_no']
            dict['floor'] = r['floor']
            dict['occupant_name'] = r['occupant_name']
            dict['occupant_id'] = r['occupant_id']
            dict['contract_period'] = r['contract_period']
            dict['contract_type'] = r['contract_type']
            dict['reserved_pay'] = r['reserved_pay']
            dict['monthly_pay'] = r['monthly_pay']
            dict['non_pay_continues'] = r['non_pay_continues']
            dict['contract_startdate'] = r['contract_startdate']
            dict['contract_remains'] = r['contract_remains']
            dict['cars'] = r['cars']
            dict['pets'] = r['pets']
            dict['has_issue'] = r['has_issue']
            dict['defectiveness'] = r['defectiveness']
            dict['description'] = r['description']
            dict['payday'] = r['payday']

            lt.append(dict)

    # app['clipboards'] = l
    print(f'clipboard:{lt}')

    return 0

if __name__ == "__main__":
    # uvloop을 사용합니다
    uvloop.install()

    # --path 아큐먼트를 받는 부분입니다
    parser = argparse.ArgumentParser(description='api_property')
    parser.add_argument('--path')
    parser.add_argument('--port')
    args = parser.parse_args()

    loghandler = logging.handlers.RotatingFileHandler(
        '/home/utylee/api_property.log', maxBytes=5*1024*1024, backupCount=3)
    loghandler.setFormatter(logging.Formatter('[%(asctime)s]-%(message)s'))
    log = logging.getLogger('log')
    log.addHandler(loghandler)
    # log.setLevel(logging.DEBUG)
    log.setLevel(logging.INFO)

    app = web.Application()

    # clipboarrd 구조
    #       { uid (_key값), time , text, type(0 or 1 : text or url ) }

    '''
    app['clipboards'] = [
            { 'uid': 10000000, time': 1640412852000, 'text': '데헷', 'type': 0 },
            { 'uid': 10000000, time': 1640412853000, 'text': '빵야빵야', 'type': 0 },
            { 'uid': 10000000, time': 1640412854000, 'text': 'http://naver.com', 'type': 1 },
            { 'uid': 10000000, time': 1640412855000, 'text': '일자도끼', 'type': 2 },
            { 'uid': 10000000, time': 1640412856000, 'text': '하하하하하하하하', 'type': 0 }
            ]
            '''

    # print(app['clipboards'][0]['text'])

    # web.run_app(init(app), port=args.port, path=args.path)
    web.run_app(init(app),  path=args.path)
    # web.run_app(init(app), port=9090)
    # web.run_app(init(app), path=args.path, port=8080)
    # web.run_app(init(app), port=8080)
    # web.run_app(init(app), port=8080)
    # web.run_app(app, port=8080)
    # web.run_app(init(app), path='/tmp/api.sock')
    # web.run_app(app, path='/tmp/api.sock', port=8080)
