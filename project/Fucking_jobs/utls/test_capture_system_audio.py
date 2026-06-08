from pynput import keyboard
import sounddevice as sd
import numpy as np
import tempfile
import os
import wave
from pydub import AudioSegment
from datetime import datetime

recording = False
frames = []
shift_pressed = False


def test_capture_microphone():
    """按住 Shift+S 录制 Lenovo X370 麦克风，松开后保存为 MP3"""

    # 列出所有音频设备
    devices = sd.query_devices()

    # 自动查找 Lenovo X370 麦克风
    mic_device = None
    for i, dev in enumerate(devices):
        name = dev['name'].lower()
        if 'lenovo x370' in name and dev['max_input_channels'] > 0:
            mic_device = i
            break

    if mic_device is None:
        mic_device = None

    # 获取设备默认采样率
    sample_rate = int(devices[mic_device]['default_samplerate']) if mic_device else 44100
    channels = devices[mic_device]['max_input_channels'] if mic_device else 1
    dtype = np.int16

    print(f"采样率: {sample_rate}Hz | 通道: {channels}")
    print("按住 Shift+S 开始录音，松开停止...")

    def audio_callback(indata, frame_count, time_info, status):
        global frames
        if recording:
            frames.append(indata.copy())

    stream = sd.InputStream(
        samplerate=sample_rate, channels=channels, dtype=dtype,
        callback=audio_callback, device=mic_device
    )
    stream.start()

    def on_press(key):
        global recording, frames, shift_pressed
        
        if key in (keyboard.Key.shift_l, keyboard.Key.shift_r):
            shift_pressed = True
        elif hasattr(key, 'char'):
            if key.char.lower() == 's' and shift_pressed:
                if not recording:
                    frames = []
                    recording = True
                    print("🔴 录音开始...")

    def on_release(key):
        global recording, shift_pressed
        
        # 只在松开 S 键时停止录音（不区分大小写）
        if recording and hasattr(key, 'char') and key.char.lower() == 's':
            recording = False
            print("🛑 录音结束，正在保存...")
            save_audio(frames, sample_rate, channels)
        
        if key in (keyboard.Key.shift_l, keyboard.Key.shift_r):
            shift_pressed = False

    def save_audio(audio_frames, sr, ch):
        if not audio_frames:
            print("⚠️ 未录制到音频")
            return

        audio = np.concatenate(audio_frames, axis=0)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name

        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(ch)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(audio.tobytes())

        # 创建 mp3_temp 目录
        mp3_dir = os.path.join(os.getcwd(), "mp3_temp")
        os.makedirs(mp3_dir, exist_ok=True)
        
        # 按时间戳命名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mp3_path = os.path.join(mp3_dir, f"audio_{timestamp}.mp3")
        
        seg = AudioSegment.from_wav(wav_path)
        seg.export(mp3_path, format="mp3", bitrate="128k")
        os.unlink(wav_path)

        print(f"✅ 已保存: {mp3_path}")
        print(f"   时长: {len(seg) / 1000:.1f}s | 采样率:{sr}Hz | 通道:{ch}")


    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

    stream.stop()
    stream.close()


if __name__ == "__main__":
    test_capture_microphone()