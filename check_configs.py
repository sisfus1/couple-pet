# -*- coding: utf-8 -*-
"""
校验 configs/me.json 与 configs/her.json 是否正确配对。

    python check_configs.py

只读 configs/ 目录，**本身不含任何密钥**，可以安全入库。
检查项：
  - 两份配置都填齐了字段
  - 两个收件箱 topic 不同（相同会导致自己收到自己发的回复）
  - 两人推送目标 key 不同（相同说明有一边填成了自己的 key，会推给自己）
  - topic 长度足够（太短容易被猜中）
  - H5_URL 一致且是 https
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIGS = ['me', 'her']
FIELDS = ['PARTNER_BARK_KEY', 'MY_TOPIC', 'H5_URL', 'MY_NAME', 'PARTNER_NAME']
MIN_TOPIC_LEN = 20


def load(who):
    path = os.path.join(BASE, 'configs', f'{who}.json')
    if not os.path.exists(path):
        sys.exit(f'❌ 找不到 {path}\n   先运行: python build.py init')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        sys.exit(f'❌ {path} 不是合法 JSON: {e}')


def mask(s):
    """打码显示，避免密钥出现在终端/日志里"""
    if not s:
        return '(空)'
    return s[:4] + '*' * max(0, len(s) - 8) + s[-4:] if len(s) > 12 else '***'


def main():
    cfgs = {who: load(who) for who in CONFIGS}
    failures = []

    print('=== 配置内容（已打码）===')
    for who, cfg in cfgs.items():
        print(f'\n[{who}.json]')
        for k in FIELDS:
            shown = mask(cfg.get(k, '')) if ('KEY' in k or 'TOPIC' in k) else cfg.get(k, '')
            print(f'  {k:18s} = {shown}')

    print('\n=== 校验 ===')

    def check(name, ok, hint=''):
        print(f'  {"✅" if ok else "❌"} {name}' + (f'  → {hint}' if not ok and hint else ''))
        if not ok:
            failures.append(name)

    for who, cfg in cfgs.items():
        missing = [k for k in FIELDS if not cfg.get(k)]
        check(f'{who}.json 字段齐全', not missing, f'缺 {missing}')

    check('两个收件箱 topic 不同',
          cfgs['me']['MY_TOPIC'] != cfgs['her']['MY_TOPIC'],
          '相同会导致自己收到自己的回复，删掉 configs/ 重新 init')
    check('两人推送 key 不同',
          cfgs['me']['PARTNER_BARK_KEY'] != cfgs['her']['PARTNER_BARK_KEY'],
          '相同说明有一边填成了自己的 key，会把推送发给自己')
    check('topic 长度足够',
          min(len(cfgs[w]['MY_TOPIC']) for w in CONFIGS) >= MIN_TOPIC_LEN,
          f'建议 >= {MIN_TOPIC_LEN} 字符，ntfy 官方：「topic 名就等于密码」')
    check('H5_URL 是 https 且两边一致',
          all(cfgs[w]['H5_URL'].startswith('https://') for w in CONFIGS)
          and cfgs['me']['H5_URL'] == cfgs['her']['H5_URL'])
    check('昵称互为对方',
          cfgs['me']['PARTNER_NAME'] == cfgs['her']['MY_NAME']
          and cfgs['her']['PARTNER_NAME'] == cfgs['me']['MY_NAME'],
          '两边昵称对不上，通知里会显示成不认识的名字')

    if failures:
        print(f'\n❌ {len(failures)} 项未通过')
        return 1
    print('\n✅ 全部通过，可以 python build.py all')
    return 0


if __name__ == '__main__':
    sys.exit(main())
