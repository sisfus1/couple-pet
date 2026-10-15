# -*- coding: utf-8 -*-
"""
自动生成桌宠所需的透明 GIF 动画素材和 ICO 图标。
依赖: Pillow (PIL)
运行: python generate_assets.py
"""
from PIL import Image, ImageDraw
import math
import os

WIDTH, HEIGHT = 200, 200


def new_canvas():
    """创建全透明 RGBA 画布"""
    return Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))


def draw_dango(draw, cx, cy, scale=1.0, blink=False, blush=False,
               eye_offset_y=0, mouth_type='smile', shake_x=0):
    """
    绘制Q版圆润团子小人。
    cx, cy: 中心坐标
    scale: 整体缩放
    blink: 眨眼
    blush: 脸红
    mouth_type: 'smile' | 'shy' | 'happy'
    """
    bx = cx + shake_x
    by = cy

    body_w = int(72 * scale)
    body_h = int(66 * scale)

    # 阴影 (淡灰色椭圆)
    draw.ellipse(
        [bx - body_w // 2 + 2, by + body_h // 2 - 4,
         bx + body_w // 2 + 2, by + body_h // 2 + 8],
        fill=(210, 210, 220, 50)
    )

    # 身体 — 主体 (白色到粉色渐变感，用两层椭圆模拟)
    outer = (255, 200, 220, 255)       # 外圈淡粉
    inner = (255, 240, 248, 255)       # 内圈白粉
    draw.ellipse(
        [bx - body_w // 2, by - body_h // 2,
         bx + body_w // 2, by + body_h // 2],
        fill=outer, outline=(255, 170, 200, 255), width=2
    )
    draw.ellipse(
        [bx - body_w // 2 + 6, by - body_h // 2 + 6,
         bx + body_w // 2 - 6, by + body_h // 2 - 6],
        fill=inner
    )

    # 顶部小天线/呆毛
    tuft_x = bx + int(2 * math.sin(shake_x * 0.5))
    draw.line(
        [(bx, by - body_h // 2), (tuft_x, by - body_h // 2 - 12)],
        fill=(255, 170, 200, 255), width=3
    )
    draw.ellipse(
        [tuft_x - 3, by - body_h // 2 - 15, tuft_x + 3, by - body_h // 2 - 9],
        fill=(255, 150, 190, 255)
    )

    # 脸红
    if blush:
        blush_c = (255, 140, 175, 160)
        bw = 14
        bh = 9
        # 左脸
        draw.ellipse(
            [bx - body_w // 3 - bw // 2, by + eye_offset_y + 4,
             bx - body_w // 3 + bw // 2, by + eye_offset_y + 4 + bh],
            fill=blush_c
        )
        # 右脸
        draw.ellipse(
            [bx + body_w // 3 - bw // 2, by + eye_offset_y + 4,
             bx + body_w // 3 + bw // 2, by + eye_offset_y + 4 + bh],
            fill=blush_c
        )

    # 眼睛
    eye_y = by + eye_offset_y - 4
    eye_dx = 16

    if blink:
        # 闭眼 — 弯线
        draw.arc(
            [bx - eye_dx - 6, eye_y - 3, bx - eye_dx + 6, eye_y + 5],
            200, 340, fill=(90, 70, 80, 255), width=2
        )
        draw.arc(
            [bx + eye_dx - 6, eye_y - 3, bx + eye_dx + 6, eye_y + 5],
            200, 340, fill=(90, 70, 80, 255), width=2
        )
    else:
        # 睁眼 — 大圆点 + 高光
        draw.ellipse(
            [bx - eye_dx - 5, eye_y - 5, bx - eye_dx + 5, eye_y + 5],
            fill=(70, 60, 65, 255)
        )
        draw.ellipse(
            [bx + eye_dx - 5, eye_y - 5, bx + eye_dx + 5, eye_y + 5],
            fill=(70, 60, 65, 255)
        )
        # 高光
        draw.ellipse(
            [bx - eye_dx - 3, eye_y - 4, bx - eye_dx + 1, eye_y],
            fill=(255, 255, 255, 255)
        )
        draw.ellipse(
            [bx + eye_dx - 3, eye_y - 4, bx + eye_dx + 1, eye_y],
            fill=(255, 255, 255, 255)
        )

    # 嘴巴
    mx = bx
    my = by + eye_offset_y + 8
    if mouth_type == 'smile':
        draw.arc([mx - 8, my - 2, mx + 8, my + 12], 10, 170,
                 fill=(220, 110, 140, 255), width=2)
    elif mouth_type == 'shy':
        # 小波浪嘴
        draw.line(
            [(mx - 6, my), (mx - 2, my - 2), (mx + 2, my + 2), (mx + 6, my)],
            fill=(220, 110, 140, 255), width=2
        )
    elif mouth_type == 'happy':
        # 大笑嘴
        draw.arc([mx - 10, my - 4, mx + 10, my + 14], 10, 170,
                 fill=(220, 110, 140, 255), width=3)
        # 舌头
        draw.ellipse(
            [mx - 3, my + 6, mx + 3, my + 12],
            fill=(255, 160, 180, 255)
        )


def draw_heart(draw, cx, cy, size=8, color=(255, 100, 150, 255)):
    """画一个小爱心"""
    r = size // 2
    # 两个圆 + 三角形组合
    draw.ellipse(
        [cx - r, cy - r // 2, cx, cy + r // 2],
        fill=color
    )
    draw.ellipse(
        [cx, cy - r // 2, cx + r, cy + r // 2],
        fill=color
    )
    draw.polygon(
        [(cx - r + 1, cy + 1), (cx + r - 1, cy + 1), (cx, cy + r + 1)],
        fill=color
    )


def draw_star(draw, cx, cy, size=6, color=(255, 220, 100, 255)):
    """画一个五角星"""
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = size if i % 2 == 0 else size * 0.4
        points.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
    draw.polygon(points, fill=color)


def draw_note(draw, cx, cy, color=(150, 120, 255, 255)):
    """画一个音符"""
    # 音符头
    draw.ellipse([cx - 4, cy - 2, cx + 4, cy + 6], fill=color)
    # 音符杆
    draw.line([(cx + 3, cy - 2), (cx + 3, cy - 12)], fill=color, width=2)
    # 音符旗
    draw.line([(cx + 3, cy - 12), (cx + 8, cy - 10)], fill=color, width=2)


# ──────────────────────────────────────────────
# idle.gif — 呼吸 + 偶尔眨眼
# ──────────────────────────────────────────────
def gen_idle():
    frames = []
    total = 24
    for i in range(total):
        canvas = new_canvas()
        draw = ImageDraw.Draw(canvas)

        # 呼吸缩放: sin 波动
        t = i / total
        scale = 1.0 + 0.04 * math.sin(t * 2 * math.pi)
        # 呼吸时身体轻微上下浮动
        bob = int(2 * math.sin(t * 2 * math.pi))

        # 眨眼: 在 3/4 周期处眨一次
        blink = (i >= 17 and i <= 19)

        draw_dango(draw, WIDTH // 2, HEIGHT // 2 + bob, scale=scale,
                   blink=blink, eye_offset_y=0, mouth_type='smile')

        frames.append(canvas)

    save_transparent_gif(frames, 'assets/idle.gif', duration=80)
    print("  ✓ idle.gif")


# ──────────────────────────────────────────────
# jump.gif — 蹦跳 + 头顶星星/音符
# ──────────────────────────────────────────────
def gen_jump():
    frames = []
    total = 16
    for i in range(total):
        canvas = new_canvas()
        draw = ImageDraw.Draw(canvas)

        t = i / total
        # 抛物线跳跃: y = -4h * t * (t - 1)
        jump_h = 40
        dy = int(-4 * jump_h * t * (t - 1))
        # 身体在跳跃时微微缩放
        scale = 1.0 + 0.08 * (1 - abs(2 * t - 1))

        cy = HEIGHT // 2 + dy - 10

        draw_dango(draw, WIDTH // 2, cy, scale=scale,
                   blink=False, mouth_type='happy')

        # 头顶星星/音符 — 随帧旋转出现
        star_y = cy - 55
        angle_phase = t * 2 * math.pi

        # 三颗星，错开角度
        for k in range(3):
            ang = angle_phase + k * 2.094  # 120°
            sx = WIDTH // 2 + int(22 * math.cos(ang))
            sy = star_y + int(8 * math.sin(ang * 2))
            sz = 5 + k
            draw_star(draw, sx, sy, size=sz)

        # 音符
        if i % 4 < 2:
            draw_note(draw, WIDTH // 2 + 30, star_y + 5)
        if i % 4 >= 2:
            draw_note(draw, WIDTH // 2 - 35, star_y - 3)

        frames.append(canvas)

    save_transparent_gif(frames, 'assets/jump.gif', duration=60)
    print("  ✓ jump.gif")


# ──────────────────────────────────────────────
# love.gif — 脸红摇晃 + 漂浮爱心
# ──────────────────────────────────────────────
def gen_love():
    frames = []
    total = 24
    # 预生成几颗爱心的运动轨迹
    num_hearts = 5
    heart_trails = []
    for k in range(num_hearts):
        start_frame = k * (total // num_hearts)
        x_base = WIDTH // 2 + (k - 2) * 28
        x_offset = (k % 2) * 10 - 5
        heart_trails.append({
            'start': start_frame,
            'x': x_base + x_offset,
            'speed': 1.0 + 0.3 * k,
            'size': 7 + (k % 3) * 2,
        })

    for i in range(total):
        canvas = new_canvas()
        draw = ImageDraw.Draw(canvas)

        t = i / total
        # 摇晃
        shake_x = int(6 * math.sin(t * 2 * math.pi * 2))
        # 轻微缩放
        scale = 1.0 + 0.03 * math.sin(t * 2 * math.pi)

        draw_dango(draw, WIDTH // 2, HEIGHT // 2,
                   scale=scale, blink=(i == 12), blush=True,
                   shake_x=shake_x, mouth_type='shy')

        # 漂浮爱心
        for trail in heart_trails:
            elapsed = i - trail['start']
            if elapsed < 0:
                elapsed += total
            progress = elapsed / total
            hy = HEIGHT // 2 + 30 - int(70 * progress)
            hx = trail['x'] + int(8 * math.sin(progress * 2 * math.pi))
            alpha = int(255 * (1 - progress * 0.5))
            color = (255, 100 + (trail['size'] % 3) * 20, 150, alpha)
            draw_heart(draw, hx, hy, size=trail['size'], color=color)

        frames.append(canvas)

    save_transparent_gif(frames, 'assets/love.gif', duration=70)
    print("  ✓ love.gif")


# ──────────────────────────────────────────────
# heart.ico — 像素爱心图标
# ──────────────────────────────────────────────
def gen_heart_ico():
    """生成像素风粉红爱心图标 (多尺寸 ICO)"""
    sizes = [16, 32, 48, 64]
    images = []

    for sz in sizes:
        img = Image.new('RGBA', (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 心形像素图案 — 按比例缩放
        # 使用 16x16 基础图案
        pattern = [
            "  XX   XX  ",
            " XXXX XXXX ",
            "XXXXXXXXXXX",
            "XXXXXXXXXXX",
            "XXXXXXXXXXX",
            "XXXXXXXXXXX",
            " XXXXXXXXX ",
            "  XXXXXXX  ",
            "   XXXXX   ",
            "    XXX    ",
            "     X     ",
        ]
        pw = len(pattern[0])
        ph = len(pattern)
        cell = sz // max(pw, ph)
        offset_x = (sz - pw * cell) // 2
        offset_y = (sz - ph * cell) // 2 + cell // 2

        # 颜色渐变 — 从亮粉到深粉
        for py, row in enumerate(pattern):
            for px, ch in enumerate(row):
                if ch == 'X':
                    x = offset_x + px * cell
                    y = offset_y + py * cell
                    # 上半部分更亮，下半部分更深
                    brightness = 1.0 - (py / ph) * 0.3
                    r = int(255 * brightness)
                    g = int(120 * brightness)
                    b = int(160 * brightness)
                    draw.rectangle(
                        [x, y, x + cell - 1, y + cell - 1],
                        fill=(r, g, b, 255)
                    )

        # 添加高光
        hl_size = max(1, cell)
        if sz >= 32:
            draw.rectangle(
                [offset_x + 2 * cell, offset_y + 2 * cell,
                 offset_x + 2 * cell + hl_size - 1,
                 offset_y + 2 * cell + hl_size - 1],
                fill=(255, 200, 220, 255)
            )

        images.append(img)

    # 保存为 ICO (第一张作为主图)
    images[1].save(  # 32x32 作为主图
        'assets/heart.ico',
        format='ICO',
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
        append_images=[images[0], images[2], images[3]]
    )
    print("  ✓ heart.ico")


# ──────────────────────────────────────────────
# GIF 透明保存
# ──────────────────────────────────────────────
def save_transparent_gif(frames, filename, duration=80):
    """
    将 RGBA 帧列表保存为透明 GIF。
    使用 palette 模式，index 0 = 透明色。
    """
    p_frames = []
    for frame in frames:
        rgba = frame.convert('RGBA')
        # 创建 P 模式图像，填充 index 0（透明）
        p = Image.new('P', rgba.size, 0)
        # 量化 RGB 部分
        rgb = rgba.convert('RGB')
        quantized = rgb.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
        # 用 alpha 作为 mask 粘贴
        alpha = rgba.split()[3]
        p.paste(quantized, (0, 0), alpha)
        p_frames.append(p)

    p_frames[0].save(
        filename,
        save_all=True,
        append_images=p_frames[1:],
        duration=duration,
        loop=0,
        disposal=2,
        transparency=0
    )


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs('assets', exist_ok=True)
    print("正在生成桌宠素材...")
    gen_idle()
    gen_jump()
    gen_love()
    gen_heart_ico()
    print("\n✅ 所有素材已生成到 assets/ 目录")

    # 验证文件
    for f in ['idle.gif', 'jump.gif', 'love.gif', 'heart.ico']:
        path = os.path.join('assets', f)
        size = os.path.getsize(path)
        print(f"  {f}: {size} bytes")
