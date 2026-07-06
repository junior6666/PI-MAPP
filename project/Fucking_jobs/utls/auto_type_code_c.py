import pyautogui
import time


def type_c_code(code_path):
    """
    模拟人工逐字符输入 C 语言代码到 LeetCode 编辑器

    参数:
        code_path: C 代码文件路径 (如 'code_c.txt')

    核心处理逻辑:
    1. 花括号: 代码结构中的 '}' 不输入（IDE 自动补全），但需移动光标
    2. 缩进: 信任 IDE 自动缩进，只在缩进回退时修正
    3. 字符/字符串字面量: 其中的 '{' '(' '[' 原样输入，但需删除 IDE 自动补全的对应右括号
    4. 数组初始化: {} 必须在同一行内完成

    限制说明:
    - 不支持嵌套数组初始化跨多行
    - 代码中不应包含注释
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

    prev_indent = 0

    for i, line in enumerate(lines):
        current_indent = len(line) - len(line.lstrip())
        content = line.lstrip()

        if i == 0:
            _type_content_with_states(content)
        else:
            if content == '}':
                pyautogui.press('down')
                prev_indent = current_indent
                continue

            elif content.startswith('}') and content != '}':
                pyautogui.press('down')
                after_brace = content[1:]
                _type_content_with_states(after_brace)
                prev_indent = current_indent
                continue

            else:
                pyautogui.press('return')
                time.sleep(0.05)

                if current_indent < prev_indent:
                    pyautogui.press('home')
                    pyautogui.typewrite(' ' * current_indent, interval=0.01)

                _type_content_with_states(content)

        prev_indent = current_indent

    print("C 代码输入完成！")


def _delete_auto_close_bracket():
    """
    删除 IDE 自动补全的多余右括号
    操作: Right (右移到括号后) + Backspace (删除前面的括号)
    """
    pyautogui.press('right')
    pyautogui.press('backspace')


def _type_content_with_states(text):
    """
    输入内容，支持状态机处理字符/字符串字面量中的花括号

    状态:
        NORMAL: 正常代码，'{' 触发 IDE 补全 '}'，'}' 跳过
        IN_CHAR: 字符字面量 '...' 中，'{' '(' '[' 原样输入但删除 IDE 自动补全
        IN_CHAR_ESCAPE: 字符转义中，下一个字符原样输入
        IN_STRING: 字符串字面量 "..." 中，'{' '(' '[' 原样输入但删除 IDE 自动补全
        IN_STRING_ESCAPE: 字符串转义中，下一个字符原样输入
    """
    state = 'NORMAL'
    i = 0

    while i < len(text):
        char = text[i]

        # ========== NORMAL ==========
        if state == 'NORMAL':
            if char == "'":
                pyautogui.typewrite(char, interval=0.01)
                state = 'IN_CHAR'
                i += 1
                continue

            elif char == '"':
                pyautogui.typewrite(char, interval=0.01)
                state = 'IN_STRING'
                i += 1
                continue

            elif char == '{':
                pyautogui.typewrite('{', interval=0.01)

                brace_depth = 1
                j = i + 1
                while j < len(text) and brace_depth > 0:
                    if text[j] == '{':
                        brace_depth += 1
                    elif text[j] == '}':
                        brace_depth -= 1
                    j += 1

                if brace_depth == 0:
                    middle = text[i + 1:j - 1]
                    if middle:
                        _type_content_with_states(middle)
                    pyautogui.press('right')
                    i = j
                    continue

            elif char == '}':
                pass

            else:
                pyautogui.typewrite(char, interval=0.01)

        # ========== IN_CHAR ==========
        elif state == 'IN_CHAR':
            pyautogui.typewrite(char, interval=0.01)

            if char == '\\':
                state = 'IN_CHAR_ESCAPE'

            elif char == "'":
                # 退出字符字面量，Monaco 智能跳过自动补全的 '
                state = 'NORMAL'

            elif char in '({[':
                # 在字符字面量中输入 { ( [，IDE 自动补全 } ) ]
                # 右移然后 Backspace 删除
                _delete_auto_close_bracket()

        # ========== IN_CHAR_ESCAPE ==========
        elif state == 'IN_CHAR_ESCAPE':
            pyautogui.typewrite(char, interval=0.01)
            state = 'IN_CHAR'

        # ========== IN_STRING ==========
        elif state == 'IN_STRING':
            pyautogui.typewrite(char, interval=0.01)

            if char == '\\':
                state = 'IN_STRING_ESCAPE'

            elif char == '"':
                # 退出字符串字面量，Monaco 智能跳过自动补全的 "
                state = 'NORMAL'

            elif char in '({[':
                # 在字符串字面量中输入 { ( [，IDE 自动补全 } ) ]
                # 右移然后 Backspace 删除
                _delete_auto_close_bracket()

        # ========== IN_STRING_ESCAPE ==========
        elif state == 'IN_STRING_ESCAPE':
            pyautogui.typewrite(char, interval=0.01)
            state = 'IN_STRING'

        i += 1


# ========== 使用示例 ==========
if __name__ == '__main__':
    type_c_code('c_code.txt')