import sys
import json
import http.client
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_token = ""
        self.init_ui()
        self.chat_history = []

    def init_ui(self):
        self.setWindowTitle("小猪AI聊天助手")
        self.setGeometry(100, 100, 800, 600)

        # 设置主窗口背景色
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # 标题
        title_label = QLabel("🐷 小猪AI聊天助手")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #ff6b6b;
            padding: 10px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # API密钥输入区域
        api_layout = QHBoxLayout()
        api_label = QLabel("API Token:")
        api_label.setStyleSheet("font-weight: bold;")
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("请输入您的API Token")
        self.token_input.setEchoMode(QLineEdit.Password)
        save_token_btn = QPushButton("保存")
        save_token_btn.clicked.connect(self.save_token)

        api_layout.addWidget(api_label)
        api_layout.addWidget(self.token_input, 1)
        api_layout.addWidget(save_token_btn)
        main_layout.addLayout(api_layout)

        # 聊天历史显示区域
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(400)
        self.chat_display.setStyleSheet("""
            font-size: 14px;
            line-height: 1.5;
        """)
        main_layout.addWidget(self.chat_display)

        # 输入区域
        input_layout = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        self.message_input.setPlaceholderText("请输入您的问题...")

        send_button = QPushButton("发送")
        send_button.clicked.connect(self.send_message)
        send_button.setFixedWidth(80)

        clear_button = QPushButton("清空")
        clear_button.clicked.connect(self.clear_chat)
        clear_button.setFixedWidth(80)

        input_layout.addWidget(self.message_input, 1)
        input_layout.addWidget(send_button)
        input_layout.addWidget(clear_button)
        main_layout.addLayout(input_layout)

        # 添加一些示例问题按钮
        examples_layout = QHBoxLayout()
        examples_label = QLabel("快速提问:")
        examples_label.setStyleSheet("font-weight: bold;")
        examples_layout.addWidget(examples_label)

        example_questions = ["你是谁？", "今天天气怎么样？", "讲个笑话", "你的特长是什么？"]
        for question in example_questions:
            btn = QPushButton(question)
            btn.clicked.connect(lambda checked, q=question: self.set_example_question(q))
            btn.setStyleSheet("background-color: #4ecdc4;")
            examples_layout.addWidget(btn)

        main_layout.addLayout(examples_layout)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 设置Enter键发送消息
        self.message_input.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.message_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() & Qt.ControlModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def set_example_question(self, question):
        self.message_input.setText(question)

    def save_token(self):
        self.api_token = self.token_input.text()
        if self.api_token:
            self.status_bar.showMessage("API Token 已保存", 3000)
            self.token_input.clear()
        else:
            QMessageBox.warning(self, "警告", "请输入有效的API Token")

    def send_message(self):
        if not self.api_token:
            QMessageBox.warning(self, "警告", "请先输入并保存API Token")
            return

        user_message = self.message_input.toPlainText().strip()
        if not user_message:
            return

        # 显示用户消息
        self.display_message("你", user_message, "#4ecdc4")
        self.message_input.clear()

        # 发送到API
        self.status_bar.showMessage("正在思考中...")
        QApplication.processEvents()  # 更新UI

        response = self.call_gemini_api(user_message)

        if response:
            # 显示AI回复
            self.display_message("小猪AI", response, "#ff6b6b")
            self.status_bar.showMessage("回复完成", 3000)
        else:
            self.status_bar.showMessage("请求失败", 3000)

    def call_gemini_api(self, user_message):
        try:
            conn = http.client.HTTPSConnection("yunwu.ai")

            # 构建历史对话
            contents = []
            for role, text in self.chat_history[-6:]:  # 保留最近6条历史
                contents.append({
                    "role": role,
                    "parts": [{"text": text}]
                })

            # 添加当前消息
            contents.append({
                "role": "user",
                "parts": [{"text": user_message}]
            })

            payload = json.dumps({
                "systemInstruction": {
                    "parts": [{
                        "text": "你是一只可爱的小猪AI助手。你会在每次回复的开头加上'🐷 哼哼~'，然后进行回答。请用友好、可爱的语气回复用户的问题。"
                    }]
                },
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.9,
                    "maxOutputTokens": 1024
                }
            })

            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }

            conn.request("POST", "/v1beta/models/gemini-3-pro:generateContent", payload, headers)
            res = conn.getresponse()
            data = res.read()

            if res.status == 200:
                response_json = json.loads(data.decode("utf-8"))
                # 提取回复文本
                if "candidates" in response_json and len(response_json["candidates"]) > 0:
                    if "content" in response_json["candidates"][0]:
                        parts = response_json["candidates"][0]["content"]["parts"]
                        if parts and "text" in parts[0]:
                            ai_response = parts[0]["text"]
                            # 保存到历史
                            self.chat_history.append(("user", user_message))
                            self.chat_history.append(("model", ai_response))
                            return ai_response
            return "抱歉，我暂时无法回答这个问题。"

        except Exception as e:
            print(f"API调用错误: {e}")
            return f"请求出错: {str(e)}"

    def display_message(self, sender, message, color):
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")

        # 使用HTML格式化消息
        html = f"""
        <div style="margin: 10px 0; padding: 10px; border-radius: 10px; background-color: {color}20;">
            <div style="display: flex; justify-content: space-between;">
                <span style="font-weight: bold; color: {color};">{sender}</span>
                <span style="font-size: 12px; color: #888;">{timestamp}</span>
            </div>
            <div style="margin-top: 5px; color: #333;">{message.replace(chr(10), '<br>')}</div>
        </div>
        """

        # 添加分隔线
        separator = f"""
        <div style="margin: 5px 0; border-bottom: 1px solid #eee;"></div>
        """

        # 追加到聊天显示区域
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertHtml(html + separator)

        # 滚动到底部
        self.chat_display.ensureCursorVisible()

    def clear_chat(self):
        self.chat_display.clear()
        self.chat_history.clear()
        self.status_bar.showMessage("聊天记录已清空", 3000)


def main():
    app = QApplication(sys.argv)

    # 设置应用图标和样式
    app.setStyle('Fusion')

    window = ChatWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()