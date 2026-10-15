# -*- coding: utf-8 -*-
"""
端到端验证「点桌宠 → 发 Bark 推送」这条链路。

为了不打扰对方，临时把推送目标换成你自己的 Bark Key，测完自动还原。
流程：备份配置 → 换成你的 key → 启动 → 模拟点击 → 本地验证动画/气泡 → 还原配置 → 重启
"""
import ctypes
import ctypes.wintypes as wt
import json
import os
import shutil
import subprocess
import time

BASE = r'D:\sisfus-project\couple-pet'
DIST = os.path.join(BASE, 'dist')
EXE = os.path.join(DIST, '想念桌宠-me.exe')
CFG = os.path.join(DIST, 'config.json')
BAK = CFG + '.bak-verify'
HIS_KEY = 'FasNSdcSnEgr6pPUF5uDe4'      # 你自己的 key（测试用）

user32 = ctypes.windll.user32
Proc = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


def kill_pet():
    subprocess.run(['taskkill', '/F', '/IM', '想念桌宠-me.exe'],
                   capture_output=True, text=True, encoding='gbk', errors='ignore')
    time.sleep(1.5)


def start_pet():
    subprocess.Popen([EXE], cwd=DIST,
                     creationflags=subprocess.DETACHED_PROCESS |
                                   subprocess.CREATE_NEW_PROCESS_GROUP,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(7)


def find_pet():
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
    return wins[0] if wins else None


def snap():
    from PIL import ImageGrab
    return ImageGrab.grab()


def pink_count(img):
    try:
        px = list(img.convert('RGB').get_flattened_data())
    except AttributeError:
        px = list(img.convert('RGB').getdata())
    return sum(1 for p in px if p[0] > 200 and p[0] - p[1] > 20 and p[2] > 140)


def diff_count(a, b):
    from PIL import ImageChops
    d = ImageChops.difference(a.convert('RGB'), b.convert('RGB'))
    try:
        return sum(1 for p in d.get_flattened_data() if max(p) > 30)
    except AttributeError:
        return sum(1 for p in d.getdata() if max(p) > 30)


# ══════════════════════════════════════════
kill_pet()

# 备份 + 临时换成你的 key
shutil.copy2(CFG, BAK)
cfg = json.load(open(CFG, encoding='utf-8'))
original_key = cfg['PARTNER_BARK_KEY']
cfg['PARTNER_BARK_KEY'] = HIS_KEY
json.dump(cfg, open(CFG, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f'① 已备份配置，临时把推送目标换成你自己的 key（原为 {original_key[:6]}…）')

start_pet()
win = find_pet()
if not win:
    print('❌ 桌宠窗口没起来，中止')
    shutil.copy2(BAK, CFG)
    raise SystemExit(1)
x, y, w, h = win
print(f'② 桌宠已启动: ({x},{y}) {w}x{h}')

BOX_BODY = (x, y, x + w, y + h)
BOX_ABOVE = (x - 80, y - 160, x + w + 80, y)

img0 = snap()
body0, above0 = img0.crop(BOX_BODY), img0.crop(BOX_ABOVE)
print(f'③ 点击前: 本体粉色={pink_count(body0)}  上方粉色={pink_count(above0)}')

# ── 模拟左键点击桌宠中心 ──
pt = wt.POINT()
user32.GetCursorPos(ctypes.byref(pt))
orig = (pt.x, pt.y)
cx, cy = x + w // 2, y + h // 2
user32.SetCursorPos(cx, cy)
time.sleep(0.25)
user32.mouse_event(0x0002, 0, 0, 0, 0)
time.sleep(0.06)
user32.mouse_event(0x0004, 0, 0, 0, 0)
print(f'④ 已模拟点击 ({cx},{cy})')

time.sleep(0.8)
img1 = snap()
body1, above1 = img1.crop(BOX_BODY), img1.crop(BOX_ABOVE)
user32.SetCursorPos(orig[0], orig[1])

d_body = diff_count(body0, body1)
d_above = diff_count(above0, above1)
p_above = pink_count(above1)
print(f'⑤ 点击后: 本体像素变化={d_body}  上方像素变化={d_above}  上方粉色={p_above}')
img1.crop((x - 80, y - 160, x + w + 80, y + h)).save(os.path.join(BASE, 'click_verify.png'))

# ── 等动画结束回 idle ──
time.sleep(3.2)
body2 = snap().crop(BOX_BODY)
d_back = diff_count(body0, body2)
print(f'⑥ 3.2秒后晃动残差={d_back} ({"已回 idle ✅" if d_back < d_body else "仍在动"})')

# ── 还原配置并重启 ──
kill_pet()
shutil.copy2(BAK, CFG)
os.remove(BAK)
start_pet()
restored = json.load(open(CFG, encoding='utf-8'))['PARTNER_BARK_KEY']
print(f'⑦ 已还原配置（推送目标={restored[:6]}…）并重启桌宠')

print('\n=== 判定 ===')
print(f'  点击被响应(动画切换) : {"✅" if d_body > 300 else "❌"}  ({d_body} px)')
print(f'  气泡弹出发送提示     : {"✅" if p_above > 300 else "❌"}  ({p_above} 粉色像素)')
print('  Bark 推送已发出      : 见你手机是否收到「猪猪想你啦 💖」')
