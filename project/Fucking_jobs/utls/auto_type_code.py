import threading

import pyautogui
import time
import random
import ctypes

from pynput import keyboard


def is_english_input():
    """检测当前是否为英文输入状态"""
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    thread_id = user32.GetWindowThreadProcessId(hwnd, 0)
    layout = user32.GetKeyboardLayout(thread_id)
    lang_id = layout & 0xFFFF
    return (lang_id == 0x0409) or (lang_id & 0xFF == 0x09)


def switch_to_english():
    """切换到英文输入状态"""
    print("正在切换到英文输入模式...")
    pyautogui.hotkey('alt', 'shift')
    time.sleep(0.8)
    if not is_english_input():
        pyautogui.hotkey('alt', 'shift')
        time.sleep(0.5)
    print("已切换到英文输入模式")



def get_nearby_keys(char):
    """获取键盘上接近目标字符的其他字符"""
    keyboard_layout = {
        'q': ['w', 'a', 's'], 'w': ['q', 'e', 'a', 's', 'd'], 'e': ['w', 'r', 's', 'd', 'f'],
        'r': ['e', 't', 'd', 'f', 'g'], 't': ['r', 'y', 'f', 'g', 'h'], 'y': ['t', 'u', 'g', 'h', 'j'],
        'u': ['y', 'i', 'h', 'j', 'k'], 'i': ['u', 'o', 'j', 'k', 'l'], 'o': ['i', 'p', 'k', 'l'],
        'p': ['o', 'l'], 'a': ['q', 'w', 's', 'z', 'x'], 's': ['q', 'w', 'e', 'a', 'd', 'z', 'x', 'c'],
        'd': ['w', 'e', 'r', 's', 'f', 'x', 'c', 'v'], 'f': ['e', 'r', 't', 'd', 'g', 'c', 'v', 'b'],
        'g': ['r', 't', 'y', 'f', 'h', 'v', 'b', 'n'], 'h': ['t', 'y', 'u', 'g', 'j', 'b', 'n', 'm'],
        'j': ['y', 'u', 'i', 'h', 'k', 'n', 'm'], 'k': ['u', 'i', 'o', 'j', 'l', 'm'],
        'l': ['i', 'o', 'p', 'k'], 'z': ['a', 's', 'x'], 'x': ['z', 's', 'd', 'c'],
        'c': ['x', 'd', 'f', 'v'], 'v': ['c', 'f', 'g', 'b'], 'b': ['v', 'g', 'h', 'n'],
        'n': ['b', 'h', 'j', 'm'], 'm': ['n', 'j', 'k']
    }

    lower_char = char.lower()
    if lower_char in keyboard_layout:
        nearby = keyboard_layout[lower_char]
        return [c.upper() if char.isupper() else c for c in nearby]
    return []


def type_with_realistic_errors(char, delay=0.05, error_rate=0.08):
    """
    模拟真实打字，有一定概率打错并退格修正
    :param char: 要输入的字符
    :param delay: 输入延迟
    :param error_rate: 出错概率 (默认8%)
    """
    if random.random() < error_rate:
        nearby_chars = get_nearby_keys(char)
        if nearby_chars:
            num_errors = random.randint(1, min(3, len(nearby_chars)))
            wrong_chars = random.sample(nearby_chars, num_errors)

            for wrong_char in wrong_chars:
                pyautogui.typewrite(wrong_char, interval=delay * 0.7)
                time.sleep(random.uniform(0.1, 0.3))
                pyautogui.press('backspace')
                time.sleep(random.uniform(0.05, 0.15))
            return



def type_code_from_file(file_path, delay=0.01):
    """
    从txt文件中读取内容并使用pyautogui模拟输入
    核心逻辑：
    - Tab 按 4 空格计算
    - 若当前行空格数 < 上一行 → Home 手动处理
    - 否则 → 换行自动处理
    """

    import pyautogui
    import time
    import random

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total_chars = sum(len(line) for line in lines)
    print(f"准备输入 {len(lines)} 行，共 {total_chars} 个字符")
    print("请在3秒内切换到目标输入窗口...")

    time.sleep(3)

    # if not is_english_input():
    #     print("检测到非英文输入状态，正在切换...")
    #     switch_to_english()
    # else:
    #     print("当前已是英文输入状态")

    print("开始输入...")

    last_leading_spaces = None
    need_home = False

    for line_idx, line in enumerate(lines):

        if getattr(type_code_from_file, '_stop_flag', False):
            print("\n用户中断输入！")
            return
        while getattr(type_code_from_file, '_paused', False):
            time.sleep(0.1)

        # ✅ Tab 按 4 空格展开后再计算缩进
        expanded_line = line.expandtabs(4)
        leading_spaces = len(expanded_line) - len(expanded_line.lstrip(" "))

        if last_leading_spaces is not None and leading_spaces < last_leading_spaces:
            need_home = True

        if need_home:
            pyautogui.press('home')
            need_home = False
            line_content = line
            for char in line_content:
                if char == '\n':
                    pyautogui.typewrite(' ')
                pyautogui.typewrite(char, interval=delay)
            print(f"已输入行 {line_idx + 1} inter的下一行")
            print(f"[Home] 行 {line_idx + 1}")
        else:

            line_content = line.strip()
            # 只输入非空白字符
            for char in line_content:
                type_with_realistic_errors(char,delay= delay) # 只负责写错别字和删除
                pyautogui.typewrite(char, interval=delay)
            # pyautogui.press('enter')
            pyautogui.typewrite(' ')
            pyautogui.typewrite('\n')
            # 随机延迟模拟思考时间（0.3-1.5秒）
            think_time = random.uniform(0.5, 0.5)
            time.sleep(think_time)

        # 随机思考停顿
        time.sleep(random.uniform(0.3, 0.8))

        if len(line_content) > 18 and random.random() > 0.9:
            pyautogui.press('enter')
            time.sleep(random.uniform(0.4, 0.8))

        if (line_idx + 1) % 5 == 0 or line_idx == len(lines) - 1:
            print(f"已输入 {line_idx + 1}/{len(lines)} 行")

        last_leading_spaces = leading_spaces

    print("输入完成!")

def start_typing(file_path="code.txt", delay=0.05):
    """启动自动输入"""
    type_code_from_file._stop_flag = False
    type_code_from_file._paused = False
    type_code_from_file(file_path, delay)


def stop_typing():
    """停止自动输入"""
    if hasattr(type_code_from_file, '_stop_flag'):
        type_code_from_file._stop_flag = True
        print("\n正在停止输入...")


def toggle_pause():
    """切换暂停/恢复状态"""
    if hasattr(type_code_from_file, '_paused'):
        type_code_from_file._paused = not type_code_from_file._paused
        if type_code_from_file._paused:
            print("\n[已暂停] 按 Alt+L 恢复输入")
        else:
            print("\n[已恢复] 继续输入...")


def listen_hotkeys():
    """监听全局快捷键"""

    def on_press(key):
        if key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            listen_hotkeys._alt_pressed = True
        elif hasattr(listen_hotkeys, '_alt_pressed') and listen_hotkeys._alt_pressed:
            if hasattr(key, 'char') and key.char == 's':
                print("\n[快捷键] 检测到 Alt+S，开始自动输入...")
                typing_thread = threading.Thread(target=start_typing)
                typing_thread.daemon = True
                typing_thread.start()
                listen_hotkeys._alt_pressed = False
            elif hasattr(key, 'char') and key.char == 'l':
                print("\n[快捷键] 检测到 Alt+L，切换暂停/恢复...")
                toggle_pause()
                listen_hotkeys._alt_pressed = False

    def on_release(key):
        if key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            listen_hotkeys._alt_pressed = False

    listen_hotkeys._alt_pressed = False
    print("=" * 50)
    print("自动输入程序已启动")
    print("快捷键说明：")
    print("  Alt + S : 开始自动输入")
    print("  Alt + L : 暂停/恢复输入")
    print("=" * 50)
    print("等待快捷键指令...\n")

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    # 启动快捷键监听
    listen_hotkeys()