from gradio_client import Client
import shutil
import os

# 1. 这里填你仙宫云的公网链接 (每次重启实例后，这个链接可能会变，记得更新)
# 注意：要把最后的斜杠去掉，或者保留都行
API_URL = "https://35o5uyvyfj6nth2l-7860.container.x-gpu.com/"

print(f"🔗 正在连接到云端服务器: {API_URL} ...")
client = Client(API_URL)

# 2. 发送生图指令
print("🎨 正在发送指令，请稍候...")
result = client.predict(
    prompt="A beautiful landscape, mountains, river, 8k, masterpiece", # 你的提示词
    steps=6,            # 步数
    seed=-1,            # 随机种子 (-1表示随机)
    width=1024,         # 宽
    height=768,         # 高
    use_enhancer=True,  # 是否开启画质增强
    api_name="/run_inference" # 调用的接口名字（对应文生图）
)

# 3. 处理结果
# result 是一个元组：(图片本地路径, 日志信息)
image_path = result[0]
log_msg = result[1]

print("✅ 生成完成！")
print(f"📄 服务器日志: {log_msg}")
print(f"📂 图片已自动下载到本地临时目录: {image_path}")

# 4. (可选) 把图片复制到当前目录，方便查看
destination = "./output.webp"
shutil.copy(image_path, destination)
print(f"💾 已将图片保存为当前目录下的: {destination}")