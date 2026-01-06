import sys
import os
from google import genai
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QLineEdit, QPushButton, QLabel, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# ================= 配置区域 (已根据你的要求修改) =================

# 1. 设置代理 (这是你提供的端口)
PROXY_URL = "http://127.0.0.1:11304"
os.environ["http_proxy"] = PROXY_URL
os.environ["https_proxy"] = PROXY_URL

# 2. 强制指定模型名称
# 这里严格按照你的要求填写，如果 Google 后台确实有这个 API，就能调通
MODEL_NAME = "gemini-3-pro-preview"


# =============================================================

class Worker(QThread):
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, api_key, user_input):
        super().__init__()
        self.api_key = api_key
        self.user_input = user_input

    def run(self):
        try:
            # 初始化新版客户端
            client = genai.Client(api_key=self.api_key)

            # 发送请求
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=self.user_input
            )

            if response.text:
                self.finished_signal.emit(response.text)
            else:
                self.finished_signal.emit("模型返回内容为空。")

        except Exception as e:
            error_msg = str(e)
            # 针对性错误提示
            if "404" in error_msg:
                error_msg += f"\n\n【严重提示】: Google 服务器返回 404。\n这意味着 API 名称 '{MODEL_NAME}' 目前尚未对公众开放。\n即便你在网页版看到了这个名字，API 接口可能还没部署。"
            elif "403" in error_msg:
                error_msg += "\n\n【提示】: API Key 权限不足或地区受限。"

            self.error_signal.emit(error_msg)


class Gemini3Client(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f'Gemini 3 Pro Preview - 专属客户端')
        self.resize(600, 750)
        layout = QVBoxLayout()

        # 顶部提示
        info_label = QLabel(f"Target Model: <b style='color:#d32f2f'>{MODEL_NAME}</b>")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)

        # API Key 输入区域
        api_layout = QHBoxLayout()
        api_label = QLabel("API Key:")
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("在此粘贴你的 Google API Key")
        self.api_input.setEchoMode(QLineEdit.Password)
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_input)
        layout.addLayout(api_layout)

        # 聊天记录
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("font-size: 14px; padding: 10px; background-color: #f5f5f5;")
        layout.addWidget(self.chat_display)

        # 输入框
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("输入指令...")
        self.message_input.setFixedHeight(120)
        layout.addWidget(self.message_input)

        # 发送按钮
        self.send_btn = QPushButton("发送指令")
        self.send_btn.setFixedHeight(45)
        self.send_btn.setStyleSheet("background-color: #0b57d0; color: white; font-weight: bold; font-size: 14px;")
        self.send_btn.clicked.connect(self.send_message)
        layout.addWidget(self.send_btn)

        self.setLayout(layout)

    def send_message(self):
        api_key = self.api_input.text().strip()
        user_text = self.message_input.toPlainText().strip()

        if not api_key:
            QMessageBox.warning(self, "提示", "请输入 API Key")
            return
        if not user_text:
            return

        self.chat_display.append(f"<div style='margin: 10px 0;'><b>You:</b><br>{user_text}</div>")
        self.message_input.clear()
        self.send_btn.setEnabled(False)
        self.send_btn.setText("正在请求 Gemini 3...")

        self.worker = Worker(api_key, user_text)
        self.worker.finished_signal.connect(self.handle_response)
        self.worker.error_signal.connect(self.handle_error)
        self.worker.start()

    def handle_response(self, response_text):
        formatted_text = response_text.replace('\n', '<br>')
        self.chat_display.append(
            f"<div style='margin: 10px 0; color: #004d40;'><b>Gemini 3:</b><br>{formatted_text}</div>")
        self.chat_display.append("<hr>")
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送指令")

    def handle_error(self, error_msg):
        self.chat_display.append(f"<div style='color: red;'><b>调用失败:</b><br>{error_msg}</div>")
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送指令")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Gemini3Client()
    window.show()
    sys.exit(app.exec_())