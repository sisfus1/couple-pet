# 💖 想念桌宠 (Couple Pet)

情侣双向互动桌宠：Windows 桌面宠物 ⇄ iPhone 全屏互动网页，**免服务器、免后端**。

她点一下桌宠 → 你的 iPhone 收到 Bark 推送 → 点开网页回一句 → 她的桌宠立刻冒出爱心和气泡。

---

## 📁 项目结构

```
couple-pet/
├── pet.py                # Windows 桌宠客户端 (PyQt6)
├── generate_assets.py    # 素材自动生成脚本 (Pillow)
├── web/index.html        # 手机端全屏互动页 (单文件)
├── index.html            # 同上（GitHub Pages 根目录入口）
├── assets/
│   ├── idle.gif          # 待机：呼吸 + 眨眼
│   ├── jump.gif          # 蹦跳：星星 + 音符
│   ├── love.gif          # 心动：脸红 + 漂浮爱心
│   └── heart.ico         # 托盘/EXE 图标
└── dist/想念桌宠.exe      # 打包成品（单文件，双击即用）
```

## 🔗 通信机制

| 方向 | 通道 | 说明 |
|---|---|---|
| 她 → 你 | **Bark** HTTP GET | 点击桌宠触发推送，附带 `url` 参数跳转 H5 |
| 你 → 她 | **ntfy.sh** HTTP POST/流式 | H5 页面 POST，桌宠 `QThread` 长连接毫秒级接收 |

两端共用同一个 `SECRET_TOPIC`，**不需要任何服务器**。

---

## ⚙️ 配置

程序首次运行会在 **EXE 同级目录**自动生成 `config.json`：

```json
{
  "BARK_KEY": "你的BarkKey",
  "H5_URL": "https://sisfus1.github.io/couple-pet/",
  "SECRET_TOPIC": "couple_pet_zhuqi_2026_8a3f7b2e9c",
  "BOYFRIEND_NAME": "猪猪"
}
```

改配置**只需编辑 `config.json`**，无需重新打包。
若想改默认值（发给别人时用），编辑 `pet.py` 顶部的 `DEFAULT_*` 常量。

> ⚠️ `SECRET_TOPIC` 必须和 `web/index.html` 里的 `SECRET_TOPIC` 完全一致。
> 它相当于频道密码，公开后会被人发垃圾消息，建议定期更换。

### 获取 Bark Key
iPhone 装 [Bark](https://bark.day.app/) → 打开 App → 首页那串字符即 Key。

---

## 🚀 使用

1. 把 `dist/想念桌宠.exe` 发给她，双击运行
2. 右下角出现粉色团子，托盘有爱心图标
3. **左键点桌宠** → 你手机收到推送（5 秒防连点冷却，动画照常播放）
4. **拖拽**（位移 ≥ 5px）只是移动位置，不会误触发推送
5. **右键 / 托盘菜单**：💌 发悄悄话 · 🚀 开机自启 · ❌ 退出
6. 你在手机上回一句 → 她的桌宠播放 5 秒爱心动画 + 8 秒气泡

---

## 🔨 重新构建

```bash
pip install PyQt6 requests Pillow pyinstaller

python generate_assets.py            # 重新生成素材（含自动校验）

pyinstaller --noconfirm --onefile --windowed \
  --icon=assets/heart.ico \
  --add-data "assets;assets" \
  --name "想念桌宠" pet.py
```

产物：`dist/想念桌宠.exe`（约 43MB）

---

## 🕳️ 踩坑记录

**透明 GIF 会变灰度** — 用 `img.paste(quantized, alpha_mask)` 的方式给 GIF 加透明是错的：
那样只搬运了调色板**索引**，没有搬运**调色板本身**，成品所有颜色会塌缩成灰阶，
屏幕上只剩一圈黑色轮廓（桌宠看起来"消失"了）。

正确做法见 `generate_assets.py::save_transparent_gif`：
1. 所有帧拼成一张长图，**统一量化出唯一的全局调色板**（GIF 只有一张全局调色板，
   否则 Pillow 只采用第 1 帧的调色板，后续帧颜色全错）
2. 把 index 0 固定留给透明位，其余索引整体 +1
3. 用 alpha 掩码把透明像素打回 index 0
4. 保存时带 `transparency=0, disposal=2`

`generate_assets.py` 内置 `verify_gif()`，生成后会直接统计彩色/粉色像素数，
若为灰阶会输出 ❌，避免再打包出坏素材。
