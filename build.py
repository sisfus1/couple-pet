# -*- coding: utf-8 -*-
"""
一键构建：给指定的人生成单文件桌宠 EXE。

    python build.py init     # 初始化 configs/me.json 和 configs/her.json（自动生成随机收件箱 topic）
    python build.py me       # 构建你自己的 → dist/想念桌宠-me.exe
    python build.py her      # 构建她的     → dist/想念桌宠-her.exe
    python build.py all      # 两个都构建

configs/ 和 _secrets.py 都被 .gitignore 忽略，密钥不会进仓库。
每次构建会把对应配置写成 _secrets.py，由 PyInstaller 编进 EXE，
所以交付出去的单文件 EXE 开箱即用、无需附带 config.json。
"""

import json
import os
import random
import string
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIGS_DIR = os.path.join(BASE, 'configs')
SECRETS_PATH = os.path.join(BASE, '_secrets.py')

H5_URL = "https://sisfus1.github.io/couple-pet/"

PEOPLE = {
    'me':  {'MY_NAME': '猪猪',   'PARTNER_NAME': '大美女'},
    'her': {'MY_NAME': '大美女', 'PARTNER_NAME': '猪猪'},
}

FIELDS = ['PARTNER_BARK_KEY', 'MY_TOPIC', 'H5_URL', 'MY_NAME', 'PARTNER_NAME']


def new_topic():
    """高强度随机 topic —— ntfy 官方：「topic 名就等于密码」"""
    return 'couple_' + ''.join(
        random.choices(string.ascii_lowercase + string.digits, k=28))


def cmd_init():
    os.makedirs(CONFIGS_DIR, exist_ok=True)
    for who, names in PEOPLE.items():
        path = os.path.join(CONFIGS_DIR, f'{who}.json')

        # 已存在则只补缺失字段，不覆盖已填好的密钥/topic
        cfg = {}
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                cfg = json.load(f) or {}

        cfg.setdefault('PARTNER_BARK_KEY', '')
        cfg.setdefault('MY_TOPIC', new_topic())
        cfg.setdefault('H5_URL', H5_URL)
        for k, v in names.items():
            cfg.setdefault(k, v)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)

        bark = cfg['PARTNER_BARK_KEY']
        print(f"  {path}")
        print(f"    收件箱 topic : {cfg['MY_TOPIC']}")
        print(f"    推送目标 key : {bark or '⚠️  还没填！用文本编辑器打开这个文件填上对方的 Bark Key'}")

    print('\n下一步：把对方的 Bark Key 填进 PARTNER_BARK_KEY，然后 python build.py all')


def load_config(who):
    path = os.path.join(CONFIGS_DIR, f'{who}.json')
    if not os.path.exists(path):
        sys.exit(f'❌ 找不到 {path}\n   先运行: python build.py init')
    with open(path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    missing = [k for k in FIELDS if not cfg.get(k)]
    if missing:
        sys.exit(f'❌ {path} 缺少字段: {missing}\n'
                 f'   （PARTNER_BARK_KEY 需要填对方的 Bark Key）')
    return cfg


def write_secrets(cfg):
    """把配置写成 _secrets.py，供 PyInstaller 编进 EXE"""
    with open(SECRETS_PATH, 'w', encoding='utf-8') as f:
        f.write('# 本文件由 build.py 自动生成，已被 .gitignore 忽略，切勿提交\n')
        for k in FIELDS:
            f.write(f'{k} = {json.dumps(cfg[k], ensure_ascii=False)}\n')


def cmd_build(who):
    cfg = load_config(who)
    write_secrets(cfg)

    name = f'想念桌宠-{who}'
    print(f'▶ 正在构建 {name}.exe  (发给「{cfg["PARTNER_NAME"]}」用，我的名字「{cfg["MY_NAME"]}」)')

    subprocess.run([
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm', '--onefile', '--windowed',
        '--icon=assets/heart.ico',
        '--add-data', 'assets;assets',
        '--name', name,
        'pet.py',
    ], cwd=BASE, check=True)

    out = os.path.join(BASE, 'dist', f'{name}.exe')
    size = os.path.getsize(out) / 1024 / 1024
    print(f'✅ {out}  ({size:.1f} MB)')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''

    if cmd == 'init':
        cmd_init()
    elif cmd == 'all':
        for who in PEOPLE:
            cmd_build(who)
    elif cmd in PEOPLE:
        cmd_build(cmd)
    else:
        print(__doc__)
        sys.exit(1)
