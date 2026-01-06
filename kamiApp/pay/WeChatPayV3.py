import time
import json
import uuid
import requests
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key


class WeChatPayV3:
    def __init__(self, mchid, appid, serial_no, private_key_path):
        self.mchid = mchid
        self.appid = appid
        self.serial_no = serial_no
        self.url_base = "https://api.mch.weixin.qq.com/v3"

        # 加载私钥
        with open(private_key_path, 'rb') as f:
            self.private_key = load_pem_private_key(f.read(), password=None)

    def _sign(self, method, url_path, body):
        """生成签名"""
        timestamp = str(int(time.time()))
        nonce_str = uuid.uuid4().hex

        # 构造签名串 (注意顺序：方法\nURL\n时间戳\n随机串\n包体\n)
        sign_str = f"{method}\n{url_path}\n{timestamp}\n{nonce_str}\n{body}\n"

        signature = self.private_key.sign(
            sign_str.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        sign_b64 = base64.b64encode(signature).decode('utf-8')

        # 构造Authorization头
        auth_head = (
            f'WECHATPAY2-SHA256-RSA2048 mchid="{self.mchid}",'
            f'nonce_str="{nonce_str}",timestamp="{timestamp}",'
            f'serial_no="{self.serial_no}",signature="{sign_b64}"'
        )
        return auth_head

    def jsapi_pay(self, openid, amount_fen, description):
        """发起JSAPI下单"""
        url_path = "/v3/pay/transactions/jsapi"
        url = self.url_base + url_path

        data = {
            "appid": self.appid,
            "mchid": self.mchid,
            "description": description,
            "out_trade_no": uuid.uuid4().hex,  # 随机生成订单号
            "notify_url": "https://www.baidu.com",  # 测试用，随便填
            "amount": {
                "total": amount_fen,  # 单位：分
                "currency": "CNY"
            },
            "payer": {
                "openid": openid
            }
        }
        body = json.dumps(data)

        headers = {
            "Authorization": self._sign("POST", url_path, body),
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        resp = requests.post(url, data=body, headers=headers)

        if resp.status_code == 200:
            prepay_id = resp.json().get('prepay_id')
            print(f"✅ 下单成功！PrepayID: {prepay_id}")
            return self._get_jsapi_params(prepay_id)
        else:
            print(f"❌ 下单失败: {resp.text}")
            return None

    def _get_jsapi_params(self, prepay_id):
        """生成前端调起支付所需的参数"""
        timestamp = str(int(time.time()))
        nonce_str = uuid.uuid4().hex
        package = f"prepay_id={prepay_id}"

        # 前端再次签名
        sign_str = f"{self.appid}\n{timestamp}\n{nonce_str}\n{package}\n"
        pay_sign = self.private_key.sign(
            sign_str.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        return {
            "appId": self.appid,
            "timeStamp": timestamp,
            "nonceStr": nonce_str,
            "package": package,
            "signType": "RSA",
            "paySign": base64.b64encode(pay_sign).decode('utf-8')
        }


# ================= 配置区 =================
# 👇 1. 你的商户号
MCHID = "1735916742"

# 👇 2. 你的小程序AppID (图3里的那个)
APPID = "wxc031a99ae26c102b"

# 👇 3. 证书序列号 (在商户平台 API安全 -> 申请证书那里可以看到一串大写的字符串)
SERIAL_NO = "2F8F11870B362F2847BCDE0880F864415BBD6DAC"

# 👇 4. 你的私钥文件路径 (下载的压缩包里 apiclient_key.pem 的位置)
PRIVATE_KEY_PATH = """
-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC3ZQTlBtGLmk+l
Qi/aBs1tqmFNonPEr7y7nAI//ueb6uAatX5kWt+AJjDspIYm3LQKUpAYs3dm7qjh
7ftmYBYXcU8SGJZ7+BTGOcoSHTxzDd49PUmy5cJ1/O8jkFTFp1U9+CBsj+P6GSRW
MQfHdyAWP+yUIx3Wypqc/Q7uMZuwYhhTbhrSY3lqLPGb1XK0D0SkgkJDJZe5RP9c
xMIO4hzw+QhIL8aGj7mOJ00u9ke6fVvU0qGqAAjJtdOuejT3TylA0AtgKHSLu3x8
bdeRdJN+c+BMRtQ1hRKVLHSuKJhMk4liFk+kcFyHJD7tLH6Om72MZijwv8TqJUXa
9a16B/ytAgMBAAECggEAXln9k6rXYcBJG5easMvxImuW1e8vKlDTg5321l/ZXrEP
DQ608QKDnBWJ9CWM0y+W/PyPH/YtBurgPiRGw9vJYdQsvv2hZjQy0+zlVj5uXC8V
WGJQqVZlnng7vAtEYc/+HfyrCc9ZldEbjbB59RgHjQrkNy596oSf2QakiM1C8RIW
J4Xtlu19WRk9TfroeR2cRe/jCdMSUBAjyoJHqXMhpHvaHj+rOjFTdLDyDGiKjCmm
nMD23sVSul+QAo0wbY4JewBa0fy/YDRyzsf+IUPS1uvYsNNGjU8OtbJaLLuYQlwL
u/PubtYPajAqbbEtJKAhQM7S5Bis6vLAxzhJV0Rr4QKBgQD0expa/lAecQZdYjK8
C0sbZoXC/P5qGFupiAiCjQ+SzYH/QgOckO6GY7I9IZgJJEEe4jfxkJ/UDcd4M1FX
BmzX1J+4QVZDEryhU19p/boUZDgZSF8mmQ7lNeKYDqPBxE+BsT6K1kF5Yy+hTGgt
K/mMSkve6Dfghcj5DP1EfOhnOQKBgQDACRn3/fajVXzQE3VWLgYENXVm7T4lFAjm
G8GN07HxnwIW3Vs0P5+AdV7ZRNPie7CmUJirzcB/z+ewKRzFp3XCN9bHYDY+8ytm
3seFdiIDacidm49dnGtGK+qdDqGB/Sq1Ph79+sFwGlqj+funcvKwr3lAktNuUIvc
uQG08OatFQKBgQDsFWxP7kEEBHT2/Hqtp+IxZYFJ1/D+FuN9BIXjO8CMLLOaAO9n
43TShbd63NPqD/5qil0nglc0+NFkO3oSpXu5t/M8hKt+Pbu1tcLvoTptspGRqJdp
uGfv42cbGxf7Z0y3mqcgfuHfDG7UPepjpJFobd5yNKCwycBW77oqxsvN0QKBgQCK
gQX922ob+/h9istCUQd92aDHj60WyRByBurfBCR/hJPZMeYqFQlReVXjlsTLwTJz
ggXbRBbnGGieochitpk0b1m1iysU1AYlt+Bn3gBCPfW31w7cEYk9n0cj5/2M56/5
8Mghns4NsLRXOGHNMBbiYG0vqbZdBjMaC0Wz31xA0QKBgHOafHtOE9Wraq8OyP2n
FUgX0RDxXFILwvqVcDKyC9qC31cCjHQj43jkMjA9hfd0JD0RGqqZQSG0xwRo6bvb
vJ5npp9KUVuQS9B/zBl9SAL5bIpqtYExSh5cr3Qb4bUnEdlUTNiXNDnh+I8xYutB
6eGE5w9LjFPXJiU4kx1FNol/
-----END PRIVATE KEY-----
"""

# 👇 5. 你的个人测试OpenID (如何获取看下文)
YOUR_OPENID = "oXwV........."
# =========================================

if __name__ == "__main__":
    wx_pay = WeChatPayV3(MCHID, APPID, SERIAL_NO, PRIVATE_KEY_PATH)

    # 发起 1分钱 测试支付
    params = wx_pay.jsapi_pay(YOUR_OPENID, 1, "Python测试支付")

    if params:
        print("\n👇 请复制下面的代码到微信开发者工具的 Console 里运行：")
        print("-" * 50)
        print(f"wx.requestPayment({{")
        print(f"  timeStamp: '{params['timeStamp']}',")
        print(f"  nonceStr: '{params['nonceStr']}',")
        print(f"  package: '{params['package']}',")
        print(f"  signType: '{params['signType']}',")
        print(f"  paySign: '{params['paySign']}',")
        print(f"  success (res) {{ console.log('支付成功!', res) }},")
        print(f"  fail (res) {{ console.log('支付失败', res) }}")
        print(f"}})")
        print("-" * 50)