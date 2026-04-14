"""
工作线程模块 - 包含所有后台任务的线程类
"""

import mss
from PIL import Image
from pynput import keyboard
import time
from datetime import datetime
import os
import threading
import easyocr
import requests
import asyncio
import websockets
import socket
from PySide6.QtCore import QThread, Signal, Slot
import warnings
warnings.filterwarnings('ignore', message=".*pin_memory.*")

class ScreenshotWorker(QThread):
    """截图工作线程 - 监听热键并截图"""
    
    screenshot_taken = Signal(str)  # 截图完成信号，参数为图片路径
    error_occurred = Signal(str)     # 错误信号
    
    def __init__(self, hotkey="<alt>+x", save_dir="./screenshots"):
        super().__init__()
        self.hotkey = hotkey
        self.save_dir = save_dir
        self.enabled = True
        self.listener = None
        self.capture_lock = threading.Lock()
        # 确保保存目录存在
        os.makedirs(save_dir, exist_ok=True)
        
    def run(self):
        """运行线程"""
        try:
            # 注册热键
            self.listener = keyboard.GlobalHotKeys({
                self.hotkey: self._on_hotkey
            })
            self.listener.start()
            
            # 保持线程运行
            while self.enabled:
                self.msleep(100)
                
        except Exception as e:
            self.error_occurred.emit(f"截图监听失败: {str(e)}")
        finally:
            if self.listener:
                self.listener.stop()
    
    def _on_hotkey(self):
        """热键触发回调"""
        if not self.enabled:
            return
        
        with self.capture_lock:
            sct_instance = None
            try:
                # 创建新的 mss 实例（线程安全）
                sct_instance = mss.mss()
                
                # 截取主显示器
                monitor = sct_instance.monitors[1]
                screenshot = sct_instance.grab(monitor)
                
                # 转换为 PIL Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                filename = f"screenshot_{timestamp}.png"
                filepath = os.path.join(self.save_dir, filename)
                
                # 保存截图
                img.save(filepath)
                
                # 发送信号
                self.screenshot_taken.emit(filepath)
                
            except Exception as e:
                self.error_occurred.emit(f"截图失败: {str(e)}")
            finally:
                if sct_instance:
                    sct_instance.close()
    
    def stop(self):
        """停止监听"""
        self.enabled = False
        if self.listener:
            try:
                self.listener.stop()
            except:
                pass
        self.wait(2000)  # 等待线程结束


class OCRWorker(QThread):
    """OCR 工作线程 - 文字识别（使用单例 Reader 避免内存泄漏）"""

    ocr_completed = Signal(str, float)  # OCR 完成信号，参数为识别文本和耗时（秒）
    error_occurred = Signal(str)  # 错误信号
    
    # 类级别的单例 Reader（避免重复加载模型导致内存泄漏）
    _reader_instance = None
    _reader_lock = threading.Lock()

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self._interrupted = False
    
    @classmethod
    def get_reader(cls):
        """获取或创建 OCR Reader 单例"""
        if cls._reader_instance is None:
            with cls._reader_lock:
                # 双重检查锁定
                if cls._reader_instance is None:
                    print("🔍 正在初始化 OCR 引擎（首次加载，可能需要几秒）...")
                    try:
                        # 禁用 verbose 输出，减少日志干扰
                        cls._reader_instance = easyocr.Reader(
                            ['ch_sim', 'en'], 
                            gpu=False,  # 强制使用 CPU
                            verbose=False,
                            download_enabled=True
                        )
                        print("✅ OCR 引擎初始化完成")
                    except Exception as e:
                        print(f"❌ OCR 引擎初始化失败: {e}")
                        raise
        return cls._reader_instance
    
    @classmethod
    def cleanup_reader(cls):
        """清理 OCR Reader（程序退出时调用）"""
        if cls._reader_instance is not None:
            with cls._reader_lock:
                if cls._reader_instance is not None:
                    try:
                        del cls._reader_instance
                        cls._reader_instance = None
                        print("🗑️ OCR 引擎已清理")
                    except:
                        pass

    def run(self):
        """运行 OCR 识别"""
        reader = None
        try:
            # 检查文件是否存在
            if not os.path.exists(self.image_path):
                self.error_occurred.emit(f"图片文件不存在: {self.image_path}")
                return

            start_time = time.time()

            # 获取单例 Reader
            reader = self.get_reader()
            
            # 检查是否已被中断
            if self._interrupted:
                print("⚠️ OCR 任务在开始前已被中断")
                return

            # 执行识别（设置较短的超时时间）
            # 注意：easyocr 不支持原生中断，所以我们依赖线程终止
            result = reader.readtext(
                self.image_path,
                paragraph=False,  # 不合并段落，提高速度
                detail=0,  # 只返回文本，不返回坐标和置信度
                batch_size=1  # 单张图片处理
            )

            # 检查是否被中断
            if self._interrupted:
                print("⚠️ OCR 任务已被中断")
                return

            # 提取文本（detail=0 时直接返回文本列表）
            if isinstance(result, list) and len(result) > 0:
                full_text = '\n'.join(result)
            else:
                full_text = ""

            elapsed_time = time.time() - start_time

            # 再次检查是否被中断
            if self._interrupted:
                print("⚠️ OCR 任务已被中断（后处理阶段）")
                return

            # 发送信号
            self.ocr_completed.emit(full_text, elapsed_time)

        except Exception as e:
            if not self._interrupted:
                import traceback
                error_detail = traceback.format_exc()
                print(f"OCR 错误详情:\n{error_detail}")
                self.error_occurred.emit(f"OCR 识别失败: {str(e)}")
            else:
                print("✅ OCR 任务已安全中断")
        finally:
            # 注意：不要在这里删除 reader，它是单例
            pass

    def interrupt(self):
        """中断当前任务"""
        self._interrupted = True
        print("🛑 OCR 任务收到中断信号")
        # 注意：由于 easyocr 不支持原生中断，我们依赖主程序的 terminate()
        # 这里只是设置标志位，实际中断由线程终止完成


class LLMWorker(QThread):
    """LLM 工作线程 - 调用大语言模型 API（支持安全中断）"""

    llm_completed = Signal(str, float)  # LLM 完成信号，参数为响应文本和耗时（秒）
    error_occurred = Signal(str)  # 错误信号

    def __init__(self, api_key, model, prompt):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.prompt = prompt
        self._interrupted = False
        self._session = None  # 用于管理 requests session

    def run(self):
        """调用 LLM API"""
        self._session = None
        try:
            start_time = time.time()

            # 创建 Session 以便更好地控制连接
            self._session = requests.Session()
            
            url = "https://api.longcat.chat/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": self.prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.7
            }

            # 检查是否已被中断
            if self._interrupted:
                print("⚠️ LLM 任务在请求前已被中断")
                return

            # 发送请求（设置合理的超时）
            response = self._session.post(
                url, 
                headers=headers, 
                json=data, 
                timeout=(10, 60)  # (连接超时, 读取超时)
            )
            response.raise_for_status()

            # 检查是否被中断
            if self._interrupted:
                print("⚠️ LLM 任务已被中断")
                return

            result = response.json()

            elapsed_time = time.time() - start_time

            # 提取回复内容
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']

                # 最后检查是否被中断
                if self._interrupted:
                    print("⚠️ LLM 任务已被中断（结果处理阶段）")
                    return

                self.llm_completed.emit(content, elapsed_time)
            else:
                if not self._interrupted:
                    self.error_occurred.emit("LLM API 返回格式异常")

        except requests.exceptions.Timeout:
            if not self._interrupted:
                self.error_occurred.emit("LLM API 请求超时，请重试")
        except requests.exceptions.ConnectionError:
            if not self._interrupted:
                self.error_occurred.emit("LLM API 连接失败，请检查网络")
        except requests.exceptions.RequestException as e:
            if not self._interrupted:
                # 忽略因中断导致的异常
                if "Interrupted function call" not in str(e):
                    self.error_occurred.emit(f"LLM API 请求失败: {str(e)}")
        except Exception as e:
            if not self._interrupted:
                import traceback
                error_detail = traceback.format_exc()
                print(f"LLM 错误详情:\n{error_detail}")
                self.error_occurred.emit(f"LLM 调用失败: {str(e)}")
        finally:
            # 清理 Session
            if self._session:
                try:
                    self._session.close()
                except:
                    pass
                self._session = None

    def interrupt(self):
        """中断当前任务"""
        self._interrupted = True
        print("🛑 LLM 任务收到中断信号")
        # 关闭 Session 以中断正在进行的请求
        if self._session:
            try:
                self._session.close()
            except:
                pass

class KimiWorker(QThread):
    """Kimi 工作线程 - 调用 Kimi API 进行图片分析（支持后备模型+智能降级）"""
    
    kimi_completed = Signal(str, float)   # Kimi 完成信号，参数为响应文本和耗时(秒)
    error_occurred = Signal(str)   # 错误信号
    
    # 后备模型列表（当主模型失败时依次尝试）
    BACKUP_MODELS = [
        'Qwen/Qwen3-Omni-30B-A3B-Instruct',
        'Qwen/Qwen3-VL-8B-Instruct',
        'Qwen/Qwen3-VL-32B-Instruct',
        'Qwen/Qwen3-VL-235B-A22B-Instruct',
        'zai-org/GLM-4.5V',
        'Pro/moonshotai/Kimi-K2.5'
    ]
    
    # SiliconFlow API 配置
    SILICONFLOW_API_KEY = "sk-lhxzzjsezqnknpsjjgiyuzlbkiesxzyosmrcwzdgmvdknvln"
    SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
    
    # 类级别计数器：记录主模型连续失败次数（跨线程实例共享）
    _primary_model_fail_count = 0
    _primary_model_fail_threshold = 2  # 连续失败阈值
    _switched_to_backup = False  # 是否已切换到备选模型
    _current_backup_index = 0  # 当前使用的备选模型索引
    _backup_success_count = 0  # 备选模型连续成功次数
    _backup_success_threshold = 10  # 备选模型连续成功阈值（用于尝试恢复主模型）
    _auto_recovery_enabled = True  # 启用自动恢复机制
    
    def __init__(self, api_key, image_path, prompt):
        super().__init__()
        self.api_key = api_key
        self.image_path = image_path
        self.prompt = prompt
        self._interrupted = False

    def run(self):
        """调用 Kimi API（失败时自动切换备选模型）"""
        client = None
        try:
            import base64
            from openai import OpenAI

            start_time = time.time()

            # 检查文件是否存在
            if not os.path.exists(self.image_path):
                self.error_occurred.emit(f"图片文件不存在: {self.image_path}")
                return

            # 读取并编码图片
            with open(self.image_path, "rb") as f:
                image_data = f.read()

            # 获取图片扩展名
            ext = os.path.splitext(self.image_path)[1].lstrip('.')
            image_url = f"data:image/{ext};base64,{base64.b64encode(image_data).decode('utf-8')}"

            # 智能模型选择策略
            use_primary_model = False

            # 情况1：未切换状态，尝试主模型
            if not self._switched_to_backup:
                use_primary_model = True

            # 情况2：已切换状态，但备选模型连续成功达到阈值，尝试恢复主模型
            elif (self._switched_to_backup and
                  self._backup_success_count >= self._backup_success_threshold and
                  self._auto_recovery_enabled):
                print(f"🔍 备选模型已连续成功 {self._backup_success_count} 次，尝试恢复主模型...")
                self._switched_to_backup = False
                self._primary_model_fail_count = 0  # 重置失败计数
                self._backup_success_count = 0  # 重置成功计数
                use_primary_model = True

            # 执行调用逻辑
            if use_primary_model:
                # 尝试主模型
                try:
                    print(f"🤖 正在调用主模型: Kimi-K2.5 (Moonshot)")
                    client = OpenAI(
                        api_key=self.api_key,
                        base_url="https://api.moonshot.cn/v1",
                        timeout=60  # 设置超时
                    )
                    
                    # 检查是否已被中断
                    if self._interrupted:
                        print("⚠️ Kimi 任务在调用前已被中断")
                        return
                    
                    completion = client.chat.completions.create(
                        model="kimi-k2.5",
                        messages=[
                            {"role": "system", "content": "你是专业的面试助手。"},
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": image_url,
                                        },
                                    },
                                    {
                                        "type": "text",
                                        "text": self.prompt,
                                    },
                                ],
                            },
                        ],
                    )
                    
                    content = completion.choices[0].message.content

                    # 检查是否被中断
                    if self._interrupted:
                        print("⚠️ Kimi 任务已被中断")
                        return

                    elapsed_time = time.time() - start_time
                    print(f"✅ Kimi 主模型调用成功 (耗时: {elapsed_time:.2f}s)")

                    # 主模型成功，重置失败计数
                    self.__class__._primary_model_fail_count = 0
                    self.__class__._backup_success_count = 0  # 重置备选成功计数
                    self.kimi_completed.emit(content, elapsed_time)
                    return

                except Exception as e:
                    if self._interrupted:
                        print("✅ Kimi 任务已安全中断")
                        return
                    print(f"⚠️ 主模型 Kimi 调用失败: {str(e)}")
                    # 增加失败计数
                    self.__class__._primary_model_fail_count += 1

                    # 检查是否达到阈值
                    if self.__class__._primary_model_fail_count >= self.__class__._primary_model_fail_threshold:
                        print(f"🚨 主模型连续失败 {self.__class__._primary_model_fail_count} 次，永久切换至备选模型！")
                        self.__class__._switched_to_backup = True
                        self.__class__._backup_success_count = 0  # 重置备选成功计数
                    else:
                        remaining = self.__class__._primary_model_fail_threshold - self.__class__._primary_model_fail_count
                        print(
                            f"⏳ 主模型失败次数: {self.__class__._primary_model_fail_count}/{self.__class__._primary_model_fail_threshold} (还需{remaining}次失败将切换)")

                    # 切换至备选模型重试（效率优先：不重试主模型）
                    backup_index = self.__class__._current_backup_index
                    model = self.BACKUP_MODELS[backup_index]

            # 使用备选模型（已切换或主模型失败）
            if not use_primary_model or (use_primary_model and self._primary_model_fail_count > 0):
                # 选择备选模型
                backup_index = self.__class__._current_backup_index
                model = self.BACKUP_MODELS[backup_index]

                try:
                    print(f"🤖 使用备选模型 {backup_index + 1}/{len(self.BACKUP_MODELS)}: {model}")
                    
                    # 创建客户端
                    client = OpenAI(
                        api_key=self.SILICONFLOW_API_KEY,
                        base_url=self.SILICONFLOW_BASE_URL,
                        timeout=60
                    )
                    
                    # 检查是否已被中断
                    if self._interrupted:
                        print("⚠️ Kimi 任务在备选模型调用前已被中断")
                        return
                    
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": image_url
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": self.prompt
                                    }
                                ]
                            }
                        ]
                    )
                    
                    content = response.choices[0].message.content

                    # 检查是否被中断
                    if self._interrupted:
                        print("⚠️ Kimi 任务已被中断")
                        return

                    total_elapsed = time.time() - start_time
                    print(f"✅ 备选模型调用成功 (耗时: {total_elapsed:.2f}s)")

                    # 备选模型成功，更新状态
                    self.__class__._backup_success_count += 1
                    self.__class__._current_backup_index = (backup_index + 1) % len(self.BACKUP_MODELS)

                    # 在结果前添加使用的模型信息
                    result_with_model = f"[使用模型: {model}]\n\n{content}"
                    self.kimi_completed.emit(result_with_model, total_elapsed)
                    return

                except Exception as e:
                    if self._interrupted:
                        print("✅ Kimi 任务已安全中断")
                        return
                    print(f"⚠️ 备选模型 {model} 调用失败: {str(e)}")
                    # 备选模型也失败，重置成功计数，尝试下一个
                    self.__class__._backup_success_count = 0
                    self.__class__._current_backup_index = (backup_index + 1) % len(self.BACKUP_MODELS)

            # 所有尝试都失败
            if not self._interrupted:
                self.error_occurred.emit(f"所有模型均调用失败（主模型 + 备选模型）")
            else:
                print("✅ Kimi 任务已安全中断")

        except Exception as e:
            if self._interrupted:
                print("✅ Kimi 任务已安全中断")
                return
            import traceback
            error_detail = traceback.format_exc()
            print(f"Kimi 工作线程错误详情:\n{error_detail}")
            self.error_occurred.emit(f"图片分析失败: {str(e)}")
        finally:
            # 清理客户端
            client = None

    def interrupt(self):
        """中断当前任务"""
        self._interrupted = True
        print("🛑 Kimi 任务收到中断信号")
        # 注意：OpenAI SDK 不支持原生中断，依赖线程终止
    
    @classmethod
    def reset_model_state(cls):
        """重置所有模型状态（可用于手动恢复主模型）"""
        cls._primary_model_fail_count = 0
        cls._switched_to_backup = False
        cls._current_backup_index = 0
        cls._backup_success_count = 0
        print("🔄 KimiWorker 模型状态已重置，将重新尝试主模型")
    
    @classmethod
    def force_use_primary(cls):
        """强制使用主模型（忽略失败计数）"""
        cls._primary_model_fail_count = 0
        cls._switched_to_backup = False
        cls._backup_success_count = 0
        print("⚡ 已强制切换至主模型")


class WebSocketServerWorker(QThread):
    """WebSocket 服务器工作线程 - 局域网通信"""
    
    client_connected = Signal()      # 客户端连接信号
    client_disconnected = Signal()   # 客户端断开信号
    message_sent = Signal()          # 消息发送信号
    error_occurred = Signal(str)     # 错误信号
    
    def __init__(self, port=8765):
        super().__init__()
        self.port = port
        self.is_running = False
        self.server = None
        self.clients = set()
        self.loop = None
    
    async def handler(self, websocket):
        """处理客户端连接"""
        self.clients.add(websocket)
        client_ip = websocket.remote_address[0]
        print(f"[+] 手机已连接: {client_ip}")
        
        try:
            # 发送欢迎消息
            await websocket.send("✅ 已连接到 PC 端！等待接收消息...")
            
            # 保持连接
            async for message in websocket:
                print(f"[←] 收到手机消息: {message}")
                await websocket.send("已收到!")
                
        except websockets.exceptions.ConnectionClosed:
            print(f"[-] 手机断开: {client_ip}")
        finally:
            self.clients.discard(websocket)
    
    async def send_message_async(self, message: str, silent: bool = False):
        """异步发送消息到所有客户端
        
        Args:
            message: 要发送的消息
            silent: 是否静默发送（不打印日志）
        """
        if not self.clients:
            if not silent:
                print("[!] 没有已连接的设备")
            return
        
        disconnected = set()
        
        for client in self.clients:
            try:
                await client.send(message)
                if not silent:
                    print(f"[→] 消息已发送")
            except Exception as e:
                if not silent:
                    print(f"[✗] 发送失败: {e}")
                disconnected.add(client)
        
        # 移除断开的客户端
        for client in disconnected:
            self.clients.discard(client)
    
    def send_message(self, message: str, silent: bool = False):
        """发送消息（从主线程调用）
        
        Args:
            message: 要发送的消息
            silent: 是否静默发送（不打印日志）
        """
        if self.loop and self.loop.is_running():
            # 在事件循环中调度协程
            asyncio.run_coroutine_threadsafe(
                self.send_message_async(message, silent),
                self.loop
            )
    
    def get_local_ip(self):
        """获取本机局域网 IP"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
        except:
            return '127.0.0.1'
        finally:
            s.close()
    
    @property
    def has_clients(self):
        """检查是否有客户端连接"""
        return len(self.clients) > 0
    
    def run(self):
        """运行 WebSocket 服务器"""
        try:
            # 创建新的事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # 获取本机 IP
            local_ip = self.get_local_ip()
            print(f"WebSocket 服务器启动在 ws://{local_ip}:{self.port}")
            
            # 在事件循环中创建服务器
            async def start_server():
                server = await websockets.serve(self.handler, "0.0.0.0", self.port)
                return server
            
            # 启动服务器
            self.server = self.loop.run_until_complete(start_server())
            
            # 标记为运行状态
            self.is_running = True
            
            # 打印访问信息
            print(f"=" * 50)
            print(f"WebSocket 服务器已启动!")
            print(f"本机IP: {local_ip}")
            print(f"手机访问: ws://{local_ip}:{self.port}")
            print(f"=" * 50)
            
            # 运行事件循环
            self.loop.run_forever()
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"WebSocket 错误详情:\n{error_detail}")
            # 只在非运行时错误时才发射信号
            if "no running event loop" not in str(e):
                self.error_occurred.emit(f"WebSocket 服务器启动失败: {str(e)}")
        finally:
            self.is_running = False
            # 清理事件循环
            if self.loop and self.loop.is_running():
                self.loop.stop()
            if self.loop:
                self.loop.close()
    
    def stop(self):
        """停止服务器"""
        self.is_running = False
        
        if self.loop and self.loop.is_running():
            # 在事件循环中执行关闭操作
            async def cleanup():
                # 关闭所有客户端连接
                if self.clients:
                    close_tasks = []
                    for client in list(self.clients):  # 创建副本避免迭代时修改
                        try:
                            close_tasks.append(asyncio.ensure_future(client.close()))
                        except:
                            pass
                    if close_tasks:
                        await asyncio.gather(*close_tasks, return_exceptions=True)
                    self.clients.clear()
                
                # 关闭服务器
                if self.server:
                    self.server.close()
                    await self.server.wait_closed()
                
                # 停止事件循环
                self.loop.stop()
            
            try:
                # 在线程安全的上下文中执行清理
                future = asyncio.run_coroutine_threadsafe(cleanup(), self.loop)
                future.result(timeout=3)  # 等待最多3秒
            except Exception as e:
                print(f"WebSocket 清理警告: {e}")
                # 强制停止
                try:
                    self.loop.call_soon_threadsafe(self.loop.stop)
                except:
                    pass
        
        # 关闭事件循环
        if self.loop:
            try:
                if not self.loop.is_closed():
                    self.loop.close()
            except:
                pass
        
        self.wait(3000)  # 等待线程结束
