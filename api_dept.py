import aiohttp
from aiohttp import web
import asyncio
import logging
import logging.handlers
import argparse
import re
import json
import aioschedule as schedule
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
# from selenium.webdriver.firefox.options import Options
# from selenium.webdriver.firefox.service import Service

import uvloop

from api_youtube import create_bg_tasks

INTV =  300             # fetch 주기(초)
# INTV =  20             # fetch 주기(초)

DEPTS = [
    ('lotte', 'https://www.lotteshopping.com/store/main?cstrCd=0008'),  # 롯데백화점 분당점
    ('shinsegae', 'https://www.shinsegae.com/store/main.do?storeCd=SC00007'), # 신세계 경기
    ('ak', 'https://www.akplaza.com/store/introduce?store=03'), # ak 분당
    ('hyundai', 'https://www.ehyundai.com/newPortal/DP/DP000000_V.do?branchCd=B00148000'),  # 현대 판교
]


TIME_INTV = 1200             # 20분에 한번씩 웹페이지들을 가져옵니다

# ak 분당파싱 루틴


async def ak(url):
    status = '휴점'
    time = ''
    lines = []
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            res = await resp.text()
            # print(res)

            # log.info('ak 분당점')
            # log.info(res)

            # html을 파싱합니다
            # <article class="infoArea">
            # <strong>오늘의 영업시간<br>
            # <span><em>10:30</em> ~ <em>20:30</em></span>^
            lines = res.splitlines()
            # print(lines)

    # 전체 문자열에서 해당 라인을 찾아냅니다
    c = 0
    lines2 = []
    for l in lines:
        # print(l)
        m = re.search('<article class="infoArea">', l, re.I)
        if m:
            print(f'ak found!!: {m.group(0)}')
            lines2 = lines[c+1:]
        c += 1

    # 찾아낸 문자열의 향후 8열까지만 분리해서 파싱합니다
    # <strong>오늘의 영업시간<br>
    # <span><em>10:30</em> ~ <em>20:30</em></span>^
    for ll in lines2[:8]:
        # print(ll)
        n = re.search(r'<strong>오늘의 영업시간<br>', ll, re.I) 
        if n:
            # 영업 중이라는 텍스트가 없어 직접 지정해주는 형태로 가겠습니다
            status = '영업 중'
        o = re.search(r'<span><em>(.*)</em>\s~\s<em>(.*)</em></span>', ll, re.I)
        if o:
            time = f'{o.group(1)} ~ {o.group(2)}'
            # print(o.group(1))
    return (status, time)


# 신세계 경기 파싱 루틴
async def shinsegae(url):
    status = ''
    time = ''
    lines = []

    # <div id="weatherChk" class="weather "> ...
    # <span class="hour">오늘은       10:30부터 20:00까지<br> 정상 영업합니다.</span>

    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            res = await resp.text()
            # print(res)

            # log.info('신세계')
            # log.info(res)

            # html을 파싱합니다
            lines = res.splitlines()
            # print(lines)

    # 전체 문자열에서 해당 라인을 찾아냅니다
    # <div id="weatherChk" class="weather "> ...
    c = 0
    lines2 = []
    for l in lines:
        # print(l)
    # <div id="weatherChk" class="weather "> ...
        m = re.search('<div id="weatherChk" class="weather', l, re.I)
        if m:
            print(f'shinsegae found!!: {m.group(0)}')
            lines2 = lines[c+1:]
        c += 1

    # 찾아낸 문자열의 향후 8열까지만 분리해서 파싱합니다
    for ll in lines2[:8]:
        # print(ll)
        # <span class="hour">오늘은       10:30부터 20:00까지<br> 정상 영업합니다.</span>

        # n = re.search(r'오늘은[\s]+(.*)까지', ll, re.I)
        # if n:
        #     status = n.group(1)
        #     print(n.group(1))

        o = re.search(r'오늘은[\s]+(.*)까지<br>\s(.*)합니다', ll, re.I)
        if o:
            status = o.group(2)
            time = o.group(1)
            print(o.group(1))
    return (status, time)

async def hyundai_pangyo_selenium(url):
    service = Service(executable_path='/usr/lib/chromium-browser/chromedriver')
    options = webdriver.ChromeOptions()
    # options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    res = driver.page_source
    # log.info('현대 판교점 selenium')
    # log.info(res)

    status = '영업중'
    time = ''
    # lines = []
    lines = res.splitlines()

    c = 0
    lines2 = []
    for l in lines:
        # print(l)
        m = re.search('<div class="overview_box">', l, re.I)
        if m:
            print(f'hyundai found!!: {m.group(0)}')
            lines2 = lines[c+1:]
        c += 1

    # 찾아낸 문자열의 향후 140열까지만 분리해서 파싱합니다
    # <p class="info_tit">오늘의 영업시간은<br> <em>10:30 ~ 20:30</em> >      입니다.</p> <!-- //[D] case2. 영업할 시 -->
    # <p class="info_tit">오늘은<br> <em>휴점일</em> 입니다.</p> <!-- /      /[D] case3. 휴점일 시 -->


    for ll in lines2[:140]:
        # print(ll)
        n = re.search(r'<p class="info_tit">오늘의 영업시간은<br> <em>(.*)</em>', ll, re.I)
        # n = re.search(r'<p class="info_tit" id="runningTime">오늘은<br> <em>(.*)</em>', ll, re.I)
        if n:
            time = n.group(1)
            # status = '영업중'
            print(time)

        o = re.search(r'<p class="info_tit">오늘은<br> <em>(.*)</em> 입니다', ll, re.I)
        if o:
            status = o.group(1)
            print(status)

    # 셀레니움을 닫습니다.
    driver.quit()

    return (status, time)


# 현대 판교 파싱 루틴
async def hyundai_pangyo(url):
    status = ''
    time = ''
    lines = []
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            res = await resp.text()
            # print(res)

            log.info('현대 판교 no selenium')
            log.info(res)

            # html을 파싱합니다
            # <div class="overview_box">
            # 181448                                 <div class="information">
            # 181449                                     <p class="info_tit" id="runningTime">오늘은br>< <em10:30        ~ 20:00>/em>< 까지 영업합니다./p<
            # 181450                                     <>div class="info_desc">
            # 181451                                         <dl class="left">
            # 181452 

            lines = res.splitlines()
            # print(lines)

            # status, time = lotte_bundang(lines)
    # 전체 문자열에서 해당 라인을 찾아냅니다
    c = 0
    lines2 = []
    for l in lines:
        # print(l)
        m = re.search('<div class="overview_box">', l, re.I)
        if m:
            print(f'hyundai found!!: {m.group(0)}')
            lines2 = lines[c+1:]
        c += 1

    # 찾아낸 문자열의 향후 8열까지만 분리해서 파싱합니다
    # <p class="info_tit" id="runningTime">오늘은<br> <em>10:30 ~ 20:00</em> 까지 영업합니다.</p>
    for ll in lines2[:8]:
        # print(ll)
        n = re.search(r'<p class="info_tit" id="runningTime">오늘은<br> <em>(.*)</em>', ll, re.I)
        if n:
            status = n.group(1)
            print(n.group(1))
        o = re.search(r'영업시간은<b>(.*)</b>', ll, re.I)
        if o:
            time = o.group(1)
            print(o.group(1))
    return (status, time)


async def parse_dept(tup):
    res = ()
    if (tup[0] == 'lotte'):
        res = await lotte_bundang(tup[1])
    elif (tup[0] == 'hyundai'):
        # res = await hyundai_pangyo(tup[1])
        res = await hyundai_pangyo_selenium(tup[1])
    elif (tup[0] == 'ak'):
        res = await ak(tup[1])
    elif (tup[0] == 'shinsegae'):
        res = await shinsegae(tup[1])

    return res              # tuple (status, time)


# 분당 롯데 파싱 루틴
# async def lotte_bundang(lines):
async def lotte_bundang(url):
    status = ''
    time = ''
    lines = []
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            res = await resp.text()
            # print(res)

            # log.info(res)

            # html을 파싱합니다
            # <div class="__running"> 찾기
            lines = res.splitlines()
            # print(lines)

            # status, time = lotte_bundang(lines)
    # 전체 문자열에서 해당 라인을 찾아냅니다
    c = 0
    lines2 = []
    for l in lines:
        # print(l)
        m = re.search('__running">', l, re.I)
        if m:
            print(f'found!!: {m.group(0)}')
            lines2 = lines[c+1:]
        c += 1

    # 찾아낸 문자열의 향후 5열까지만 분리해서 파싱합니다
    # <p>영업시간은<b>10:30 ~ 20:00</b>입니다.</p>
    for ll in lines2[:5]:
        # print(ll)
        n = re.search(r'오늘은\s<b>(.*)</b><span', ll, re.I)
        if n:
            status = n.group(1)
            print(n.group(1))
        o = re.search(r'영업시간은<b>(.*)</b>', ll, re.I)
        if o:
            time = o.group(1)
            print(o.group(1))
    return (status, time)


async def get(request):
    # return web.Response(text=f'{result}')
    # json.dumps 중 한글 깨짐 encoding 문제 생길시
    return web.json_response(json.dumps(request.app['result'], ensure_ascii=False))


async def handle(request):

    return web.Response(text='success')

async def fetch(app):
    lines = []
    result = 'not found\n\n'

    for i in DEPTS:
        # log.info(f'connecting: {i}..')
        log.info(f'connecting: {i[0]}..')

        # 접속의 오류가 간간히 발생하기에 try 로 감싸주고 초기변수를 줍니다
        status, time = '', ''
        try:
            status, time = await parse_dept(i)
        except Exception as e:
            log.info(f'exception {e} on fetching {i[0]}...')
            continue

        result += f'{i[0]}:\n{status}\n{time}\n\n'
        app['result'][i[0]] = {'status': status, 'time': time} 

        # async with aiohttp.ClientSession() as sess:
        #     async with sess.get(i) as resp:
        #         res = await resp.text()
        #         # print(res)

        #         # log.info(res)
    # log.info(f'{result}')
    log.info(f'{app["result"]}')


async def timer_proc(app):
    # 하루에 특정 시간에만 긁어오게끔 합니다
    schedule.every().day.at('00:10').do(fetch, app)
    schedule.every().day.at('07:00').do(fetch, app)
    schedule.every().day.at('14:00').do(fetch, app)
    schedule.every().day.at('22:00').do(fetch, app)
    # schedule.every().day.at('17:37').do(fetch, app)
    # loop = asyncio.get_event_loop()

    while True:
        asyncio.create_task(schedule.run_pending())
        # loop.run_until_complete(schedule.run_pending())
        await asyncio.sleep(2)

        # await fetch(app)
        # await asyncio.sleep(30)


    # while True:
    #     print(f'INTERVAL : {app["intv"]}')

    #     lines = []
    #     result = 'not found\n\n'

    #     for i in DEPTS:
    #         # log.info(f'connecting: {i}..')
    #         log.info(f'connecting: {i[0]}..')
    #         status, time = await parse_dept(i)
    #         result += f'{i[0]}:\n{status}\n{time}\n\n'

    #         # async with aiohttp.ClientSession() as sess:
    #         #     async with sess.get(i) as resp:
    #         #         res = await resp.text()
    #         #         # print(res)

    #         #         # log.info(res)
    #     log.info(f'{result}')

    #     await asyncio.sleep(app['intv'])


async def create_bg_tasks(app):
    asyncio.create_task(timer_proc(app))


if __name__ == '__main__':
    uvloop.install()

    log = logging.getLogger('dept')
    loggerHandler = logging.handlers.RotatingFileHandler(
        '/home/utylee/api_dept.log', maxBytes=10 * 1024 * 1024, backupCount=3)
    loggerHandler.setFormatter(logging.Formatter('[%(asctime)s]-%(message)s'))
    log.addHandler(loggerHandler)
    log.setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description='dept')
    parser.add_argument('--port')
    parser.add_argument('--path')

    args = parser.parse_args()

    app = web.Application()

    app.add_routes([
        web.get('/', handle),
        web.get('/get', get)
    ])

    app['intv'] = INTV
    app['result'] = dict()

    app.on_startup.append(create_bg_tasks)

    web.run_app(app, port=args.port)
