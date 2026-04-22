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


def type_code_from_file(file_path, delay=0.05):
    """
    从txt文件中读取内容并使用pyautogui模拟输入
    忽略所有空格、Tab等空白字符，只执行换行

    Args:
        file_path: txt文件路径
        delay: 每个字符之间的延迟时间(秒)，默认0.05秒
    """
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total_chars = sum(len(line) for line in lines)
    print(f"准备输入 {len(lines)} 行，共 {total_chars} 个字符")
    print("请在3秒内切换到目标输入窗口...")

    # 给用户3秒时间切换到目标窗口
    time.sleep(3)
    # 检测并切换到英文输入模式
    if not is_english_input():
        print("检测到非英文输入状态，正在切换...")
        switch_to_english()
    else:
        print("当前已是英文输入状态")
    print("开始输入...")
    need_home_next = False  # 标记下一行是否需要回到行首
    # 逐行输入，忽略空格和Tab
    for line_idx, line in enumerate(lines):
        # 检查是否收到停止信号
        if hasattr(type_code_from_file, '_stop_flag') and type_code_from_file._stop_flag:
            print("\n用户中断输入！")
            return

        # 检查暂停状态
        while hasattr(type_code_from_file, '_paused') and type_code_from_file._paused:
            time.sleep(0.1)

        if need_home_next:
            pyautogui.press('home')
            need_home_next = False
            line_content = line
            for char in line_content:
                if char == '\n':
                    pyautogui.typewrite(' ')
                pyautogui.typewrite(char, interval=delay)
            print(f"已输入行 {line_idx + 1} inter的下一行")

        # 去除所有空白字符（空格、Tab等）
        elif 'return' in line:
            pyautogui.press('home')
            line_content = line
            for char in line_content:
                if char == '\n':
                    pyautogui.typewrite(' ')
                pyautogui.typewrite(char, interval=delay)
            need_home_next = True
            print(f"inter 已输入行 {line_idx + 1}")
        else:

            line_content = line.strip()
            # 只输入非空白字符
            for char in line_content:
                pyautogui.typewrite(char, interval=delay)
            # pyautogui.press('enter')
            pyautogui.typewrite(' ')
            pyautogui.typewrite('\n')
            # 随机延迟模拟思考时间（0.3-1.5秒）
            think_time = random.uniform(0.5, 0.5)
            time.sleep(think_time)

        # 每行输完后随机短暂停顿（0.1-0.5秒）
        if line_content and len(line_content) > 18 and random.random() > 0.7:  # 如果不是空行 其比较长 就有一定概率触发再次换行
            pyautogui.press('enter')  #
            pause_time = random.uniform(0.4, 0.8)
            time.sleep(pause_time)

        # 每行完成后显示进度
        if (line_idx + 1) % 10 == 0 or line_idx == len(lines) - 1:
            print(f"已输入 {line_idx + 1}/{len(lines)} 行")

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