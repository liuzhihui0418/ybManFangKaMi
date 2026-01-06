import sys
import os
import json
import base64
import hashlib
import uuid
import platform
import secrets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QLineEdit,
                             QTextEdit, QFileDialog, QGroupBox, QMessageBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# === 配置 (必须与后端一致) ===
CARD_SEED = "yunmangongfang_2024_secret"
STORAGE_SALT = "yunmangongfang_storage_v1_salt"


class DecryptorCore:
    @staticmethod
    def get_machine_id():
        try:
            node = uuid.getnode()
            system_info = f"{platform.node()}-{platform.system()}-{node}"
            machine_id = hashlib.md5(system_info.encode()).hexdigest().upper()
            return f"{machine_id[:4]}-{machine_id[4:8]}-{machine_id[8:12]}-{machine_id[12:16]}"
        except:
            return "UNKNOWN-DEVICE"

    @staticmethod
    def get_key(mode, manual_mid=""):
        """根据模式生成不同的 Key"""
        if mode == "card":
            # 模式A: 卡密通用密钥
            return hashlib.sha256(CARD_SEED.encode()).digest()
        else:
            # 模式B: 本地文件密钥 (依赖机器码)
            mid = manual_mid if manual_mid else DecryptorCore.get_machine_id()
            source = f"{mid}_{STORAGE_SALT}"
            return hashlib.sha256(source.encode()).digest()

    @classmethod
    def decrypt_data(cls, encrypted_str, mode="file", machine_id=""):
        try:
            key = cls.get_key(mode, machine_id)

            # Base64 解码
            combined = base64.urlsafe_b64decode(encrypted_str)
            iv = combined[:16]
            ciphertext = combined[16:]

            # AES 解密
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_json = unpad(cipher.decrypt(ciphertext), AES.block_size).decode('utf-8')
            return json.loads(decrypted_json), "✅ 解密成功"
        except Exception as e:
            return None, f"❌ 解密失败: {e}\n(如果是解密本地文件，请确认机器码是否正确)"

    @classmethod
    def encrypt_data(cls, data, mode="file", machine_id=""):
        try:
            key = cls.get_key(mode, machine_id)
            json_str = json.dumps(data, ensure_ascii=False)
            iv = secrets.token_bytes(16)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            encrypted_bytes = cipher.encrypt(pad(json_str.encode('utf-8'), AES.block_size))
            combined = iv + encrypted_bytes
            return base64.urlsafe_b64encode(combined).decode('utf-8'), "✅ 加密成功"
        except Exception as e:
            return None, f"❌ 加密失败: {e}"


# === GUI ===
class AdminDecryptWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("云漫工坊 - 超级解密终端 v2.0")
        self.setFixedSize(900, 750)
        self.setup_ui()
        self.apply_styles()

        # 自动填入本机ID
        self.mid_input.setText(DecryptorCore.get_machine_id())

    def setup_ui(self):
        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("🔐 通用数据解密/加密工具")
        title.setObjectName("mainTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # === 模式选择 ===
        mode_group = QGroupBox("1. 选择解密模式")
        mode_layout = QHBoxLayout(mode_group)

        self.rb_file = QRadioButton("解密本地文件 (activation.dat / *.dat)")
        self.rb_card = QRadioButton("解密卡密 (ymgfjc-...)")
        self.rb_file.setChecked(True)

        self.btn_group = QButtonGroup()
        self.btn_group.addButton(self.rb_file, 1)
        self.btn_group.addButton(self.rb_card, 2)

        self.rb_file.toggled.connect(self.toggle_mid_input)

        mode_layout.addWidget(self.rb_file)
        mode_layout.addWidget(self.rb_card)
        layout.addWidget(mode_group)

        # === 机器码输入 (仅文件模式需要) ===
        self.mid_group = QGroupBox("2. 机器码配置 (文件模式必填)")
        mid_layout = QHBoxLayout(self.mid_group)

        self.mid_input = QLineEdit()
        self.mid_input.setPlaceholderText("请输入该文件所属电脑的 Machine ID")

        btn_local_mid = QPushButton("获取本机ID")
        btn_local_mid.clicked.connect(lambda: self.mid_input.setText(DecryptorCore.get_machine_id()))

        mid_layout.addWidget(QLabel("Machine ID:"))
        mid_layout.addWidget(self.mid_input)
        mid_layout.addWidget(btn_local_mid)
        layout.addWidget(self.mid_group)

        # === 文件选择 ===
        file_group = QGroupBox("3. 选择文件")
        file_layout = QHBoxLayout(file_group)

        self.path_input = QLineEdit()
        btn_browse = QPushButton("📂 浏览")
        btn_browse.clicked.connect(self.browse_file)

        file_layout.addWidget(self.path_input)
        file_layout.addWidget(btn_browse)
        layout.addWidget(file_group)

        # === 操作按钮 ===
        btn_decrypt = QPushButton("🔓 开始解密")
        btn_decrypt.setObjectName("actionBtn")
        btn_decrypt.clicked.connect(self.do_decrypt)
        layout.addWidget(btn_decrypt)

        # === 结果显示 ===
        self.result_area = QTextEdit()
        self.result_area.setPlaceholderText("解密结果将显示在这里...")
        layout.addWidget(self.result_area)

        # === 保存按钮 ===
        btn_save = QPushButton("💾 保存修改并重新加密")
        btn_save.clicked.connect(self.do_save)
        layout.addWidget(btn_save)

    def toggle_mid_input(self):
        # 如果选了卡密模式，禁用机器码输入框
        is_file_mode = self.rb_file.isChecked()
        self.mid_group.setEnabled(is_file_mode)
        if not is_file_mode:
            self.mid_input.setStyleSheet("color: gray")
        else:
            self.mid_input.setStyleSheet("color: #00d4ff")

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "All Files (*)")
        if path: self.path_input.setText(path)

    def get_current_mode(self):
        return "file" if self.rb_file.isChecked() else "card"

    def do_decrypt(self):
        path = self.path_input.text().strip()
        if not path or not os.path.exists(path):
            self.result_area.setText("❌ 请先选择有效的文件")
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            # 如果是卡密文件，可能带有前缀 ymgfjc-
            if self.rb_card.isChecked() and content.startswith("ymgfjc-"):
                content = content[7:]

            mid = self.mid_input.text().strip()
            mode = self.get_current_mode()

            data, msg = DecryptorCore.decrypt_data(content, mode, mid)

            if data:
                self.result_area.setText(json.dumps(data, indent=4, ensure_ascii=False))
                QMessageBox.information(self, "成功", "✅ 解密成功！")
            else:
                self.result_area.setText(msg)

        except Exception as e:
            self.result_area.setText(f"❌ 读取错误: {e}")

    def do_save(self):
        path = self.path_input.text().strip()
        text = self.result_area.toPlainText().strip()
        if not path or not text: return

        try:
            data = json.loads(text)
            mid = self.mid_input.text().strip()
            mode = self.get_current_mode()

            encrypted, msg = DecryptorCore.encrypt_data(data, mode, mid)

            if encrypted:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(encrypted)
                QMessageBox.information(self, "成功", "✅ 修改已保存并重新加密！")
            else:
                QMessageBox.warning(self, "失败", msg)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"JSON 格式错误或保存失败: {e}")

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a2e; color: white; }
            QGroupBox { color: #00b4d8; font-weight: bold; border: 1px solid #30475e; margin-top: 10px; border-radius: 5px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QLineEdit, QTextEdit { background-color: #16213e; color: #00d4ff; border: 1px solid #30475e; padding: 5px; border-radius: 4px; font-family: Consolas; }
            QPushButton { background-color: #0f3460; color: white; border-radius: 4px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #16213e; border: 1px solid #00d4ff; }
            #actionBtn { background-color: #e65c00; font-size: 14px; }
            #mainTitle { font-size: 20px; font-weight: bold; color: white; margin-bottom: 10px; }
            QRadioButton { color: white; spacing: 5px; }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AdminDecryptWindow()
    win.show()
    sys.exit(app.exec_())