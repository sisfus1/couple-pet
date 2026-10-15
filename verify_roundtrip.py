# -*- coding: utf-8 -*-
"""
双向链路端到端验证 + 气泡可见性检查。

1. 定位桌宠窗口
2. 截取「窗口本身」和「窗口上方 200px」（气泡应该出现的地方）
3. 往收件箱 topic POST 一条回复
4. 再截一次，比对两块的像素变化 + 颜色
"""
import ctypes
import ctypes.wintypes as wt
import subprocess
import sys
import time
from PIL import ImageGrab, ImageChops

TOPIC = sys.argv[1] if len(sys.argv) > 1 else None
if not TOPIC:
    print('用法: python verify_roundtrip.py <收件箱topic>')
    raise SystemExit(1)

user32 = ctypes.windll.user32
Proc = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

wins = []
def cb(hwnd, lparam):
    if not user32.IsWindowVisible(hwnd):
        return True
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    if 150 <= w <= 300 and 150 <= h <= 300:
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        if 'QWindowTool' in cls.value:
            wins.append((r.left, r.top, w, h))
    return True

user32.EnumWindows(Proc(cb), 0)
if not wins:
    print('❌ 没找到桌宠窗口')
    raise SystemExit(1)

x, y, w, h = wins[0]
print(f'桌宠窗口: ({x},{y}) {w}x{h}')

# 两块观察区：窗口本身 / 窗口上方（气泡区）
BOX_BODY = (x, y, x + w, y + h)
BOX_ABOVE = (x - 60, y - 200, x + w + 60, y)

def snap():
    img = ImageGrab.grab()
    return img.crop(BOX_BODY).convert('RGB'), img.crop(BOX_ABOVE).convert('RGB')

body0, above0 = snap()
print(f'上方气泡区基准: 粉色像素={sum(1 for p in above0.getdata() if p[0]>200 and p[0]-p[1]>20)}')

# ── 模拟"对方在 H5 页面回复"：往我的收件箱发一条消息 ──
print(f'\n>>> POST 回复到 ntfy/{TOPIC}')
r = subprocess.run(['curl', '-s', '-X', 'POST',
                    f'https://ntfy.sh/{TOPIC}',
                    '-H', 'Title: 💌 回复',
                    '-d', '我到家啦，正在想你呢 🥰'],
                   capture_output=True, text=True, encoding='utf-8', errors='ignore')
print(f'    HTTP响应: {r.stdout.strip()[:120]}')

time.sleep(2.0)
body1, above1 = snap()

d_body = ImageChops.difference(body0, body1)
d_above = ImageChops.difference(above0, above1)
try:
    n_body = sum(1 for p in d_body.getdata() if max(p) > 30)
    n_above = sum(1 for p in d_above.getdata() if max(p) > 30)
    px = list(above1.getdata())
except AttributeError:
    n_body = sum(1 for p in d_body.get_flattened_data() if max(p) > 30)
    n_above = sum(1 for p in d_above.get_flattened_data() if max(p) > 30)
    px = list(above1.get_flattened_data())

pink_above = sum(1 for p in px if p[0] > 200 and p[0] - p[1] > 20)
print(f'\n--- 结果 ---')
print(f'  桌宠本体区域像素变化: {n_body}  → {"✅ 动画已切换" if n_body > 300 else "❌ 无反应"}')
print(f'  上方气泡区像素变化  : {n_above}')
print(f'  上方气泡区粉色像素  : {pink_above}  → {"✅ 气泡可见" if pink_above > 300 else "❌ 气泡没显示（被裁剪？）"}')

ImageGrab.grab().crop((x - 60, y - 200, x + w + 60, y + h)).save(
    r'D:\sisfus-project\couple-pet\roundtrip.png')
print('\n  截图已存 roundtrip.png')
