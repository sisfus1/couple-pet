# -*- coding: utf-8 -*-
"""
想念桌宠 — 情侣双向互动 Windows 桌面宠物
依赖: PyQt6, requests
打包: pyinstaller --noconfirm --onefile --windowed --icon=assets/heart.ico --add-data "assets;assets" --name "想念桌宠" pet.py
"""

import sys
import os
import json
import time
import random
import string
import threading
import requests
import winreg

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QSystemTrayIcon, QMenu,
    QLineEdit, QPushButton, QVBoxLayout, QDialog, QMessageBox,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPoint, QRect, QSize
)
from PyQt6.QtGui import (
    QIcon, QMovie, QPainter, QFont, QColor, QAction, QPixmap
)


# ════════════════════════════════════════════════
# 配置常量 (默认回退)
# ════════════════════════════════════════════════

# ★★★ 用户配置区：请修改以下值 ★★★
DEFAULT_BARK_KEY = "FasNSdcSnEgr6pPUF5uDe4"     # ← 已填入你的 Bark Key
DEFAULT_H5_URL = "https://sisfus1.github.io/couple-pet/"  # ← GitHub Pages 地址
DEFAULT_BOYFRIEND_NAME = "猪猪"                    # ← 男朋友的昵称

# 默认 SECRET_TOPIC (与 web/index.html 中保持一致)
DEFAULT_SECRET_TOPIC = "couple_pet_zhuqi_2026_8a3f7b2e9c"

CONFIG_FILE = "config.json"


def generate_random_topic():
    """生成带时间戳的随机 topic"""
    ts = time.strftime("%Y%m%d%H%M%S")
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"couple_pet_zhuqi_{ts}_{rand}"


def load_config():
    """
    加载配置: 优先读取同级目录的 config.json，否则使用默认值。
    若 config.json 不存在，自动生成一个并写入磁盘。
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), CONFIG_FILE)
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # 使用默认配置
    config = {
        "BARK_KEY": DEFAULT_BARK_KEY,
        "H5_URL": DEFAULT_H5_URL,
        "SECRET_TOPIC": DEFAULT_SECRET_TOPIC,
        "BOYFRIEND_NAME": DEFAULT_BOYFRIEND_NAME,
    }

    # 尝试写入 config.json 供用户后续修改
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # 只读环境下忽略

    return config


def resource_path(relative_path):
    """
    兼容开发环境与 PyInstaller 的 sys._MEIPASS 临时解压目录。
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ════════════════════════════════════════════════
# ntfy.sh 流式监听线程
# ════════════════════════════════════════════════

class NtfyListener(QThread):
    """后台流式监听 ntfy.sh 频道，收到消息后通过信号通知主线程"""
    message_received = pyqtSignal(str)

    def __init__(self, topic):
        super().__init__()
        self.topic = topic
        self._running = True
        self._backoff = 1

    def run(self):
        url = f"https://ntfy.sh/{self.topic}/json"
        while self._running:
            try:
                response = requests.get(url, stream=True, timeout=60)
                self._backoff = 1  # 重连成功，重置退避
                for line in response.iter_lines():
                    if not self._running:
                        break
                    if not line:
                        continue
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if data.get("event") == "message":
                            msg = data.get("message", "")
                            self.message_received.emit(msg)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass
            except requests.exceptions.Timeout:
                # 超时是正常的 (长连接保活)，直接重连
                continue
            except Exception:
                if self._running:
                    time.sleep(self._backoff)
                    self._backoff = min(self._backoff * 2, 60)

    def stop(self):
        self._running = False
        self.wait(3000)


# ════════════════════════════════════════════════
# 气泡标签 (圆角半透明)
# ════════════════════════════════════════════════

class BubbleLabel(QLabel):
    """圆角半透明粉色气泡"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 182, 203, 200);
                color: #8b4a5e;
                border-radius: 14px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 500;
                border: 1.5px solid rgba(255, 150, 180, 220);
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.adjustSize()
        self.hide()

    def set_text(self, text):
        self.setText(text)
        self.adjustSize()


# ════════════════════════════════════════════════
# 悄悄话输入对话框
# ════════════════════════════════════════════════

class WhisperDialog(QDialog):
    """轻量可爱的悄悄话输入框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💌 悄悄话")
        self.setFixedSize(360, 180)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #fff0f5, stop:1 #e6e0f8);
                border-radius: 16px;
            }
            QLabel { color: #8b4a5e; font-size: 14px; font-weight: 600; }
            QLineEdit {
                border: 2px solid rgba(255,150,180,0.5);
                border-radius: 12px; padding: 10px 14px;
                font-size: 14px; background: white;
                color: #5a3a4a;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #fd79a8, stop:1 #e84393);
                color: white; border: none; border-radius: 12px;
                padding: 8px 20px; font-size: 14px; font-weight: 600;
            }
            QPushButton:hover { opacity: 0.85; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel("写给她的悄悄话：")
        layout.addWidget(label)

        self.input = QLineEdit()
        self.input.setPlaceholderText("输入想说的话...")
        self.input.returnPressed.connect(self._on_send)
        layout.addWidget(self.input)

        btn = QPushButton("💌 发送")
        btn.clicked.connect(self._on_send)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.text = None

    def _on_send(self):
        self.text = self.input.text().strip()
        if self.text:
            self.accept()


# ════════════════════════════════════════════════
# 主桌宠窗口
# ════════════════════════════════════════════════

class PetWindow(QWidget):

    PET_SIZE = 200

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.bark_key = config.get("BARK_KEY", DEFAULT_BARK_KEY)
        self.h5_url = config.get("H5_URL", DEFAULT_H5_URL)
        self.secret_topic = config.get("SECRET_TOPIC", DEFAULT_SECRET_TOPIC)
        self.bf_name = config.get("BOYFRIEND_NAME", DEFAULT_BOYFRIEND_NAME)

        # 状态
        self._press_pos = QPoint()
        self._is_dragging = False
        self._last_click_time = 0
        self._cooldown = 5  # 秒
        self._current_gif = None

        self._init_ui()
        self._init_tray()
        self._init_listener()

        # 启动后自动播放 idle
        self._play_gif('idle.gif')

    # ─── UI 初始化 ───

    def _init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(self.PET_SIZE, self.PET_SIZE)

        # GIF 显示标签
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, self.PET_SIZE, self.PET_SIZE)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # GIF 动画
        self.movies = {}
        for gif in ['idle.gif', 'jump.gif', 'love.gif']:
            path = resource_path(os.path.join('assets', gif))
            movie = QMovie(path)
            movie.setScaledSize(QSize(self.PET_SIZE, self.PET_SIZE))
            self.movies[gif] = movie

        # 气泡
        self.bubble = BubbleLabel("", self)
        self.bubble.hide()

        # 气泡定时器
        self.bubble_timer = QTimer(self)
        self.bubble_timer.setSingleShot(True)
        self.bubble_timer.timeout.connect(self._hide_bubble)

        # 动画切换定时器 (jump/love 播放结束后切回 idle)
        self.anim_timer = QTimer(self)
        self.anim_timer.setSingleShot(True)
        self.anim_timer.timeout.connect(self._on_anim_end)

        # 默认位置: 右下角
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.PET_SIZE - 30,
                  screen.height() - self.PET_SIZE - 80)

    def _init_tray(self):
        """系统托盘图标"""
        icon_path = resource_path(os.path.join('assets', 'heart.ico'))
        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self)
        self.tray_icon.setToolTip(f"想念桌宠 💖 (来自{self.bf_name})")

        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background: rgba(255, 245, 248, 0.95);
                border: 1px solid rgba(255, 180, 200, 0.5);
                border-radius: 8px; padding: 6px;
            }
            QMenu::item {
                padding: 8px 24px; border-radius: 6px;
                color: #5a3a4a; font-size: 13px;
            }
            QMenu::item:selected {
                background: rgba(255, 182, 203, 0.5);
            }
        """)

        # 悄悄话
        act_whisper = QAction("💌 发句悄悄话给她", tray_menu)
        act_whisper.triggered.connect(self._on_whisper)
        tray_menu.addAction(act_whisper)

        # 开机自启
        self.act_autostart = QAction("🚀 开机自动启动", tray_menu)
        self.act_autostart.setCheckable(True)
        self.act_autostart.setChecked(self._is_autostart_enabled())
        self.act_autostart.triggered.connect(self._toggle_autostart)
        tray_menu.addAction(self.act_autostart)

        tray_menu.addSeparator()

        # 退出
        act_quit = QAction("❌ 休息一下（退出）", tray_menu)
        act_quit.triggered.connect(self._on_quit)
        tray_menu.addAction(act_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _init_listener(self):
        """启动 ntfy 监听线程"""
        self.listener = NtfyListener(self.secret_topic)
        self.listener.message_received.connect(self._on_message_received)
        self.listener.start()

    # ─── GIF 播放 ───

    def _play_gif(self, gif_name):
        """切换播放指定 GIF"""
        # 停止当前
        if self._current_gif:
            self.movies[self._current_gif].stop()

        self._current_gif = gif_name
        movie = self.movies[gif_name]
        self.label.setMovie(movie)
        movie.start()

    def _on_anim_end(self):
        """jump/love 动画结束，切回 idle"""
        self._play_gif('idle.gif')

    # ─── 气泡 ───

    def _show_bubble(self, text, duration_ms=3000):
        """显示气泡在桌宠头顶"""
        self.bubble.set_text(text)
        # 定位气泡: 桌宠正上方
        bw = self.bubble.width()
        bh = self.bubble.height()
        self.bubble.move(
            (self.PET_SIZE - bw) // 2,
            -bh - 8
        )
        self.bubble.show()
        self.bubble.raise_()
        self.bubble_timer.start(duration_ms)

    def _hide_bubble(self):
        self.bubble.hide()

    # ─── 鼠标事件 ───

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._is_dragging = False
        elif event.button() == Qt.MouseButton.RightButton:
            # 右键菜单由托盘处理，这里也弹一次
            pass

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._press_pos
            if delta.manhattanLength() >= 5:
                self._is_dragging = True
                self.move(self.pos() + delta)
                self._press_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._press_pos
            if delta.manhattanLength() < 5:
                # 视为点击
                self._on_pet_clicked()

    def _on_pet_clicked(self):
        """左键点击桌宠 → 发送想念到对方手机"""
        # 播放 jump 动画 (无论是否冷却)
        self._play_gif('jump.gif')
        self.anim_timer.start(2500)

        # 显示气泡
        self._show_bubble(f"正在把想念发给{self.bf_name}... 💌", 2500)

        # 冷却检查
        now = time.time()
        if now - self._last_click_time >= self._cooldown:
            self._last_click_time = now
            # 异步发送 Bark 推送
            threading.Thread(target=self._send_bark, daemon=True).start()

    def _send_bark(self, body=None):
        """通过 Bark 发送推送通知"""
        if self.bark_key == "YOUR_BARK_KEY_HERE":
            return  # 未配置，静默跳过

        title = f"{self.bf_name}想你啦 💖"
        if body is None:
            body = "她刚刚戳了戳桌宠：我想你啦！💖"

        url = f"https://api.day.app/{self.bark_key}"
        params = {
            'title': title,
            'body': body,
            'url': self.h5_url,
            'sound': 'bell',
            'icon': 'https://emojicdn.elk.sh/💖',
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
        except Exception:
            pass

    # ─── 右键菜单 / 悄悄话 ───

    def _on_whisper(self):
        """弹出悄悄话输入框"""
        dlg = WhisperDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.text:
            self._show_bubble(f"💌 悄悄话已发出...", 3000)
            threading.Thread(
                target=self._send_bark,
                args=(f"她悄悄说：{dlg.text}",),
                daemon=True
            ).start()

    # ─── 开机自启 ───

    def _is_autostart_enabled(self):
        """检查注册表是否已设置开机自启"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            winreg.QueryValueEx(key, "想念桌宠")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def _toggle_autostart(self):
        """切换开机自启"""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        if self.act_autostart.isChecked():
            # 设置自启
            exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
            try:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
                winreg.SetValueEx(key, "想念桌宠", 0, winreg.REG_SZ, f'"{exe_path}"')
                winreg.CloseKey(key)
            except Exception as e:
                QMessageBox.warning(self, "提示", f"设置自启失败: {e}")
        else:
            # 取消自启
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
                winreg.DeleteValue(key, "想念桌宠")
                winreg.CloseKey(key)
            except FileNotFoundError:
                pass
            except Exception as e:
                QMessageBox.warning(self, "提示", f"取消自启失败: {e}")

    # ─── 收到消息 ───

    def _on_message_received(self, message):
        """收到来自手机的消息"""
        # 播放 love 动画
        self._play_gif('love.gif')
        self.anim_timer.start(5000)

        # 显示气泡 (8秒)
        self._show_bubble(f"💖 他发来消息：\n『{message}』", 8000)

        # 系统通知
        self.tray_icon.showMessage(
            f"收到来自她的消息 💖",
            message,
            QSystemTrayIcon.MessageIcon.Information,
            5000
        )

    # ─── 退出 ───

    def _on_quit(self):
        self.listener.stop()
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        self.listener.stop()
        self.tray_icon.hide()
        event.accept()


# ════════════════════════════════════════════════
# 入口
# ════════════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出 (托盘保活)

    config = load_config()
    pet = PetWindow(config)
    pet.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
