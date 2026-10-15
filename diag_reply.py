# -*- coding: utf-8 -*-
"""
诊断「点通知无法回复」问题。

给你自己手机发一条推送：
  - url 参数 = 和桌宠完全相同的构造方式（H5?reply=<你的收件箱>）
  - 正文里额外写明完整链接，万一点击跳转没生效，可以直接复制打开
"""
import json

import requests

CFG = r'D:\sisfus-project\couple-pet\dist\config.json'
cfg = json.load(open(CFG, encoding='utf-8'))

MY_KEY = 'FasNSdcSnEgr6pPUF5uDe4'          # 你自己的 key（收测试推送）
MY_TOPIC = cfg['MY_TOPIC']
H5 = cfg['H5_URL']

reply_url = f"{H5}?reply={MY_TOPIC}"
print(f'收件箱 topic : {MY_TOPIC}')
print(f'跳转 URL     : {reply_url}')
print()

body = f'如果点击这条通知没打开页面，请手动复制下面链接：\n{reply_url}'

r = requests.get(
    f'https://api.day.app/{MY_KEY}',
    params={
        'title': '🔧 回复链路诊断',
        'body': body,
        'url': reply_url,
        'sound': 'bell',
        'group': '想念桌宠',
    },
    timeout=15,
)
print('Bark 响应:', r.status_code, r.text[:200])
print()
print('实际请求 URL（关键：url 参数是否被正确编码）：')
print(' ', r.url)
