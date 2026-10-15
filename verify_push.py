# -*- coding: utf-8 -*-
"""
验证「桌宠 → 手机」这条链路：复现 pet.py::_send_bark 的请求构造，
把最终 URL 打印出来核对，并给你自己手机发一条可直接点击的测试推送。

（发给你自己的 key，不打扰她。）
"""
import json
import os
import urllib.parse

import requests

BASE = r'D:\sisfus-project\couple-pet'
cfg = json.load(open(os.path.join(BASE, 'configs', 'me.json'), encoding='utf-8'))

HIS_KEY = 'FasNSdcSnEgr6pPUF5uDe4'      # 你自己的 key（测试用，不碰她的）

# 完全复现 pet.py 的构造逻辑
reply_url = f"{cfg['H5_URL']}?reply={cfg['MY_TOPIC']}"
params = {
    'title': f"{cfg['MY_NAME']}想你啦 💖",
    'body': f"{cfg['MY_NAME']}刚刚戳了戳桌宠：我想你啦！💖",
    'url': reply_url,
    'sound': 'bell',
    'group': '想念桌宠',
}
endpoint = f"https://api.day.app/{cfg['PARTNER_BARK_KEY']}"
final = endpoint + '?' + urllib.parse.urlencode(params)

print("=== pet.py 实际会发出的请求（她收到的那条）===")
print(f"  收件人 key : {cfg['PARTNER_BARK_KEY'][:6]}…(她的)")
print(f"  最终 URL   : {final}")
print()
print("=== 关键参数核对 ===")
print(f"  跳转 url   : {reply_url}")
print(f"  回复会发往 : ntfy/{cfg['MY_TOPIC']}  ← 我的收件箱")
print(f"  topic 是否为随机长串 : {'✅' if len(cfg['MY_TOPIC']) >= 20 else '❌'}")
print()

# ── 给你自己手机发一条等价测试推送（换成你的 key，topic 也用你自己的，形成自闭环）──
print("=== 给你自己手机发测试推送 ===")
test_params = dict(params)
test_params['title'] = '🔧 链路测试（点我跳转页面）'
test_params['body'] = '来自你的桌宠·配置自测。点开这条通知应该打开互动页面。'
try:
    r = requests.get(f"https://api.day.app/{HIS_KEY}", params=test_params, timeout=15)
    print(f"  HTTP {r.status_code}  {r.text.strip()[:100]}")
    if r.status_code == 200 and '"code":200' in r.text:
        print("  ✅ Bark 已受理 —— 检查你手机是否收到，点开应跳到互动页面")
    else:
        print("  ❌ Bark 返回异常")
except Exception as e:
    print(f"  ❌ 请求失败: {e}")
