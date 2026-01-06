import requests
import time

# 把你刚才生成的那个打不开的长链接，复制粘贴到下面引号里
target_url = """
https://openapi.alipaydev.com/gateway.do?app_id=9021000158645353&biz_content=...
(请粘贴你那条完整的长链接)
"""

print(f"当前电脑时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("正在尝试请求支付宝沙箱服务器...")

try:
    # 模拟浏览器请求
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.get(target_url, headers=headers, timeout=10)

    print(f"\n状态码: {resp.status_code}")
    print("服务器返回的前200个字符:")
    print("-" * 30)
    print(resp.text[:200])
    print("-" * 30)

    if "Error" in resp.text or "错误" in resp.text:
        print("\n❌ 页面返回了错误信息，通常是参数或时间戳问题。")
    elif resp.status_code == 200:
        print("\n✅ 网络是通的！如果在浏览器打不开，可能是浏览器拦截了。")
    else:
        print("\n❌ 服务器连接异常。")

except Exception as e:
    print(f"\n❌ 根本连不上服务器 (网络错误): {e}")