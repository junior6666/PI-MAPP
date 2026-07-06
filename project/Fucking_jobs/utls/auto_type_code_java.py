import pyautogui
import time


def type_java_code(code_path):
    """
    模拟人工逐字符输入 Java 代码到 LeetCode 编辑器

    参数:
        code_path: 代码文件路径 (如 'code.txt')
    """

    # 读取代码文件
    with open(code_path, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')

    # 过滤空行
    lines = [line for line in lines if line.strip() != '']

    # 给用户 5 秒时间定位光标到编辑器
    print("请在 5 秒内将光标定位到 LeetCode 编辑器...")
    time.sleep(5)

    # 配置
    pyautogui.PAUSE = 0.01

    prev_indent = 0  # 上一行的缩进

    for i, line in enumerate(lines):
        current_indent = len(line) - len(line.lstrip())
        content = line.lstrip()

        if i == 0:
            # 第一行直接输入
            _type_content(content)
        else:
            # 判断下一行是否是纯 '}'
            next_is_close_brace = False
            if i + 1 < len(lines) and lines[i + 1].strip() == '}':
                next_is_close_brace = True

            # 判断当前行内容
            if content == '}':
                # 纯 '}' 行：不输入任何内容
                # 上一行输入完后光标在行尾，按 Down 到 } 行
                pyautogui.press('down')
                # 光标在 } 后面（Down 在短行时跳到行尾）
                prev_indent = current_indent
                continue

            else:
                # 普通代码行或 else { 等
                pyautogui.press('return')
                time.sleep(0.05)  # 等待 IDE 自动缩进

                # 缩进策略 B：只在回退时修正
                if current_indent < prev_indent:
                    # 缩进回退，需要修正
                    pyautogui.press('home')  # 跳到行首
                    pyautogui.typewrite(' ' * current_indent, interval=0.01)

                # 输入代码内容（处理 {} 同一行的情况）
                _type_content_with_braces(content)

        prev_indent = current_indent

    print("代码输入完成！")


def _type_content(text):
    """普通内容输入（无特殊括号处理）"""
    pyautogui.typewrite(text, interval=0.01)


def _type_content_with_braces(text):
    """
    输入内容，处理 {} 在同一行的情况

    遇到 '{' 时：
    - IDE 自动补全 '}'
    - 继续输入 {} 中间的内容
    - 按 Right 跳过 IDE 自动补全的 '}'
    - 继续输入 } 后面的内容
    """
    i = 0
    while i < len(text):
        char = text[i]

        if char == '{':
            # 输入 {，IDE 自动补全 }
            pyautogui.typewrite('{', interval=0.01)

            # 找同一行内匹配的 }
            brace_depth = 1
            j = i + 1
            while j < len(text) and brace_depth > 0:
                if text[j] == '{':
                    brace_depth += 1
                elif text[j] == '}':
                    brace_depth -= 1
                j += 1

            if brace_depth == 0:
                # 找到匹配的 }，在同一行内
                # 输入 {} 中间的内容
                middle = text[i + 1:j - 1]
                if middle:
                    pyautogui.typewrite(middle, interval=0.01)

                # 按 Right 跳过 IDE 自动补全的 }
                pyautogui.press('right')

                # 继续处理 } 后面的内容
                i = j
                continue

        elif char == '}':
            # 跨行场景的 }，不应该出现在这里
            # 跳过（由 IDE 自动补全）
            pass

        else:
            pyautogui.typewrite(char, interval=0.01)

        i += 1


# ========== 使用示例 ==========
if __name__ == '__main__':
    type_java_code('java_code.txt')