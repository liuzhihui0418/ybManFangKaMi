import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import secrets
import json


class CardKeyEncryption:
    """卡密加密管理器"""

    def __init__(self, secret_key=None):
        # 使用固定的密钥种子，确保加密一致性
        self.seed = "yunmangongfang_2024_secret"
        if secret_key:
            self.secret_key = secret_key
        else:
            # 从种子生成固定密钥
            self.secret_key = self._generate_fixed_key()

        # AES配置
        self.bs = AES.block_size

    def _generate_fixed_key(self):
        """从种子生成固定密钥"""
        return hashlib.sha256(self.seed.encode()).digest()

    def encrypt_api_key(self, real_api_key):
        """加密真实API密钥，生成用户卡密"""
        try:
            # 生成随机IV
            iv = secrets.token_bytes(16)

            # 创建AES cipher
            cipher = AES.new(self.secret_key, AES.MODE_CBC, iv)

            # 加密数据
            encrypted = cipher.encrypt(pad(real_api_key.encode('utf-8'), self.bs))

            # 组合IV + 加密数据
            combined = iv + encrypted

            # Base64编码
            encrypted_b64 = base64.urlsafe_b64encode(combined).decode('utf-8')

            # 添加前缀格式：ymgfjc-加密字符串
            user_card_key = f"ymgfjc-{encrypted_b64}"

            return user_card_key

        except Exception as e:
            print(f"加密失败: {e}")
            return None

    def decrypt_card_key(self, user_card_key):
        """从用户卡密解密出真实API密钥"""
        try:
            # 验证格式
            if not user_card_key.startswith("ymgfjc-"):
                raise ValueError("无效的卡密格式")

            # 提取加密部分
            encrypted_b64 = user_card_key[7:]  # 去掉"ymgfjc-"

            # Base64解码
            combined = base64.urlsafe_b64decode(encrypted_b64)

            # 分离IV和加密数据
            iv = combined[:16]
            encrypted_data = combined[16:]

            # 创建解密cipher
            cipher = AES.new(self.secret_key, AES.MODE_CBC, iv)

            # 解密
            decrypted = unpad(cipher.decrypt(encrypted_data), self.bs)

            return decrypted.decode('utf-8')

        except Exception as e:
            print(f"解密失败: {e}")
            return None

    def validate_card_format(self, card_key):
        """验证卡密格式是否正确"""
        return card_key.startswith("ymgfjc-") and len(card_key) > 20

    def get_card_info(self, card_key):
        """获取卡密信息（不解密真实密钥）"""
        if not self.validate_card_format(card_key):
            return None

        return {
            "format": "valid",
            "prefix": "ymgfjc",
            "encrypted_length": len(card_key) - 7,
            "is_encrypted": True
        }


# 单例加密管理器
card_encryptor = CardKeyEncryption()

# 演示使用示例
if __name__ == "__main__":
    # 原始API密钥
    original_api_key = "sk-kjGnQsnHmmDIcOCeZs6MKQG1qpjZ99pik6wzIAIytewh82gX"

    print("=" * 60)
    print("卡密加密解密演示")
    print("=" * 60)

    # 1. 加密API密钥
    print("\n1. 加密API密钥:")
    print(f"原始API密钥: {original_api_key}")

    encrypted_card = card_encryptor.encrypt_api_key(original_api_key)
    print(f"加密后的卡密: {encrypted_card}")

    # 2. 验证卡密格式
    print("\n2. 验证卡密格式:")
    is_valid = card_encryptor.validate_card_format(encrypted_card)
    print(f"卡密格式验证: {'有效' if is_valid else '无效'}")

    # 3. 获取卡密信息
    print("\n3. 卡密信息:")
    card_info = card_encryptor.get_card_info(encrypted_card)
    if card_info:
        print(f"卡密前缀: {card_info['prefix']}")
        print(f"加密部分长度: {card_info['encrypted_length']}")
        print(f"是否加密: {'是' if card_info['is_encrypted'] else '否'}")

    # 4. 解密卡密
    print("\n4. 解密卡密:")
    decrypted_key = card_encryptor.decrypt_card_key(encrypted_card)
    print(f"解密后的API密钥: {decrypted_key}")

    # 5. 验证加解密一致性
    print("\n5. 验证加解密一致性:")
    is_consistent = (decrypted_key == original_api_key)
    print(f"加解密是否一致: {'是' if is_consistent else '否'}")

    # 6. 测试无效卡密
    print("\n6. 测试无效卡密处理:")
    invalid_card = "invalid-card-key-123"
    try:
        result = card_encryptor.decrypt_card_key(invalid_card)
        print(f"无效卡密解密结果: {result}")
    except Exception as e:
        print(f"无效卡密处理: {e}")

    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)

    # 保存示例结果
    demo_result = {
        "original_api_key": original_api_key,
        "encrypted_card": encrypted_card,
        "decrypted_api_key": decrypted_key,
        "is_consistent": is_consistent
    }

    print(f"\n完整加解密结果:")
    print(json.dumps(demo_result, indent=2, ensure_ascii=False))