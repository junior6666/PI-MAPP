import requests
import os

def test_siliconflow_api(audio_file_path):
    """测试 SiliconFlow API 语音识别"""
    
    # 检查文件是否存在
    if not os.path.exists(audio_file_path):
        print(f"❌ 文件不存在: {audio_file_path}")
        return None
    
    print(f"📁 正在读取音频文件: {audio_file_path}")
    
    # 调用 SiliconFlow API
    url = "https://api.siliconflow.cn/v1/audio/transcriptions"
    headers = {"Authorization": "Bearer sk-amdrbrmgijytxbimkqjajogwscjmgpvvreidupkohkxrrheu"}

    with open(audio_file_path, "rb") as audio_file:
        files = {
            "file": (os.path.basename(audio_file_path), audio_file),
            "model": (None, "FunAudioLLM/SenseVoiceSmall")
        }
        print("🚀 正在调用 API...")
        resp = requests.post(url, headers=headers, files=files)

    if resp.status_code == 200:
        text = resp.json().get("text", "")
        print(f"\n✅ 识别成功!")
        print(f"📝 识别结果: {text}")
        return text
    else:
        print(f"\n❌ 识别失败!")
        print(f"状态码: {resp.status_code}")
        print(f"错误信息: {resp.text}")
        return None


# 测试
if __name__ == "__main__":
    # 测试音频文件路径
    audio_path = r"mp3_temp\audio_20260608_111743.mp3"
    
    print("="*50)
    print("SiliconFlow 语音识别 API 测试")
    print("="*50)
    
    result = test_siliconflow_api(audio_path)
