from aiohttp import web
import asyncio
import uvloop
import re
import os
import time
import socket

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy()) # 최신버전은 uvloop.install()로 
                                            # 간단히 실행할 수 있으나 파이선 3.7이상을 요구합니다   
def getmyip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("192.168.1.1", 80))
        ip = s.getsockname()[0]
        # 아이피 마지막을 얻기위한 방법입니다
        #what = ip.split('.')[-1]
        return s.getsockname()[0]

async def handle(request):
    return web.Response(text='command http site')

async def reboot_5():
    # 5초 후 재붓합니다
    await asyncio.sleep(5)
    #time.sleep(10)
    os.system('echo sksmsqnwk11 | sudo -S reboot')
    return

async def reboot(request):
    # request 에 loop을 넣어줬었군요. 따로 asyncio 를 import 할 필요가 없는 이유였군요
    # 또한await는 코루틴에 걸어줘야하는 것이지 asyncio 메써드에 걸어주면 hang이 걸리고 이상동작합니다
    request.loop.create_task(reboot_5())
    #request.loop.run_in_executor(None, reboot_5)
    #asyncio.ensure_future(reboot_5())
    return web.Response(text='reboot after 5 seconds')

# ?나 다른 기호들이 안들어올 경우를 대비하여 따로 양방향으로 교체를 모두 해줍니다
def transl(t):
    t = re.sub('_u_qa_', '?', t)
    t = re.sub('_u_sp_', ' ', t)
    t = re.sub('_u_im_', '&', t)
    return t

def deco_link(t):
    # print(t)
    r = t
    m = re.search('://|magnet:',t.lower())
    if m:
        r = f'<a href=\'{t}\'>{t}</a>'
    return r

async def ccopy(request):
    l = app['clipboards']
    a = request.match_info['content']
    l.append(a)
    m = f'추가했습니다. 총 {len(l)}개의 항목이 있습니다\n\n'
    #m = f'추가했습니다. 총 {len(l)}개의 항목이 있습니다<br><br>'
    
    # 항목들도 다 보여주기로 합니다
    for i in l:
        m += transl(i) + '\n'
        #m += deco_link(i) + '<br>'

    #return web.Response(text=m, content_type='text/html')
    return web.Response(text=m)

async def cremove(request):
    l = app['clipboards']
    m = '삭제할 데이터가 없습니다\n'
    if len(l) > 0:
        l.pop()
        #m = f'삭제했습니다. {len(l)}개의 항목이 남았습니다<br><br>'
        m = f'삭제했습니다. {len(l)}개의 항목이 남았습니다\n\n'

        # 항목들도 다 보여주기로 합니다
        for i in l:
            #m += deco_link(i) + '<br>'
            m += transl(i) + '\n'

    #return web.Response(text=m, content_type='text/html')
    return web.Response(text=m)

async def cview(request):
    #m = ''
    l = app['clipboards']
    m = f'총 {len(l)}개의 항목이 있습니다<br><br>'
    for i in l:
        m += deco_link(transl(i)) + '<br>'

    return web.Response(text=m, content_type='text/html')

async def cviewtext(request):
    #m = ''
    l = app['clipboards']
    m = f'총 {len(l)}개의 항목이 있습니다\n\n'
    for i in l:
        m += transl(i) + '\n'

    return web.Response(text=m)

'''
app = web.Application()

app.add_routes([web.get('/', handle),
                web.get('/reboot', reboot)
                ])
                '''

if __name__ == '__main__':
    app = web.Application()

    app.add_routes([web.get('/', handle),
                    web.get('/reboot', reboot),
                    web.get('/c/{content:.*}', ccopy),      # 'c'opy, 'c'lipboard 등을 의미하는 단축어입니다
                    web.get('/r', cremove),                 # 'r'emove
                    web.get('/r/{any:.*}', cremove),        # 'r'emove
                    web.get('/v', cview),                   # 'v'iew
                    web.get('/v/{any:.*}', cview),
                    web.get('/vt', cviewtext),              # 'v'iew 't'ext only
                    web.get('/vt/{any:.*}', cviewtext)
                    ])

    app['clipboards'] = []

    my_port = '9' + getmyip().split('.')[-1]
    web.run_app(app, port=my_port)
    #web.run_app(app, port=9213)        # 개발용 테스트 포트입니다


