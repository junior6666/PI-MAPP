from pynput import keyboard
import time


class KeyboardBlocker:
    def __init__(self):
        self.enabled = False  # False=禁用, True=启用（注意这里改成了False）
        self.running = True

    def on_press(self, key):
        if not self.running:
            return False

        # 按 F12 切换禁用/启用
        try:
            if key == keyboard.Key.f12:
                self.enabled = not self.enabled
                status = "启用" if self.enabled else "禁用"
                print(f"\n键盘已{status} (按 F12 切换)")
                return True
        except:
            pass

        # 按 Esc 退出程序
        try:
            if key == keyboard.Key.esc:
                print("\n正在退出程序...")
                self.running = False
                return False  # 停止监听器
        except:
            pass

        # 如果键盘处于禁用状态，阻止所有按键
        if not self.enabled:  # enabled=False 时禁用键盘
            print(f"\r阻止按键: {key}", end='')  # 可选：显示阻止了哪些键
            return False  # 返回 False 阻止该按键

        # 键盘启用状态，允许所有按键
        return True

    def start(self):
        print("=" * 50)
        print("键盘控制程序")
        print("F12: 切换键盘禁用/启用")
        print("Esc: 退出程序")
        print("=" * 50)
        print("当前状态: 键盘已禁用（按 F12 启用）")
        print("-" * 50)

        # 创建并启动监听器
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            suppress=True  # 重要！抑制系统默认处理
        )
        self.listener.start()

        # 保持程序运行
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n检测到 Ctrl+C")
        finally:
            self.listener.stop()
            print("程序已退出")

if __name__ == "__main__":
    # 方法1：使用类版本
    blocker = KeyboardBlocker()
    blocker.start()