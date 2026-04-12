import mss
from PIL import Image
from pynput import keyboard  # 替换 keyboard 库
import time
from datetime import datetime
import os
import threading


class HotkeyScreenshot:
    """绑定热键的截图工具 - 使用 pynput"""

    def __init__(self, hotkey: str = "<ctrl>+<shift>+s", save_dir: str = "./screenshots"):
        """
        初始化截图工具

        Args:
            hotkey: 触发截图的热键组合
            save_dir: 截图保存目录
        """
        self.hotkey = hotkey
        self.save_dir = save_dir
        self.sct = None
        self.enabled = True
        self.listener = None
        self.capture_lock = threading.Lock()  # 添加线程锁

        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)

        # 初始化截图器
        self._init_screenshotter()

        # 注册热键
        self._register_hotkey()

        print(f"截图工具已启动!")
        print(f"按下 [{hotkey.replace('<', '').replace('>', '')}] 进行截图")
        print(f"截图将保存到: {os.path.abspath(save_dir)}")
        print("按 ESC 退出程序\n")

    def _init_screenshotter(self):
        """初始化 mss 截图器"""
        if self.sct:
            self.sct.close()
        self.sct = mss.mss()

    def _register_hotkey(self):
        """注册全局热键"""
        # 解析热键字符串
        keys = []
        modifiers = []

        parts = self.hotkey.lower().replace(' ', '').split('+')
        for part in parts:
            part = part.strip('<>')
            if part in ['ctrl', 'control']:
                modifiers.append(keyboard.Key.ctrl)
            elif part in ['alt', 'option']:
                modifiers.append(keyboard.Key.alt)
            elif part in ['shift']:
                modifiers.append(keyboard.Key.shift)
            elif part in ['win', 'cmd', 'meta']:
                modifiers.append(keyboard.Key.cmd)
            else:
                keys.append(part)

        self.trigger_key = keys[0] if keys else 's'
        self.modifiers = modifiers

        # 启动监听器
        self.listener = keyboard.GlobalHotKeys({
            self.hotkey: self.quick_screenshot
        })
        self.listener.start()

        # ESC 退出
        keyboard.Listener(on_press=self._on_escape).start()

    def _on_escape(self, key):
        """ESC 键退出"""
        try:
            if key == keyboard.Key.esc:
                print("\n正在退出...")
                self.enabled = False
                if self.listener:
                    self.listener.stop()
                if self.sct:
                    self.sct.close()
                print("再见!")
                exit(0)
        except AttributeError:
            pass

    def quick_screenshot(self):
        """热键触发的截图方法 - 线程安全"""
        if not self.enabled:
            return

        with self.capture_lock:
            sct_instance = None
            try:
                start = time.perf_counter()

                # 在当前线程创建新的 mss 实例
                sct_instance = mss.mss()

                # 截取主显示器
                monitor = sct_instance.monitors[1]
                screenshot = sct_instance.grab(monitor)

                # 转换为 PIL Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

                # 生成文件名（时间戳）
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                filename = f"screenshot_{timestamp}.png"
                filepath = os.path.join(self.save_dir, filename)

                # 保存截图
                img.save(filepath)

                elapsed = (time.perf_counter() - start) * 1000

                print(f"[✓] 截图成功! 耗时: {elapsed:.2f}ms | 保存至: {filepath}")

                return img

            except Exception as e:
                print(f"[✗] 截图失败: {e}")
            finally:
                # 确保关闭当前线程的 mss 实例
                if sct_instance:
                    sct_instance.close()

# ==================== 使用方法 ====================

if __name__ == "__main__":
    # 方式1：使用默认配置
    screenshot_tool = HotkeyScreenshot(
        hotkey="<alt>+x",  # 截图热键
        save_dir="./screenshots"  # 保存目录
    )

    # 保持程序运行
    listener = keyboard.Listener(on_press=lambda k: None)
    listener.start()
    listener.join()