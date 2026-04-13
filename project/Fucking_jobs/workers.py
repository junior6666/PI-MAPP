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
            self.listener.stop()


class OCRWorker(QThread):
    """OCR 工作线程 - 文字识别"""
    
    ocr_completed = Signal(str, float)   # OCR 完成信号，参数为识别文本和耗时（秒）
    error_occurred = Signal(str)   # 错误信号
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        
    def run(self):
        """运行 OCR 识别"""
        try:
            # 检查文件是否存在
            if not os.path.exists(self.image_path):
                self.error_occurred.emit(f"图片文件不存在: {self.image_path}")
                return
            
            start_time = time.time()
            
            # 初始化 OCR 阅读器
            reader = easyocr.Reader(['ch_sim', 'en'])
            
            # 执行识别
            result = reader.readtext(self.image_path)
            
            # 提取文本
            texts = [text for bbox, text, prob in result]
            full_text = '\n'.join(texts)
            
            elapsed_time = time.time() - start_time
            
            # 发送信号
            self.ocr_completed.emit(full_text, elapsed_time)
            
        except Exception as e:
            self.error_occurred.emit(f"OCR 识别失败: {str(e)}")


class LLMWorker(QThread):
    """LLM 工作线程 - 调用大语言模型 API"""
    
    llm_completed = Signal(str, float)   # LLM 完成信号，参数为响应文本和耗时（秒）
    error_occurred = Signal(str)   # 错误信号
    
    def __init__(self, api_key, model, prompt):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.prompt = prompt
        
    def run(self):
        """调用 LLM API"""
        try:
            start_time = time.time()
            
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
            
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            elapsed_time = time.time() - start_time
            
            # 提取回复内容
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                self.llm_completed.emit(content, elapsed_time)
            else:
                self.error_occurred.emit("LLM API 返回格式异常")
                
        except requests.exceptions.Timeout:
            self.error_occurred.emit("LLM API 请求超时，请重试")
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"LLM API 请求失败: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"LLM 调用失败: {str(e)}")


class KimiWorker(QThread):
    """Kimi 工作线程 - 调用 Kimi API 进行图片分析"""
    
    kimi_completed = Signal(str, float)   # Kimi 完成信号，参数为响应文本和耗时（秒）
    error_occurred = Signal(str)   # 错误信号
    
    def __init__(self, api_key, image_path, prompt):
        super().__init__()
        self.api_key = api_key
        self.image_path = image_path
        self.prompt = prompt
        
    def run(self):
        """调用 Kimi API"""
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
            
            # 创建 OpenAI 客户端
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.moonshot.cn/v1",
            )
            
            # 调用 API
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
            
            elapsed_time = time.time() - start_time
            
            # 提取回复内容
            content = completion.choices[0].message.content
            self.kimi_completed.emit(content, elapsed_time)
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"Kimi API 错误详情:\n{error_detail}")
            self.error_occurred.emit(f"Kimi API 调用失败: {str(e)}")


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
    
    async def send_message_async(self, message: str):
        """异步发送消息到所有客户端"""
        if not self.clients:
            print("[!] 没有已连接的设备")
            return
        
        disconnected = set()
        
        for client in self.clients:
            try:
                await client.send(message)
                print(f"[→] 消息已发送")
            except Exception as e:
                print(f"[✗] 发送失败: {e}")
                disconnected.add(client)
        
        # 移除断开的客户端
        for client in disconnected:
            self.clients.discard(client)
    
    def send_message(self, message: str):
        """发送消息（从主线程调用）"""
        if self.loop and self.loop.is_running():
            # 在事件循环中调度协程
            asyncio.run_coroutine_threadsafe(
                self.send_message_async(message),
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
                    for client in self.clients:
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
