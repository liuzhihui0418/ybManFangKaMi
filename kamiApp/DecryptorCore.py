import sys
import os
import json
import base64
import hashlib
import platform
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QLabel, QPushButton, QLineEdit,
                             QTextEdit, QFileDialog, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad  # 注意：这里增加了 pad 用于加密

# === 配置区 (必须与主程序 ActivationManager 保持一致) ===
DEFAULT_SALT = "yunmangongfang_storage_v1_salt"  # 必须与主程序一致


class DecryptorCore:
    """核心加解密逻辑"""

    @staticmethod
    def get_local_fingerprint():
        """获取本机的指纹"""
        try:
            computer_name = platform.node()
            processor = platform.processor()
            system_version = platform.version()
            try:
                import uuid
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                                for elements in range(0, 8 * 6, 8)][::-1])
            except:
                mac = "unknown_mac"

            raw_info = f"{computer_name}_{processor}_{system_version}_{mac}"
            return hashlib.sha256(raw_info.encode()).hexdigest()
        except:
            return "无法获取本机指纹"

    @staticmethod
    def decrypt_data(encrypted_content, fingerprint, salt):
        """执行解密"""
        try:
            # 1. 计算密钥
            key_source = f"{fingerprint}_{salt}"
            key = hashlib.sha256(key_source.encode()).digest()

            # 2. Base64 解码
            combined = base64.urlsafe_b64decode(encrypted_content)

            # 3. 分离 IV 和 密文
            iv = combined[:16]
            ciphertext = combined[16:]

            # 4. AES 解密
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_bytes = unpad(cipher.decrypt(ciphertext), AES.block_size)

            # 5. 转 JSON
            return json.loads(decrypted_bytes.decode('utf-8')), "✅ 解密成功"
        except Exception as e:
            return None, f"❌ 解密失败: {str(e)}\n(原因可能是：指纹不匹配、盐值错误或文件损坏)"

    @staticmethod
    def encrypt_data(json_data, fingerprint, salt):
        """执行加密 (用于保存修改)"""
        try:
            # 1. 计算密钥
            key_source = f"{fingerprint}_{salt}"
            key = hashlib.sha256(key_source.encode()).digest()

            # 2. 处理数据
            json_str = json.dumps(json_data, ensure_ascii=False)

            # 3. AES 加密
            iv = os.urandom(16)  # 生成新的随机IV
            cipher = AES.new(key, AES.MODE_CBC, iv)
            encrypted_bytes = cipher.encrypt(pad(json_str.encode('utf-8'), AES.block_size))

            # 4. 组合 IV + 密文 并转 Base64
            combined = iv + encrypted_bytes
            return base64.urlsafe_b64encode(combined).decode('utf-8'), "✅ 加密成功"
        except Exception as e:
            return None, f"❌ 加密失败: {str(e)}"


class AdminDecryptWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("云漫工坊 - 激活文件修改终端 (Admin Pro)")
        self.setFixedSize(950, 750)
        self.setup_ui()
        self.apply_styles()

        # 自动填入本机指纹
        local_fp = DecryptorCore.get_local_fingerprint()
        self.fingerprint_input.setText(local_fp)

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # === 标题 ===
        title = QLabel("🔐 激活文件可视化修改工具 (解密/编辑/重加密)")
        title.setObjectName("mainTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # === 步骤 1: 选择文件 ===
        file_group = QGroupBox("1. 选择加密文件 (activation.dat)")
        file_layout = QHBoxLayout(file_group)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("请选择 activation.dat 文件路径...")
        self.path_input.setReadOnly(True)

        self.browse_btn = QPushButton("📂 浏览文件")
        self.browse_btn.setFixedSize(100, 38)
        self.browse_btn.clicked.connect(self.browse_file)

        file_layout.addWidget(self.path_input)
        file_layout.addWidget(self.browse_btn)
        layout.addWidget(file_group)

        # === 步骤 2: 解密参数 ===
        param_group = QGroupBox("2. 机器指纹配置 (关键)")
        param_layout = QGridLayout(param_group)

        # 指纹输入
        fp_label = QLabel("机器指纹 (Machine Fingerprint):")
        self.fingerprint_input = QLineEdit()
        self.fingerprint_input.setPlaceholderText("如果是解密用户的文件，必须填入用户的指纹")
        self.fingerprint_input.setStyleSheet("color: #00ff00; font-weight: bold;")

        # 快捷按钮：重置为本机
        reset_fp_btn = QPushButton("使用本机指纹")
        reset_fp_btn.setFixedWidth(100)
        reset_fp_btn.clicked.connect(lambda: self.fingerprint_input.setText(DecryptorCore.get_local_fingerprint()))

        # 盐值输入
        salt_label = QLabel("加密盐值 (Salt):")
        self.salt_input = QLineEdit()
        self.salt_input.setText(DEFAULT_SALT)  # 默认盐值
        self.salt_input.setReadOnly(True)      # 通常不需要修改盐值
        self.salt_input.setStyleSheet("color: #888;")

        # 布局
        param_layout.addWidget(fp_label, 0, 0)
        param_layout.addWidget(self.fingerprint_input, 0, 1)
        param_layout.addWidget(reset_fp_btn, 0, 2)
        param_layout.addWidget(salt_label, 1, 0)
        param_layout.addWidget(self.salt_input, 1, 1, 1, 2)

        layout.addWidget(param_group)

        # === 解密按钮 ===
        self.action_btn = QPushButton("🔓 1. 解密并查看内容")
        self.action_btn.setObjectName("actionBtn")
        self.action_btn.setFixedHeight(45)
        self.action_btn.clicked.connect(self.perform_decryption)
        layout.addWidget(self.action_btn)

        # === 步骤 3: 结果展示与编辑 ===
        result_group = QGroupBox("3. 数据编辑 (JSON)")
        result_layout = QVBoxLayout(result_group)

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(False)  # 允许编辑！
        self.result_area.setFont(QFont("Consolas", 10))
        self.result_area.setPlaceholderText("解密成功后，这里会显示 JSON 数据。\n您可以直接修改数据（如修改过期时间），然后点击下方保存按钮。")
        result_layout.addWidget(self.result_area)

        # 保存按钮
        self.save_btn = QPushButton("💾 2. 保存修改并重新加密 (覆盖原文件)")
        self.save_btn.setFixedHeight(50)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #11998e, stop: 1 #38ef7d);
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #16a085, stop: 1 #2ecc71);
            }
        """)
        self.save_btn.clicked.connect(self.save_changes)
        result_layout.addWidget(self.save_btn)

        layout.addWidget(result_group)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择加密文件", "", "Data Files (*.dat);;All Files (*)")
        if path:
            self.path_input.setText(path)

    def perform_decryption(self):
        """解密逻辑"""
        file_path = self.path_input.text().strip()
        fingerprint = self.fingerprint_input.text().strip()
        salt = self.salt_input.text().strip()

        if not file_path or not os.path.exists(file_path):
            self.log_result("❌ 请先选择有效的文件路径")
            return

        if not fingerprint:
            self.log_result("❌ 机器指纹不能为空！\n解密必须依赖生成该文件时的机器指纹。")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                encrypted_content = f.read().strip()

            if not encrypted_content:
                self.log_result("❌ 文件内容为空")
                return

            # 开始解密
            data, msg = DecryptorCore.decrypt_data(encrypted_content, fingerprint, salt)

            if data:
                # 格式化 JSON 显示
                pretty_json = json.dumps(data, indent=4, ensure_ascii=False)
                self.result_area.setText(pretty_json)
                self.result_area.setStyleSheet("color: #00ff00; background-color: #0c0c1f; border: 1px solid #333;")
                QMessageBox.information(self, "成功", "文件解密成功！\n现在您可以修改下方文本框中的内容。")
            else:
                self.log_result(msg)

        except Exception as e:
            self.log_result(f"❌ 系统错误: {str(e)}")

    def save_changes(self):
        """保存修改逻辑"""
        # 1. 获取参数
        file_path = self.path_input.text().strip()
        fingerprint = self.fingerprint_input.text().strip()
        salt = self.salt_input.text().strip()
        json_text = self.result_area.toPlainText().strip()

        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "错误", "未选择文件或文件路径无效")
            return

        if not fingerprint:
            QMessageBox.warning(self, "错误", "机器指纹不能为空！")
            return

        if not json_text:
            QMessageBox.warning(self, "错误", "内容为空，无法保存")
            return

        # 2. 验证 JSON 格式是否正确
        try:
            json_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "格式错误", f"JSON 格式不正确，请检查语法！\n\n错误: {e}")
            return

        # 3. 确认对话框 (防止误操作)
        warning_text = (
            "确定要覆盖原文件吗？\n\n"
            "⚠️ 重要提示：\n"
            "1. 加密将使用上方填写的【机器指纹】。\n"
            "2. 如果这是发给用户的，请确保指纹是【用户的机器指纹】，否则用户打不开！\n"
            "3. 操作不可撤销。"
        )
        reply = QMessageBox.question(self, "确认保存", warning_text, QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            # 4. 执行加密
            encrypted_content, msg = DecryptorCore.encrypt_data(json_data, fingerprint, salt)

            if encrypted_content:
                try:
                    # 5. 写入文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(encrypted_content)
                    QMessageBox.information(self, "保存成功", "✅ 文件已成功修改并重新加密！\n\n现在可以将此文件发回给用户了。")
                except Exception as e:
                    QMessageBox.critical(self, "写入失败", f"写入文件时出错: {e}")
            else:
                QMessageBox.critical(self, "加密失败", msg)

    def log_result(self, text):
        self.result_area.setText(text)
        self.result_area.setStyleSheet("color: #ff3366; background-color: #0c0c1f; border: 1px solid #ff3366;")

    def apply_styles(self):
        """应用暗黑科技风样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
            QGroupBox {
                color: #00b4d8;
                font-weight: bold;
                border: 1px solid #16213e;
                border-radius: 5px;
                margin-top: 10px;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }
            QLabel {
                color: #e9ecef;
                font-size: 12px;
                font-family: "Microsoft YaHei";
            }
            #mainTitle {
                font-size: 24px;
                color: #ffffff;
                font-weight: bold;
                padding: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f0c29, stop:0.5 #302b63, stop:1 #24243e);
                border-radius: 8px;
            }
            QLineEdit {
                background-color: #16213e;
                color: #00d4ff;
                border: 1px solid #30475e;
                border-radius: 4px;
                padding: 8px;
                font-family: "Consolas";
            }
            QLineEdit:focus {
                border: 1px solid #00b4d8;
            }
            QTextEdit {
                background-color: #0c0c1f;
                color: #00d4ff;
                border: 1px solid #30475e;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #0f3460;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #16213e;
                border: 1px solid #00b4d8;
            }
            #actionBtn {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #e65c00, stop: 1 #F9D423);
                color: black;
                font-size: 16px;
                font-weight: bold;
            }
            #actionBtn:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ff7e26, stop: 1 #fabd05);
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    window = AdminDecryptWindow()
    window.show()
    sys.exit(app.exec_())