import csv
import os
import sys
import random
import string
import math
import base64
import hashlib
import secrets
import json
import http.client
import urllib.parse
from datetime import datetime, timedelta

import requests
# Crypto 库依赖
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QFrame, QGraphicsDropShadowEffect, QAbstractItemView,
                             QDialog, QDialogButtonBox, QFormLayout, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QPointF, QRect, QSize
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QPen, QFont, QBrush, QRadialGradient, QIcon, QColorConstants, \
    QFontDatabase, QCursor

# ================= 配置区域 (HACKER THEME) =================
THEME_BG = QColor(0, 0, 0)
THEME_PRIMARY = QColor(0, 255, 65)  # 黑客绿
THEME_SECONDARY = QColor(0, 243, 255)  # 赛博青
THEME_ALERT = QColor(255, 0, 85)  # 故障红
THEME_GLASS = QColor(0, 20, 0, 150)

FONT_FAMILY = "Consolas"

# API 配置
API_HOST = "yunbaoymgf.chat"
API_USER_ID = '129676'
API_AUTH_TOKEN = 'pD9xPhBvzuIISaKBdOfNIpjMzUSf'


# ================= 统一的API请求头 =================
def get_api_headers():
    """返回统一的API请求头"""
    return {
        'new-api-user': API_USER_ID,
        'Authorization': f'Bearer {API_AUTH_TOKEN}',
        'content-type': 'application/json'
    }


# ================= 加密管理类 =================
class CardKeyEncryption:
    def __init__(self, secret_key=None):
        self.seed = "yunmangongfang_2024_secret"
        if secret_key:
            self.secret_key = secret_key
        else:
            self.secret_key = self._generate_fixed_key()
        self.bs = AES.block_size

    def _generate_fixed_key(self):
        return hashlib.sha256(self.seed.encode()).digest()

    def encrypt_api_key(self, real_api_key):
        try:
            iv = secrets.token_bytes(16)
            cipher = AES.new(self.secret_key, AES.MODE_CBC, iv)
            encrypted = cipher.encrypt(pad(real_api_key.encode('utf-8'), self.bs))
            combined = iv + encrypted
            encrypted_b64 = base64.urlsafe_b64encode(combined).decode('utf-8')
            return f"ymgfjc-{encrypted_b64}"
        except Exception as e:
            print(f"加密失败: {e}")
            return None


card_encryptor = CardKeyEncryption()


# ================= 新增卡密对话框 =================
class AddCardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TERMINAL // ADD_TOKEN")
        self.setFixedSize(600, 580)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #050505;
                border: 2px solid {THEME_PRIMARY.name()};
            }}
            QLabel {{
                color: {THEME_PRIMARY.name()};
                font-family: '{FONT_FAMILY}';
            }}
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # 标题
        title = QLabel(">>> INITIATE NEW TOKEN GENERATION")
        title.setStyleSheet(f"""
            QLabel {{
                color: {THEME_SECONDARY.name()};
                font-family: '{FONT_FAMILY}';
                font-size: 18px;
                font-weight: bold;
                border-bottom: 1px dashed {THEME_SECONDARY.name()};
                padding-bottom: 10px;
            }}
        """)
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(20)

        label_style = f"QLabel {{ color: #888; font-size: 12px; font-family: '{FONT_FAMILY}'; font-weight: bold; }}"

        self.token_name_input = QLineEdit()
        self.token_name_input.setPlaceholderText("_Enter token name...")
        self.token_name_input.setStyleSheet(self._input_style(color_hex="#ffff00"))
        form_layout.addRow(QLabel("NAME_TAG:", styleSheet=label_style), self.token_name_input)

        api_btn_layout = QHBoxLayout()
        self.api_create_btn = QPushButton("[ EXECUTE REMOTE GENERATION ]")
        self.api_create_btn.setCursor(Qt.PointingHandCursor)
        self.api_create_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #000; color: {THEME_PRIMARY.name()};
                border: 1px solid {THEME_PRIMARY.name()};
                padding: 8px 15px; font-family: '{FONT_FAMILY}'; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {THEME_PRIMARY.name()}; color: #000; }}
            QPushButton:pressed {{ background-color: #fff; }}
        """)
        self.api_create_btn.clicked.connect(self.create_remote_token)
        api_btn_layout.addStretch()
        api_btn_layout.addWidget(self.api_create_btn)
        form_layout.addRow("", api_btn_layout)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #333; border-top: 1px dashed #333;")
        form_layout.addRow(line)

        self.token_id_input = QLineEdit()
        self.token_id_input.setPlaceholderText("AUTO_FETCH or MANUAL")
        self.token_id_input.setStyleSheet(self._input_style(color_hex="#ffffff"))
        form_layout.addRow(QLabel("TOKEN_ID:", styleSheet=label_style), self.token_id_input)

        self.original_card_input = QLineEdit()
        self.original_card_input.setPlaceholderText("INPUT_SECRET_KEY")
        self.original_card_input.setStyleSheet(self._input_style())
        self.original_card_input.textChanged.connect(self.encrypt_api_key)
        form_layout.addRow(QLabel("RAW_KEY:", styleSheet=label_style), self.original_card_input)

        self.encrypted_card_input = QLineEdit()
        self.encrypted_card_input.setPlaceholderText("WAITING_FOR_ENCRYPTION...")
        self.encrypted_card_input.setReadOnly(True)
        self.encrypted_card_input.setStyleSheet(self._input_style(readonly=True))
        form_layout.addRow(QLabel("ENC_HASH:", styleSheet=label_style), self.encrypted_card_input)

        self.amount_input = QLineEdit("399")
        self.amount_input.setStyleSheet(self._input_style(color_hex=THEME_ALERT.name()))
        form_layout.addRow(QLabel("VALUE(CNY):", styleSheet=label_style), self.amount_input)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        # Cancel Btn
        self.cancel_btn = QPushButton("ABORT")
        self.cancel_btn.setStyleSheet(f"""
             QPushButton {{ background-color: #000; color: #666; border: 1px solid #666; padding: 12px 30px; font-family: '{FONT_FAMILY}'; font-weight: bold; }}
             QPushButton:hover {{ color: #fff; border: 1px solid #fff; }}
        """)
        self.cancel_btn.clicked.connect(self.reject)

        self.ok_btn = QPushButton("CONFIRM_UPLOAD")
        self.ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_SECONDARY.name()};
                color: #000; border: none;
                padding: 12px 30px; font-family: '{FONT_FAMILY}'; font-weight: bold; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: #fff; box-shadow: 0 0 15px {THEME_SECONDARY.name()}; }}
        """)
        self.ok_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        layout.addLayout(btn_layout)

    def _input_style(self, readonly=False, color_hex=None):
        text_color = color_hex if color_hex else (THEME_PRIMARY.name() if not readonly else THEME_SECONDARY.name())
        bg = "#050505" if readonly else "#0a0a0a"
        border = "#222" if readonly else "#333"
        return f"""
            QLineEdit {{
                background-color: {bg}; border: 1px solid {border}; color: {text_color}; 
                font-size: 13px; padding: 8px; font-family: '{FONT_FAMILY}';
            }}
            QLineEdit:focus {{ border: 1px solid {text_color}; background-color: #001100; }}
        """

    def create_remote_token(self):
        token_name = self.token_name_input.text().strip()
        if not token_name:
            QMessageBox.warning(self, "ERR", "MISSING_PARAMETER: token_name")
            return
        api_key = None
        conn = None
        try:
            self.api_create_btn.setText("CONNECTING...")
            self.api_create_btn.setEnabled(False)
            QApplication.processEvents()

            conn = http.client.HTTPSConnection(API_HOST)
            payload = json.dumps({
                "remain_quota": 50000000, "expired_time": -1, "unlimited_quota": False,
                "model_limits_enabled": False, "model_limits": "", "group": "限时特价",
                "mj_image_mode": "default", "mj_custom_proxy": "", "selected_groups": [],
                "name": token_name, "allow_ips": ""
            })
            headers = get_api_headers()
            conn.request("POST", "/api/token/", payload, headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            resp_json = json.loads(data)

            if resp_json.get("success"):
                data_field = resp_json.get("data")
                if isinstance(data_field, str):
                    api_key = data_field
                elif isinstance(data_field, dict) and "key" in data_field:
                    api_key = data_field["key"]
                elif "key" in resp_json:
                    api_key = resp_json["key"]

            if not api_key:
                QMessageBox.warning(self, "API_FAIL", f"Response: {data}")
                return

            self.original_card_input.setText(api_key.strip())

            params = urllib.parse.urlencode({'keyword': token_name})
            conn.request("GET", f"/api/token/?{params}", "", headers)
            res_query = conn.getresponse()
            query_json = json.loads(res_query.read().decode("utf-8"))
            token_id = None
            if query_json.get("success") and "data" in query_json:
                items = query_json["data"].get("items", []) if isinstance(query_json["data"], dict) else query_json[
                    "data"]
                for item in items:
                    if item.get("key") == api_key or (item.get("name") == token_name and not token_id):
                        token_id = item.get("id")
                        break
            if token_id: self.token_id_input.setText(str(token_id))
        except Exception as e:
            QMessageBox.critical(self, "SYS_ERR", f"{str(e)}")
        finally:
            if conn: conn.close()
            self.api_create_btn.setText("[ EXECUTE REMOTE GENERATION ]")
            self.api_create_btn.setEnabled(True)

    def encrypt_api_key(self):
        key = self.original_card_input.text().strip()
        if not key:
            self.encrypted_card_input.clear()
            return
        enc = card_encryptor.encrypt_api_key(key)
        if enc: self.encrypted_card_input.setText(enc)

    def get_card_data(self):
        return {
            'token_id': self.token_id_input.text().strip(),
            'original_key': self.original_card_input.text().strip(),
            'encrypted_key': self.encrypted_card_input.text().strip(),
            'amount': self.amount_input.text().strip()
        }


# ================= UI组件 (特效增强) =================
class NeonEffect(QGraphicsDropShadowEffect):
    def __init__(self, color, blur_radius=25):
        super().__init__()
        self.setBlurRadius(blur_radius)
        self.setColor(color)
        self.setOffset(0, 0)


class CyberButton(QPushButton):
    def __init__(self, text, color=THEME_PRIMARY, parent=None):
        super().__init__(text, parent)
        self.color = color
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        self.setFont(QFont(FONT_FAMILY, 10, QFont.Bold))
        self.update_style(False)
        self.shadow = NeonEffect(self.color, 10)
        self.setGraphicsEffect(self.shadow)

    def update_style(self, hover):
        c_hex = self.color.name()
        bg = c_hex if hover else "rgba(0,0,0,0.5)"
        fg = "#000" if hover else c_hex
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg}; color: {fg}; border: 1px solid {c_hex}; 
                border-radius: 2px; padding: 0 10px; font-family: '{FONT_FAMILY}';
            }}
        """)

    def enterEvent(self, event):
        self.update_style(True)
        self.shadow.setBlurRadius(30)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update_style(False)
        self.shadow.setBlurRadius(10)
        super().leaveEvent(event)


# ================= 炫酷窗口控制按钮 (新增) =================
class WindowCtrlButton(QPushButton):
    def __init__(self, text, color, hover_color, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(50, 35)
        self.setCursor(Qt.PointingHandCursor)
        self.base_color = color
        self.hover_color = hover_color
        self.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))

        # 初始样式
        self.setStyleSheet(self._get_style(False))

        # 初始特效
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(0)
        self.shadow.setColor(self.hover_color)
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)

    def _get_style(self, hover):
        if hover:
            return f"""
                QPushButton {{
                    background-color: {self.hover_color.name()};
                    color: #000;
                    border: 1px solid {self.hover_color.name()};
                    border-bottom: 3px solid {self.hover_color.name()};
                    font-weight: 900;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: rgba(0,0,0,0.3);
                    color: {self.base_color.name()};
                    border: 1px solid #333;
                    border-bottom: 1px solid {self.base_color.name()};
                }}
            """

    def enterEvent(self, event):
        self.setStyleSheet(self._get_style(True))
        self.shadow.setBlurRadius(30)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self._get_style(False))
        self.shadow.setBlurRadius(0)
        super().leaveEvent(event)


class StatusBadge(QLabel):
    def __init__(self, text, status_type="normal"):
        super().__init__(text)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(90, 24)
        if status_type == "active":
            color, bg, border = "#000", "#00ff41", "#00ff41"
        elif status_type == "used":
            color, bg, border = "#ff0055", "#000", "#ff0055"
        elif status_type == "expired":
            color, bg, border = "#666", "#000", "#666"
        else:
            color, bg, border = "#00f3ff", "rgba(0, 243, 255, 0.1)", "#00f3ff"
        self.setStyleSheet(
            f"QLabel {{ color: {color}; background-color: {bg}; border: 1px solid {border}; font-family: '{FONT_FAMILY}'; font-weight: bold; font-size: 11px; }}")


class MatrixRainBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_rain)
        self.timer.start(40)
        self.font_size = 14
        self.cols = 0
        self.drops = []
        self.chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ@#$%^&*"

    def resizeEvent(self, event):
        self.cols = int(self.width() / self.font_size)
        self.drops = [random.randint(-50, 0) for _ in range(self.cols)]
        super().resizeEvent(event)

    def update_rain(self):
        for i in range(len(self.drops)):
            self.drops[i] += 1
            if self.drops[i] * self.font_size > self.height() and random.random() > 0.975:
                self.drops[i] = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), THEME_BG)
        font = QFont(FONT_FAMILY, self.font_size)
        font.setBold(True)
        painter.setFont(font)
        for i in range(len(self.drops)):
            x = i * self.font_size
            y = self.drops[i] * self.font_size
            painter.setPen(QColor(200, 255, 200))
            painter.drawText(x, int(y), random.choice(self.chars))
            for j in range(1, 15):
                char_y = y - (j * self.font_size)
                if char_y < 0: break
                alpha = max(0, 255 - (j * 18))
                painter.setPen(QColor(0, 255, 65, alpha))
                painter.drawText(x, int(char_y), random.choice(self.chars))

        scan_pen = QPen(QColor(0, 0, 0, 80))
        scan_pen.setWidth(2)
        painter.setPen(scan_pen)
        for y in range(0, self.height(), 4):
            painter.drawLine(0, y, self.width(), y)


# ================= 主窗口系统 =================
class CyberCardSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YUNWU.AI // ACCESS TERMINAL")
        self.resize(1400, 850)

        # 1. 窗口标志：无边框
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 2. 背景
        self.bg_widget = MatrixRainBackground(self)
        self.setCentralWidget(self.bg_widget)

        # 3. 主布局
        self.main_layout = QVBoxLayout(self.bg_widget)
        self.main_layout.setContentsMargins(25, 35, 25, 25)
        self.main_layout.setSpacing(15)

        # 4. 初始化各个模块
        self.init_header()
        self.init_stats_panel()
        self.init_controls()
        self.init_table()
        self.init_footer()

        # 5. 初始化炫酷窗口按钮 (覆盖在最上层)
        self.init_window_controls()

        # 状态变量
        self.is_maximized_custom = False
        self.old_pos = None
        self.old_size = None

    # === 窗口拖拽逻辑 ===
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if not self.isMaximized() and not self.is_maximized_custom:
                self.move(event.globalPos() - self.drag_pos)
                event.accept()

    # === 顶部炫酷按钮初始化 ===
    def init_window_controls(self):
        self.win_ctrl_container = QWidget(self)
        self.win_ctrl_container.setFixedSize(120, 40)

        layout = QHBoxLayout(self.win_ctrl_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.btn_max = WindowCtrlButton("▣", QColor("#00aaaa"), THEME_SECONDARY)
        self.btn_max.setToolTip("TOGGLE FULLSCREEN")
        self.btn_max.clicked.connect(self.toggle_max_restore)

        self.btn_close = WindowCtrlButton("✕", QColor("#aa0000"), THEME_ALERT)
        self.btn_close.setToolTip("TERMINATE SESSION")
        self.btn_close.clicked.connect(self.close)

        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

    def resizeEvent(self, event):
        if hasattr(self, 'win_ctrl_container'):
            self.win_ctrl_container.move(self.width() - 130, 10)
            self.win_ctrl_container.raise_()
        super().resizeEvent(event)

    def toggle_max_restore(self):
        if self.isMaximized():
            self.showNormal()
            self.btn_max.setText("▣")
        else:
            self.showMaximized()
            self.btn_max.setText("❐")

    def init_header(self):
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 10)

        title = QLabel("SYSTEM_ROOT // KEY_MANAGER")
        title.setFont(QFont("Impact", 28))
        title.setStyleSheet(f"color: {THEME_PRIMARY.name()}; letter-spacing: 3px;")
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(20)
        effect.setColor(THEME_PRIMARY)
        effect.setOffset(0, 0)
        title.setGraphicsEffect(effect)

        subtitle = QLabel("[ v3.0.1_STABLE ]")
        subtitle.setStyleSheet(
            f"color: {THEME_SECONDARY.name()}; font-family: '{FONT_FAMILY}'; margin-left: 10px; margin-bottom: 5px;")
        subtitle.setAlignment(Qt.AlignBottom)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addStretch()

        self.time_lbl = QLabel()
        self.time_lbl.setStyleSheet(
            f"color: #fff; font-size: 16px; font-family: '{FONT_FAMILY}'; font-weight: bold; margin-right: 120px;")
        header_layout.addWidget(self.time_lbl)

        timer = QTimer(self)
        timer.timeout.connect(lambda: self.time_lbl.setText(f"SERVER_TIME: {datetime.now().strftime('%H:%M:%S')}"))
        timer.start(1000)
        self.main_layout.addWidget(header_frame)

    def init_stats_panel(self):
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        panel_configs = [("TOTAL_KEYS", THEME_PRIMARY, "0", "lbl_total_val"),
                         ("TOTAL_VALUE (CNY)", THEME_SECONDARY, "¥ 0.00", "lbl_amount_val"),
                         ("ACTIVE_NODES", THEME_ALERT, "0", "lbl_active_val")]
        for label_text, color, default_val, var_name in panel_configs:
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background-color: rgba(0, 20, 0, 0.6); border: 1px solid {color.name()}; border-left: 5px solid {color.name()}; }}")
            card_layout = QVBoxLayout(card)
            lbl_title = QLabel(label_text)
            lbl_title.setStyleSheet(
                f"color: {color.name()}; font-size: 12px; font-family: '{FONT_FAMILY}'; font-weight: bold;")
            lbl_val = QLabel(default_val)
            lbl_val.setStyleSheet(f"color: white; font-size: 26px; font-family: '{FONT_FAMILY}'; font-weight: bold;")
            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(15)
            glow.setColor(color)
            lbl_val.setGraphicsEffect(glow)
            setattr(self, var_name, lbl_val)
            card_layout.addWidget(lbl_title)
            card_layout.addWidget(lbl_val)
            stats_layout.addWidget(card)
        self.main_layout.addLayout(stats_layout)

    def update_dashboard_stats(self):
        total_count = self.table.rowCount()
        total_amount = 0.0
        active_users = 0

        for row in range(total_count):
            amount_item = self.table.item(row, 3)
            if amount_item:
                try:
                    amount_text = amount_item.text().replace('¥', '').replace(',', '').strip()
                    total_amount += float(amount_text)
                except ValueError:
                    pass

            widget = self.table.cellWidget(row, 4)
            if widget:
                status_lbl = widget.findChild(QLabel)
                if status_lbl:
                    status_text = status_lbl.text()
                    if "USED" in status_text.upper() or "已使用" in status_text:
                        active_users += 1

        self.lbl_total_val.setText(f"{total_count:,}")
        self.lbl_amount_val.setText(f"¥ {total_amount:,.2f}")
        self.lbl_active_val.setText(f"{active_users:,}")

    def init_controls(self):
        control_frame = QFrame()
        control_frame.setFixedHeight(50)
        layout = QHBoxLayout(control_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(">>> SEARCH_QUERY...")
        self.search_input.setFixedWidth(350)
        self.search_input.setFixedHeight(40)
        self.search_input.setStyleSheet(
            f"QLineEdit {{ background-color: #000; border: 1px solid #333; color: {THEME_PRIMARY.name()}; padding-left: 10px; font-family: '{FONT_FAMILY}'; font-size: 14px; }} QLineEdit:focus {{ border: 1px solid {THEME_PRIMARY.name()}; }}")
        self.search_input.returnPressed.connect(self.perform_search)

        btn_search = CyberButton("SEARCH", THEME_PRIMARY)
        btn_search.clicked.connect(self.perform_search)
        btn_gen = CyberButton(" + NEW_KEY ", THEME_SECONDARY)
        btn_gen.clicked.connect(self.show_add_card_dialog)
        self.btn_refresh = CyberButton(" [ REFRESH ] ", QColor("#ffff00"))
        self.btn_refresh.clicked.connect(self.load_data_from_api)
        btn_export = CyberButton("EXPORT_CSV", QColor("#cccccc"))
        btn_export.clicked.connect(self.export_data)
        btn_del = CyberButton("DELETE", THEME_ALERT)
        btn_del.clicked.connect(self.delete_row)

        layout.addWidget(self.search_input)
        layout.addWidget(btn_search)
        layout.addStretch()
        layout.addWidget(btn_gen)
        layout.addWidget(self.btn_refresh)
        layout.addWidget(btn_export)
        layout.addWidget(btn_del)
        self.main_layout.addWidget(control_frame)

    def perform_search(self):
        search_text = self.search_input.text().strip().lower()
        found_count = 0
        for row in range(self.table.rowCount()):
            match = False
            for col in [0, 1, 2]:
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
            if match: found_count += 1
        if search_text and found_count == 0: QMessageBox.information(self, "SEARCH_RESULT", "NO MATCH FOUND.")

    def export_data(self):
        if self.table.rowCount() == 0: return
        file_path, _ = QFileDialog.getSaveFileName(self, "SAVE_DATA", f"DUMP_{datetime.now().strftime('%H%M%S')}.csv",
                                                   "CSV(*.csv)")
        if not file_path: return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
                writer.writerow(headers)
                for row in range(self.table.rowCount()):
                    if self.table.isRowHidden(row): continue
                    row_data = []
                    for col in range(self.table.columnCount()):
                        if col == 4:
                            w = self.table.cellWidget(row, col)
                            t = w.findChild(QLabel).text() if w else ""
                        else:
                            it = self.table.item(row, col)
                            t = it.text() if it else ""
                        row_data.append(t)
                    writer.writerow(row_data)
            QMessageBox.information(self, "DONE", "DATA_EXPORT_SUCCESSFUL")
        except Exception as e:
            QMessageBox.critical(self, "ERR", str(e))

    def load_data_from_api(self):
        self.btn_refresh.setText("DOWNLOADING...")
        self.btn_refresh.setEnabled(False)
        QApplication.processEvents()
        conn = None
        try:
            conn = http.client.HTTPSConnection(API_HOST, timeout=10)
            headers = get_api_headers()
            conn.request("GET", "/api/token/?p=0&size=100", "", headers)
            res = conn.getresponse()
            data = json.loads(res.read().decode("utf-8"))
            if data.get("success"):
                items = data.get("data", {}).get("items", [])
                self.table.setRowCount(0)
                for item in items:
                    self.add_api_row_to_table(item)
                self.update_dashboard_stats()
                QMessageBox.information(self, "SYNC_COMPLETE", f"LOADED {len(items)} RECORDS.")
            else:
                QMessageBox.warning(self, "API_ERR", data.get("message", "Unknown Error"))
        except Exception as e:
            QMessageBox.critical(self, "NET_ERR", f"{str(e)}")
        finally:
            if conn: conn.close()
            self.btn_refresh.setText(" [ REFRESH ] ")
            self.btn_refresh.setEnabled(True)

    def add_api_row_to_table(self, item_data):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 45)
        token_id = str(item_data.get("id", ""))
        original_key = item_data.get("key", "")
        encrypted_key = card_encryptor.encrypt_api_key(original_key) if original_key else ""
        used_quota = item_data.get("used_quota", 0)
        created_ts = item_data.get("created_time", 0)
        created_str = datetime.fromtimestamp(created_ts).strftime("%Y-%m-%d %H:%M") if created_ts else "-"
        expired_ts = item_data.get("expired_time", -1)
        expired_str = "PERMANENT" if expired_ts == -1 else datetime.fromtimestamp(expired_ts).strftime("%Y-%m-%d %H:%M")

        self.table.setItem(row, 0, self.create_item(token_id, "#888"))
        self.table.setItem(row, 1, self.create_item(original_key, THEME_PRIMARY.name()))
        self.table.setItem(row, 2, self.create_item(encrypted_key, THEME_SECONDARY.name()))
        self.table.setItem(row, 3, self.create_item("¥ 399", "#fff", is_bold=True))
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        lbl = StatusBadge("USED", "used") if used_quota > 0 else StatusBadge("ACTIVE", "active")
        layout.addWidget(lbl)
        self.table.setCellWidget(row, 4, container)
        self.table.setItem(row, 5, self.create_item(created_str, "#aaa"))
        self.table.setItem(row, 6, self.create_item(expired_str, "#aaa"))

    def init_table(self):
        self.table = QTableWidget()
        columns = ["ID", "RAW_KEY", "ENCRYPTED_HASH", "VALUE", "STATUS", "CREATED_AT", "EXPIRES_AT"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background-color: transparent; gridline-color: #222; border: 1px solid #333; color: #ddd; font-family: '{FONT_FAMILY}'; font-size: 13px; outline: 0; }}
            QTableWidget::item {{ padding: 5px; border-bottom: 1px solid rgba(0, 255, 65, 0.1); }}
            QTableWidget::item:selected {{ background-color: rgba(0, 255, 65, 0.2); color: #fff; }}
            QHeaderView::section {{ background-color: #0a0a0a; color: {THEME_PRIMARY.name()}; border: none; border-bottom: 2px solid {THEME_PRIMARY.name()}; border-right: 1px solid #222; padding: 8px; font-family: '{FONT_FAMILY}'; font-weight: bold; }}
            QScrollBar:vertical {{ background: #000; width: 10px; }}
            QScrollBar::handle:vertical {{ background: #333; }}
        """)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 120)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.main_layout.addWidget(self.table)

    def init_footer(self):
        footer = QHBoxLayout()
        status = QLabel("> SYSTEM_READY... WAITING_FOR_INPUT_")
        status.setStyleSheet(f"color: #666; font-family: '{FONT_FAMILY}'; font-size: 12px;")
        footer.addWidget(status)
        footer.addStretch()
        progress = QFrame()
        progress.setFixedSize(150, 4)
        progress.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {THEME_PRIMARY.name()}, stop:1 #000);")
        footer.addWidget(progress)
        self.main_layout.addLayout(footer)

    def show_add_card_dialog(self):
        dialog = AddCardDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            card_data = dialog.get_card_data()
            if not card_data['original_key'] and not card_data['encrypted_key']: return
            self.add_card_to_table(card_data)

    def create_item(self, text, color_hex, font_family=FONT_FAMILY, is_bold=False):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(QBrush(QColor(color_hex)))
        font = QFont(font_family, 10)
        if is_bold: font.setBold(True)
        item.setFont(font)
        return item

    def add_card_to_table(self, card_data):
        row = 0
        self.table.insertRow(row)
        self.table.setRowHeight(row, 45)
        created_at = datetime.now()
        expired_at = created_at + timedelta(days=365)
        tid = card_data.get('token_id') or str(random.randint(1000, 9999))
        self.table.setItem(row, 0, self.create_item(tid, "#888"))
        self.table.setItem(row, 1, self.create_item(card_data.get('original_key'), THEME_PRIMARY.name()))
        self.table.setItem(row, 2, self.create_item(card_data.get('encrypted_key'), THEME_SECONDARY.name()))
        self.table.setItem(row, 3, self.create_item(f"¥ {card_data.get('amount', '0')}", "#fff", is_bold=True))
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(StatusBadge("ACTIVE", "active"))
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table.setCellWidget(row, 4, container)
        self.table.setItem(row, 5, self.create_item(created_at.strftime("%Y-%m-%d %H:%M"), "#aaa"))
        self.table.setItem(row, 6, self.create_item(expired_at.strftime("%Y-%m-%d %H:%M"), "#aaa"))
        self.table.scrollToTop()
        self.update_dashboard_stats()

    def delete_row(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "INFO", "请先选择要删除的行")
            return

        token_id = self.table.item(current_row, 0).text()
        token_key = self.table.item(current_row, 1).text() if self.table.item(current_row, 1) else "N/A"

        reply = QMessageBox.question(
            self,
            "CONFIRM_DELETE",
            f"确认删除令牌?\nID: {token_id}\nKey: {token_key[:20]}...",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            print(f"开始删除流程...")
            print(f"令牌ID: {token_id}")

            if token_id and token_id.isdigit():
                print("尝试远程删除...")
                if self.delete_remote_token(token_id):
                    self.table.removeRow(current_row)
                    QMessageBox.information(self, "DELETED", "令牌删除成功")
                    self.update_dashboard_stats()
                else:
                    QMessageBox.warning(self, "DELETE_FAILED", "远程删除失败，请检查控制台输出")
            else:
                print("本地删除（无效的令牌ID）")
                self.table.removeRow(current_row)
                QMessageBox.information(self, "DELETED", "本地记录已删除")
                self.update_dashboard_stats()

    import requests

    def delete_remote_token(self, token_id):
        """删除远程令牌 - 使用requests库自动处理重定向"""
        try:
            url = f"https://{API_HOST}/api/token/{token_id}/"
            headers = get_api_headers()

            print(f"正在删除令牌 ID: {token_id}")
            print(f"请求URL: {url}")
            print(f"请求头: {headers}")

            # 使用requests库，自动处理重定向
            response = requests.delete(url, headers=headers, allow_redirects=True, timeout=10)

            print(f"最终状态码: {response.status_code}")
            print(f"最终URL: {response.url}")
            print(f"响应内容: {response.text}")

            if response.status_code in [200, 204]:
                print("删除成功")
                return True
            elif response.status_code == 404:
                print("令牌不存在或已被删除")
                return True
            else:
                print(f"删除失败，状态码: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"错误详情: {error_data}")
                except:
                    pass
                return False

        except Exception as e:
            print(f"删除请求异常: {e}")
            return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont(FONT_FAMILY)
    font.setPixelSize(12)
    app.setFont(font)
    window = CyberCardSystem()
    window.show()
    sys.exit(app.exec_())