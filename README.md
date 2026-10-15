# 💖 想念桌宠 (Couple Pet) — 双向对称版

情侣双向互动桌宠：**两个人各自在电脑上养一只**，点一下就把「我想你」推送到对方手机；
对方点开通知 → 打开网页 → 回一句 → 你的桌宠立刻冒出爱心和气泡。

**免服务器、免后端、免账号。**

---

## 🔗 通信机制

```
        你的电脑 桌宠A                                  她的电脑 桌宠B
            │ 你点一下                                        │ 她点一下
            ├──▶ Bark 推送 ──▶ 她手机                          ├──▶ Bark 推送 ──▶ 你手机
            │     通知自带跳转链接                              │     通知自带跳转链接
            │     H5?reply=<你的收件箱>                         │     H5?reply=<她的收件箱>
            ▼                                                 ▼
    她点通知 → 打开 H5 → 回复                          你点通知 → 打开 H5 → 回复
            │                                                 │
            └──▶ POST ntfy/<你的收件箱> ──▶ 桌宠A 弹气泡         └──▶ POST ntfy/<她的收件箱> ──▶ 桌宠B 弹气泡
```

| 方向 | 通道 | 谁收到 |
|---|---|---|
| 我点桌宠 | **Bark** HTTP GET | 对方**手机**推送（点通知跳转 H5） |
| 对方在 H5 回复 | **ntfy.sh** POST → QThread 长连接 | 我的**桌宠**气泡 + 托盘通知 |

### 为什么收件箱 topic 不会泄露

回复目标写在跳转链接的 `?reply=` 参数里，而这个参数是**你自己的桌宠**生成的。
所以公开的 GitHub Pages 页面里**一个密钥都没有**；两边的 topic 只存在于各自电脑上。

> ntfy 官方明确说「the topic is essentially a password」，所以 topic 用 28 位随机串。

---

## 📁 项目结构

```
couple-pet/
├── pet.py                 # 桌宠客户端 (PyQt6) —— 两人共用同一份代码
├── build.py               # 一键构建：给指定的人打 exe
├── generate_assets.py     # 素材自动生成 (Pillow，含产物自检)
├── configs/               # 两份配置 (已 gitignore，含 Bark Key)
│   ├── me.json
│   └── her.json
├── web/index.html         # 手机端互动页（单文件，不含任何密钥）
├── index.html             # 同上（GitHub Pages 根目录入口）
├── assets/                # idle.gif / jump.gif / love.gif / heart.ico
└── dist/                  # 构建产物（已 gitignore）
```

---

## 🚀 快速开始

### 1. 初始化配置

```bash
python build.py init
```

生成 `configs/me.json` 和 `configs/her.json`，各自带一个随机收件箱 topic。

### 2. 填入双方的 Bark Key

```jsonc
// configs/me.json  —— 你自己电脑上的桌宠
{
  "PARTNER_BARK_KEY": "她的BarkKey",        // 我点桌宠 → 推给她的手机
  "MY_TOPIC": "couple_xxxxxxxxxxxx",        // 我的收件箱（她的回复进这里）
  "H5_URL": "https://sisfus1.github.io/couple-pet/",
  "MY_NAME": "猪猪",                         // 通知里显示"谁想你啦"
  "PARTNER_NAME": "大美女"                    // 气泡里显示"发给谁/谁发来"
}

// configs/her.json —— 她电脑上的桌宠（MY_NAME 与 PARTNER_NAME 对调）
{
  "PARTNER_BARK_KEY": "你的BarkKey",
  "MY_TOPIC": "couple_yyyyyyyyyyyy",
  ...
}
```

- **对方 iPhone 装 [Bark](https://bark.day.app/) → 打开 App → 首页那串字符就是 Key**，互相交换一下
- 昵称按实际改，改完重跑构建即可

### 3. 构建

```bash
python build.py all     # 或 python build.py me / her
```

产出：
- `dist/想念桌宠-me.exe` → 你自己用
- `dist/想念桌宠-her.exe` → 发给她，双击即用（配置已编进 EXE，**无需附带 config.json**）

### 4. 使用

| 操作 | 效果 |
|---|---|
| **左键点桌宠** | 播放蹦跳动画 + 推送到对方手机（5 秒防连点冷却，动画照常播放） |
| **拖拽**（位移 ≥ 5px） | 只移动位置，不会误触发推送 |
| **右键 / 托盘菜单** | 💌 发句悄悄话（自定义内容直推对方手机）· 🚀 开机自启 · ❌ 退出 |
| **收到对方回复** | 桌宠播放 5 秒爱心动画 + 头顶气泡 8 秒 + 托盘通知 |

---

## 🔨 重新生成素材

```bash
python generate_assets.py    # 生成 3 个透明 GIF + ICO，并自动校验
```

---

## 🕳️ 踩坑记录（都是实测踩出来的）

### 1. 透明 GIF 会塌缩成灰阶

用 `img.paste(quantized, alpha_mask)` 给 GIF 加透明是错的：只搬运了调色板**索引**，
没搬运**调色板本身**，成品所有颜色变成灰阶，屏幕上只剩一圈黑轮廓（桌宠"消失"）。

正确做法（见 `generate_assets.py::save_transparent_gif`）：
1. 所有帧拼成一张长图，**统一量化出唯一的全局调色板**（GIF 只有一张全局调色板，
   否则 Pillow 只采用第 1 帧的，后续帧颜色全错）
2. index 0 固定留给透明位，其余索引整体 +1
3. alpha 掩码把透明像素打回 index 0
4. 保存带 `transparency=0, disposal=2`

生成脚本内置 `verify_gif()`，灰阶会直接报 ❌。

### 2. 气泡放在窗口外 → 被 Qt 裁剪，永远看不见

气泡原本是桌宠窗口的**子控件**，定位在窗口正上方（`y = -bh-8`）。
Qt 会把子控件裁剪在父窗口矩形内，窗口外那部分根本不绘制 —— 实测像素变化为 0。

**必须做成独立顶层窗口**（无父控件 + `ToolTip` 标志 + `WindowTransparentForInput` 鼠标穿透），
用全局坐标定位；拖动桌宠时在 `moveEvent` 里跟随。

### 3. 透明顶层窗口上，QLabel 不画样式表背景

改成顶层窗口后气泡只剩文字、没有底色。QLabel 不绘制样式表里的 `background`。
**要在 `paintEvent` 里用 `QPainter.drawRoundedRect` 自己画**圆角底色 + 描边。

### 4. 密钥绝不能进源码

真实 Bark Key 一旦 `git add` 到 **public** 仓库就是永久泄露（历史 commit 里一直能读到，
删掉再提交也没用，唯一补救是轮换密钥）。

本项目做法：密钥放 `configs/*.json` 和 `_secrets.py`（**都已 gitignore**），
由 `build.py` 打包时注入 EXE。提交前自检：

```bash
git add -A --dry-run | grep -i -E "secret|configs"   # 必须为空
```

### 5. Windows / git-bash 环境

- 重新打包前**必须先杀进程**，否则 `rm -rf dist` 报 `Device or resource busy`
- git-bash 下 `taskkill //F` 参数会被 MSYS 改写，用 python `subprocess` 代替
- 中文进程名用 `tasklist /FI "IMAGENAME eq 中文.exe"` 会因编码不匹配而**误报"未运行"**
  （曾据此误判程序崩溃），改用 python 读 `tasklist /FO CSV` + `encoding='gbk'`
