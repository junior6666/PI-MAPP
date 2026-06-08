"""
音频问答测试脚本
功能：按住 Shift+S 录音，松开后自动识别并调用 API 回答
"""

from pynput import keyboard
import sounddevice as sd
import numpy as np
import tempfile
import os
import wave
from pydub import AudioSegment
from datetime import datetime
import requests
from openai import OpenAI

# API 配置
API_KEY = "sk-amdrbrmgijytxbimkqjajogwscjmgpvvreidupkohkxrrheu"
BASE_URL = "https://api.siliconflow.cn/v1"

# 全局变量
recording = False
frames = []
shift_pressed = False


def save_audio(audio_frames, sample_rate=44100, channels=1):
    """保存音频为 MP3"""
    audio = np.concatenate(audio_frames, axis=0)
    
    # 临时 WAV
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
    
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())
    
    # 保存到 mp3_temp
    mp3_dir = os.path.join(os.getcwd(), "mp3_temp")
    os.makedirs(mp3_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mp3_path = os.path.join(mp3_dir, f"audio_{timestamp}.mp3")
    
    seg = AudioSegment.from_wav(wav_path)
    seg.export(mp3_path, format="mp3", bitrate="128k")
    os.unlink(wav_path)
    
    print(f"✅ 音频已保存: {mp3_path} ({len(seg)/1000:.1f}s)")
    return mp3_path


def speech_to_text(audio_path):
    """语音转文字"""
    print("\n🎯 正在识别语音...")
    
    url = f"{BASE_URL}/audio/transcriptions"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    with open(audio_path, "rb") as f:
        files = {
            "file": (os.path.basename(audio_path), f),
            "model": (None, "FunAudioLLM/SenseVoiceSmall")
        }
        resp = requests.post(url, headers=headers, files=files)
    
    if resp.status_code == 200:
        text = resp.json().get("text", "")
        print(f"📝 识别结果: {text}")
        return text
    else:
        print(f"❌ 识别失败: {resp.status_code}")
        return None


def ask_question(question):
    """调用 LLM 回答问题"""
    print("\n🤖 正在生成答案...")
    
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    response = client.chat.completions.create(
        model="Pro/zai-org/GLM-4.7",
        messages=[
            {"role": "system", "content": "你是一个专业的AI助手，请用简洁清晰的语言回答用户的问题。"},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    answer = response.choices[0].message.content
    print(f"\n💡 AI回答:\n{'-'*50}\n{answer}\n{'-'*50}")
    return answer


def on_press(key):
    global recording, frames, shift_pressed
    
    if key in (keyboard.Key.shift_l, keyboard.Key.shift_r):
        shift_pressed = True
    elif hasattr(key, 'char') and key.char.lower() == 's' and shift_pressed:
        if not recording:
            frames = []
            recording = True
            print("\n🔴 录音开始...")


def on_release(key):
    global recording, shift_pressed
    
    if recording and hasattr(key, 'char') and key.char.lower() == 's':
        recording = False
        print("🛑 录音结束，正在处理...")
        
        if frames:
            # 保存音频
            audio_path = save_audio(frames)
            
            # 语音识别
            question = speech_to_text(audio_path)
            
            if question:
                # 问答
                ask_question(question)
        
    if key in (keyboard.Key.shift_l, keyboard.Key.shift_r):
        shift_pressed = False


if __name__ == "__main__":
    print("="*50)
    print("🎤 音频问答测试")
    print("="*50)
    print("📌 按住 Shift+S 开始录音，松开 S 键停止")
    print("   程序将自动识别语音并调用 AI 回答")
    print("="*50)
    
    # 启动音频流
    stream = sd.InputStream(
        samplerate=44100,
        channels=1,
        dtype=np.int16,
        callback=lambda indata, frame_count, time_info, status: 
            frames.append(indata.copy()) if recording else None
    )
    stream.start()
    
    # 启动键盘监听
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
    
    stream.stop()
    stream.close()
