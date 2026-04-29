"""
工作线程模块 - 包含所有后台任务的线程类
"""
import random
import json
import base64

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
import subprocess
import signal
import logging
import sys
import winreg
from PySide6.QtWidgets import QApplication as QtApp
from PySide6.QtCore import QThread, Signal
import warnings
warnings.filterwarnings('ignore', message=".*pin_memory.*")

class ScreenshotWorker(QThread):
    """截图工作线程 - 监听热键并截图"""
    
    screenshot_taken = Signal(str)  # 截图完成信号，参数为图片路径
    error_occurred = Signal(str)     # 错误信号
    
    # 类级别的手机照片管理（跨实例共享）
    _phone_photo_index = 0  # 当前图片索引（从0开始）
    _phone_photo_list = []  # 当前批次的图片列表
    _current_folder = None  # 当前文件夹路径
    _last_check_time = 0  # 上次检查文件夹的时间戳
    
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
            try:
                # 检查图片来源配置
                image_source = self._get_image_source_config()
                
                if image_source == 'phone':
                    # 使用手机拍照来源
                    filepath = self._get_latest_phone_photo()
                    if filepath:
                        print(f"📱 Case1 使用手机拍照: {os.path.basename(filepath)}")
                        self.screenshot_taken.emit(filepath)
                    else:
                        self.error_occurred.emit("手机拍照目录为空或不存在！\n请通过手机发送图片或切换到 PC 截图模式。")
                else:
                    # 使用 PC 屏幕截图（默认）
                    self._capture_pc_screenshot()
                    
            except Exception as e:
                self.error_occurred.emit(f"截图失败: {str(e)}")
    
    def _get_image_source_config(self):
        """获取图片来源配置"""
        try:
            import json
            # 使用 sys.executable 的目录作为基准，兼容打包环境
            if getattr(sys, 'frozen', False):
                # 打包后：使用 exe 所在目录
                base_dir = os.path.dirname(sys.executable)
            else:
                # 开发环境：使用当前工作目录
                base_dir = os.getcwd()
            
            config_file = os.path.join(base_dir, 'global_config.json')
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return config_data.get('image_source', 'pc')
            else:
                return 'pc'  # 默认使用 PC 截图
        except Exception as e:
            print(f"⚠️ 读取图片来源配置失败: {e}，使用默认值")
            return 'pc'
    
    def _get_latest_phone_photo(self):
        """获取最新的手机拍照图片路径（每次调用都重新检测最新文件夹）"""
        try:
            import time
            
            # 使用 sys.executable 的目录作为基准，兼容打包环境
            if getattr(sys, 'frozen', False):
                # 打包后：使用 exe 所在目录
                base_dir = os.path.dirname(sys.executable)
            else:
                # 开发环境：使用当前工作目录
                base_dir = os.getcwd()
            
            phone_photo_dir = os.path.join(base_dir, 'phone_photo')
            
            if not os.path.exists(phone_photo_dir):
                return None
            
            # 查找所有图片文件夹
            folders = [f for f in os.listdir(phone_photo_dir) 
                      if os.path.isdir(os.path.join(phone_photo_dir, f))]
            
            if not folders:
                return None
            
            # 按文件夹名称排序（时间戳格式确保正确排序），获取最新的文件夹
            folders.sort(reverse=True)
            latest_folder = folders[0]
            folder_path = os.path.join(phone_photo_dir, latest_folder)
            
            # 每次都重新加载最新文件夹的图片列表（确保获取最新上传的图片）
            # 查找文件夹中的图片文件
            image_files = [f for f in os.listdir(folder_path) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'))]
            
            if not image_files:
                print(f"⚠️ 文件夹 {latest_folder} 中没有图片")
                return None
            
            # 按文件名自然排序（确保 1.png, 2.png, 10.png 顺序正确）
            def natural_sort_key(filename):
                """自然排序键函数，处理数字部分"""
                import re
                parts = re.split(r'(\d+)', filename)
                return [int(p) if p.isdigit() else p.lower() for p in parts]
            
            image_files.sort(key=natural_sort_key)
            
            # 构建完整的图片路径列表
            new_photo_list = [
                os.path.join(folder_path, img) for img in image_files
            ]
            
            # 检查是否切换了文件夹
            folder_changed = (self.__class__._current_folder != folder_path)
            
            if folder_changed:
                # 新文件夹，重置索引为0（显示第1张图片）
                self.__class__._current_folder = folder_path
                self.__class__._phone_photo_index = 0
                self.__class__._phone_photo_list = new_photo_list
                print(f"📱 检测到新文件夹: {latest_folder} (共{len(new_photo_list)}张)，从第1张开始")
            else:
                # 同一文件夹，检查是否有新图片上传
                if len(new_photo_list) != len(self.__class__._phone_photo_list):
                    # 图片数量变化，更新列表但保持当前索引位置
                    old_len = len(self.__class__._phone_photo_list)
                    new_len = len(new_photo_list)
                    
                    # 保持当前索引，但如果索引超出范围则调整
                    if self.__class__._phone_photo_index >= new_len:
                        self.__class__._phone_photo_index = max(0, new_len - 1)
                    
                    self.__class__._phone_photo_list = new_photo_list
                    print(f"📱 文件夹 {latest_folder} 图片数量变化: {old_len} -> {new_len} 张")
            
            # 检查列表是否为空
            if not self.__class__._phone_photo_list:
                return None
            
            # 返回当前索引的图片
            current_index = self.__class__._phone_photo_index % len(self.__class__._phone_photo_list)
            image_path = self.__class__._phone_photo_list[current_index]
            
            return image_path
            
        except Exception as e:
            import traceback
            print(f"❌ 获取手机拍照失败: {e}")
            print(traceback.format_exc())
            return None
    
    @classmethod
    def get_next_phone_photo(cls):
        """切换到下一张手机照片（循环）- 每次都重新检测最新文件夹"""
        try:
            import re
            
            # 获取基准目录
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.getcwd()
            
            phone_photo_dir = os.path.join(base_dir, 'phone_photo')
            
            if not os.path.exists(phone_photo_dir):
                print("⚠️ 手机拍照目录不存在")
                return None
            
            # 查找所有图片文件夹
            folders = [f for f in os.listdir(phone_photo_dir) 
                      if os.path.isdir(os.path.join(phone_photo_dir, f))]
            
            if not folders:
                print("⚠️ 没有可用的图片文件夹")
                return None
            
            # 按文件夹名称排序，获取最新的文件夹
            folders.sort(reverse=True)
            latest_folder = folders[0]
            folder_path = os.path.join(phone_photo_dir, latest_folder)
            
            # 检查是否切换了文件夹
            folder_changed = (cls._current_folder != folder_path)
            
            if folder_changed:
                # 新文件夹，重置索引为0（从第1张开始）
                cls._current_folder = folder_path
                cls._phone_photo_index = 0
                
                # 查找文件夹中的图片文件
                image_files = [f for f in os.listdir(folder_path) 
                              if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'))]
                
                if not image_files:
                    print(f"⚠️ 文件夹 {latest_folder} 中没有图片")
                    return None
                
                # 按文件名自然排序（确保 1.png, 2.png, 10.png 顺序正确）
                def natural_sort_key(filename):
                    """自然排序键函数，处理数字部分"""
                    parts = re.split(r'(\d+)', filename)
                    return [int(p) if p.isdigit() else p.lower() for p in parts]
                
                image_files.sort(key=natural_sort_key)
                
                # 构建完整的图片路径列表
                cls._phone_photo_list = [
                    os.path.join(folder_path, img) for img in image_files
                ]
                print(f"📱 检测到新文件夹: {latest_folder} (共{len(cls._phone_photo_list)}张)，从第1张开始")
            else:
                # 同一文件夹，检查是否有新图片上传
                image_files = [f for f in os.listdir(folder_path) 
                              if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'))]
                
                if not image_files:
                    print(f"⚠️ 文件夹 {latest_folder} 中没有图片")
                    return None
                
                # 自然排序
                def natural_sort_key(filename):
                    parts = re.split(r'(\d+)', filename)
                    return [int(p) if p.isdigit() else p.lower() for p in parts]
                
                image_files.sort(key=natural_sort_key)
                new_photo_list = [
                    os.path.join(folder_path, img) for img in image_files
                ]
                
                # 如果图片数量变化，更新列表
                if len(new_photo_list) != len(cls._phone_photo_list):
                    old_len = len(cls._phone_photo_list)
                    new_len = len(new_photo_list)
                    
                    # 保持当前索引，但如果索引超出范围则调整
                    if cls._phone_photo_index >= new_len:
                        cls._phone_photo_index = max(0, new_len - 1)
                    
                    cls._phone_photo_list = new_photo_list
                    print(f"📱 文件夹 {latest_folder} 图片数量变化: {old_len} -> {new_len} 张")
            
            # 检查列表是否为空
            if not cls._phone_photo_list:
                print("⚠️ 没有可用的手机照片列表")
                return None
            
            # 切换到下一张（循环）
            cls._phone_photo_index = (cls._phone_photo_index + 1) % len(cls._phone_photo_list)
            current_index = cls._phone_photo_index
            
            image_path = cls._phone_photo_list[current_index]
            image_name = os.path.basename(image_path)
            folder_name = os.path.basename(cls._current_folder) if cls._current_folder else "未知"
            
            print(f"🔄 切换到第 {current_index + 1}/{len(cls._phone_photo_list)} 张: {image_name}")
            
            return image_path
            
        except Exception as e:
            import traceback
            print(f"❌ 切换手机照片失败: {e}")
            print(traceback.format_exc())
            return None
    
    @classmethod
    def get_current_photo_info(cls):
        """获取当前照片信息"""
        if not cls._phone_photo_list or cls._phone_photo_index >= len(cls._phone_photo_list):
            return None
        
        current_index = cls._phone_photo_index % len(cls._phone_photo_list)
        image_path = cls._phone_photo_list[current_index]
        total = len(cls._phone_photo_list)
        
        return {
            'path': image_path,
            'index': current_index + 1,
            'total': total,
            'filename': os.path.basename(image_path)
        }
    
    def _capture_pc_screenshot(self):
        """执行 PC 屏幕截图"""
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
            self.error_occurred.emit(f"PC 截图失败: {str(e)}")
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
    """OCR 工作线程 - 文字识别（DeepSeek-OCR 首选 + EasyOCR 备选）"""

    ocr_completed = Signal(str, float)  # OCR 完成信号，参数为识别文本和耗时（秒）
    error_occurred = Signal(str)  # 错误信号
    
    # SiliconFlow API 配置
    SILICONFLOW_API_KEY = "sk-lhxzzjsezqnknpsjjgiyuzlbkiesxzyosmrcwzdgmvdknvln"
    SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
    
    # 类级别的单例 Reader（避免重复加载模型导致内存泄漏）
    _reader_instance = None
    _reader_lock = threading.Lock()
    
    # 类级别计数器：记录主模型连续失败次数（跨线程实例共享）
    _primary_model_fail_count = 0
    _primary_model_fail_threshold = 2  # 连续失败阈值
    _switched_to_backup = False  # 是否已切换到备选模型
    _backup_success_count = 0  # 备选模型连续成功次数
    _backup_success_threshold = 10  # 备选模型连续成功阈值（用于尝试恢复主模型）
    _auto_recovery_enabled = True  # 启用自动恢复机制

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self._interrupted = False
    
    @classmethod
    def get_reader(cls):
        """获取或创建 EasyOCR Reader 单例（仅备选方案使用）"""
        if cls._reader_instance is None:
            with cls._reader_lock:
                # 双重检查锁定
                if cls._reader_instance is None:
                    print("🔍 正在初始化 EasyOCR 引擎（首次加载，可能需要几秒）...")
                    try:
                        # 禁用 verbose 输出，减少日志干扰
                        cls._reader_instance = easyocr.Reader(
                            ['ch_sim', 'en'], 
                            gpu=False,  # 强制使用 CPU
                            verbose=False,
                            download_enabled=True
                        )
                        print("✅ EasyOCR 引擎初始化完成")
                    except Exception as e:
                        print(f"❌ EasyOCR 引擎初始化失败: {e}")
                        raise
        return cls._reader_instance
    
    @classmethod
    def cleanup_reader(cls):
        """清理 EasyOCR Reader（程序退出时调用）"""
        if cls._reader_instance is not None:
            with cls._reader_lock:
                if cls._reader_instance is not None:
                    try:
                        del cls._reader_instance
                        cls._reader_instance = None
                        print("🗑️ EasyOCR 引擎已清理")
                    except:
                        pass

    def run(self):
        """运行 OCR 识别（智能降级策略）"""
        import base64
        from openai import OpenAI
        
        reader = None
        client = None
        image_url = None
        
        try:
            # 检查文件是否存在
            if not os.path.exists(self.image_path):
                self.error_occurred.emit(f"图片文件不存在: {self.image_path}")
                return

            start_time = time.time()
            
            # 智能模型选择策略
            use_primary_model = False

            # 情况1：未切换状态，尝试主模型
            if not self._switched_to_backup:
                use_primary_model = True

            # 情况2：已切换状态，但备选模型连续成功达到阈值，尝试恢复主模型
            elif (self._switched_to_backup and
                  self._backup_success_count >= self._backup_success_threshold and
                  self._auto_recovery_enabled):
                print(f"🔍 EasyOCR 已连续成功 {self._backup_success_count} 次，尝试恢复 DeepSeek-OCR...")
                self.__class__._switched_to_backup = False
                self.__class__._primary_model_fail_count = 0  # 重置失败计数
                self.__class__._backup_success_count = 0  # 重置成功计数
                use_primary_model = True

            # 执行调用逻辑
            if use_primary_model:
                # 尝试主模型：DeepSeek-OCR
                try:
                    print(f"🤖 DeepSeek-OCR 请求中...")
                    
                    # 读取并编码图片
                    with open(self.image_path, "rb") as f:
                        image_data = f.read()
                    
                    # 获取图片扩展名
                    ext = os.path.splitext(self.image_path)[1].lstrip('.')
                    image_url = f"data:image/{ext};base64,{base64.b64encode(image_data).decode('utf-8')}"
                    
                    # 【关键】立即释放 image_data，减少内存占用
                    del image_data
                    
                    # 创建客户端
                    client = OpenAI(
                        api_key=self.SILICONFLOW_API_KEY,
                        base_url=self.SILICONFLOW_BASE_URL,
                        timeout=60
                    )
                    
                    # 检查是否已被中断
                    if self._interrupted:
                        return
                    
                    response = client.chat.completions.create(
                        model="deepseek-ai/DeepSeek-OCR",
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
                                        "text": "Convert the document to markdown"
                                    }
                                ]
                            }
                        ]
                    )
                    
                    full_text = response.choices[0].message.content

                    # 检查是否被中断
                    if self._interrupted:
                        return

                    elapsed_time = time.time() - start_time
                    print(f"✅ DeepSeek-OCR 完成 ({elapsed_time:.2f}s)")

                    # 主模型成功，重置失败计数
                    self.__class__._primary_model_fail_count = 0
                    self.__class__._backup_success_count = 0  # 重置备选成功计数
                    self.ocr_completed.emit(full_text, elapsed_time)
                    return

                except Exception as e:
                    if self._interrupted:
                        return
                    print(f"❌ DeepSeek-OCR 失败: {str(e)[:50]}")
                    # 增加失败计数
                    self.__class__._primary_model_fail_count += 1

                    # 检查是否达到阈值
                    if self.__class__._primary_model_fail_count >= self.__class__._primary_model_fail_threshold:
                        print(f"🚨 切换至 EasyOCR")
                        self.__class__._switched_to_backup = True
                        self.__class__._backup_success_count = 0  # 重置备选成功计数

            # 使用备选模型（已切换或主模型失败）
            if not use_primary_model or (use_primary_model and self._primary_model_fail_count > 0):
                try:
                    print(f"🤖 EasyOCR 识别中...")
                    
                    # 获取单例 Reader
                    reader = self.get_reader()
                    
                    # 检查是否已被中断
                    if self._interrupted:
                        return
                    
                    # 执行识别
                    result = reader.readtext(
                        self.image_path,
                        paragraph=False,  # 不合并段落，提高速度
                        detail=0,  # 只返回文本，不返回坐标和置信度
                        batch_size=1  # 单张图片处理
                    )
                    
                    # 提取文本
                    if isinstance(result, list) and len(result) > 0:
                        full_text = '\n'.join(result)
                    else:
                        full_text = ""

                    # 检查是否被中断
                    if self._interrupted:
                        return

                    total_elapsed = time.time() - start_time
                    print(f"✅ EasyOCR 完成 ({total_elapsed:.2f}s)")

                    # 备选模型成功，更新状态
                    self.__class__._backup_success_count += 1

                    # 在结果前添加使用的模型信息
                    result_with_model = f"[使用模型: EasyOCR]\n\n{full_text}"
                    self.ocr_completed.emit(result_with_model, total_elapsed)
                    return

                except Exception as e:
                    if self._interrupted:
                        return
                    print(f"❌ EasyOCR 失败: {str(e)[:50]}")
                    # 备选模型也失败，重置成功计数
                    self.__class__._backup_success_count = 0

            # 所有尝试都失败
            if not self._interrupted:
                self.error_occurred.emit(f"所有模型均调用失败（DeepSeek-OCR + EasyOCR）")
            else:
                print("✅ OCR 任务已安全中断")

        except SystemExit:
            # 【关键】捕获系统退出信号，静默处理
            print("✅ OCR 任务已被系统终止")
            return
        except KeyboardInterrupt:
            # 【关键】捕获键盘中断
            print("✅ OCR 任务被用户中断")
            return
        except Exception as e:
            if self._interrupted:
                print("✅ OCR 任务已安全中断")
                return
            import traceback
            error_detail = traceback.format_exc()
            print(f"OCR 工作线程错误详情:\n{error_detail}")
            self.error_occurred.emit(f"OCR 识别失败: {str(e)}")
        finally:
            # 【关键】确保资源被正确清理
            try:
                if client is not None:
                    # 关闭客户端连接
                    if hasattr(client, 'close'):
                        client.close()
                    client = None
            except:
                pass
            # 【关键】释放大对象
            try:
                if image_url is not None:
                    del image_url
            except:
                pass
            # 注意：不要在这里删除 reader，它是单例

    def interrupt(self):
        """中断当前任务"""
        self._interrupted = True
        print("🛑 OCR 任务收到中断信号")
        # 注意：由于 easyocr 和 API 调用都不支持原生中断，我们依赖线程终止
        # 这里只是设置标志位，实际中断由线程终止完成
    
    @classmethod
    def reset_model_state(cls):
        """重置所有模型状态（可用于手动恢复主模型）"""
        cls._primary_model_fail_count = 0
        cls._switched_to_backup = False
        cls._backup_success_count = 0
        print("🔄 OCRWorker 模型状态已重置，将重新尝试 DeepSeek-OCR")
    
    @classmethod
    def force_use_primary(cls):
        """强制使用主模型（忽略失败计数）"""
        cls._primary_model_fail_count = 0
        cls._switched_to_backup = False
        cls._backup_success_count = 0
        print("⚡ 已强制切换至 DeepSeek-OCR 主模型")
    
    @classmethod
    def toggle_model(cls):
        """切换 OCR 模型（DeepSeek-OCR ↔ EasyOCR）"""
        if cls._switched_to_backup:
            # 当前是 EasyOCR，切换到 DeepSeek-OCR
            cls._switched_to_backup = False
            cls._primary_model_fail_count = 0
            cls._backup_success_count = 0
            print("🔄 OCR 模型已切换: EasyOCR → DeepSeek-OCR")
            return "DeepSeek-OCR"
        else:
            # 当前是 DeepSeek-OCR，切换到 EasyOCR
            cls._switched_to_backup = True
            cls._backup_success_count = 0
            print("🔄 OCR 模型已切换: DeepSeek-OCR → EasyOCR")
            return "EasyOCR"


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
                "max_tokens": 8192,
                "temperature": 0.7
            }

            # 检查是否已被中断
            if self._interrupted:
                return

            print(f"🤖 LLM 请求中...")
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
                return

            result = response.json()

            elapsed_time = time.time() - start_time

            # 提取回复内容
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']

                # 最后检查是否被中断
                if self._interrupted:
                    return

                print(f"✅ LLM 完成 ({elapsed_time:.2f}s)")
                self.llm_completed.emit(content, elapsed_time)
            else:
                if not self._interrupted:
                    self.error_occurred.emit("LLM API 返回格式异常")

        except requests.exceptions.Timeout:
            if not self._interrupted:
                print(f"❌ LLM 超时")
                self.error_occurred.emit("LLM API 请求超时，请重试")
        except requests.exceptions.ConnectionError:
            if not self._interrupted:
                print(f"❌ LLM 连接失败")
                self.error_occurred.emit("LLM API 连接失败，请检查网络")
        except requests.exceptions.RequestException as e:
            if not self._interrupted:
                # 忽略因中断导致的异常
                if "Interrupted function call" not in str(e):
                    print(f"❌ LLM 请求失败: {str(e)[:50]}")
                    self.error_occurred.emit(f"LLM API 请求失败: {str(e)}")
        except Exception as e:
            if not self._interrupted:
                print(f"❌ LLM 错误: {str(e)[:50]}")
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
        'Qwen/Qwen3-VL-32B-Instruct',
        'Qwen/Qwen3-VL-235B-A22B-Instruct',
        'zai-org/GLM-4.5V',
        'Pro/moonshotai/Kimi-K2.6'
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
            
            # 【关键】立即释放 image_data，减少内存占用
            del image_data

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
                    # 获取当前主模型名称
                    primary_model_name = getattr(KimiWorker, '_custom_primary_model', 'kimi-k2.5')
                    model_display = primary_model_name.split('/')[-1] if '/' in primary_model_name else primary_model_name
                    
                    # 根据模型选择 API 端点
                    if primary_model_name == 'kimi-k2.5':
                        api_key = self.api_key
                        base_url = "https://api.moonshot.cn/v1"
                    else:
                        # Qwen 等非 Kimi 模型使用 SiliconFlow
                        api_key = self.SILICONFLOW_API_KEY
                        base_url = self.SILICONFLOW_BASE_URL
                    
                    print(f"🤖 {model_display} 请求中...")
                    client = OpenAI(
                        api_key=api_key,
                        base_url=base_url,
                        timeout=240  # 设置超时
                    )
                    
                    # 检查是否已被中断
                    if self._interrupted:
                        return
                    
                    completion = client.chat.completions.create(
                        model=primary_model_name,
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
                        return

                    elapsed_time = time.time() - start_time
                    print(f"✅ {model_display} 完成 ({elapsed_time:.2f}s)")

                    # 主模型成功，重置失败计数
                    self.__class__._primary_model_fail_count = 0
                    self.__class__._backup_success_count = 0  # 重置备选成功计数
                    self.kimi_completed.emit(content, elapsed_time)
                    return

                except Exception as e:
                    if self._interrupted:
                        return
                    print(f"❌ {model_display} 失败: {str(e)[:50]}")
                    # 增加失败计数
                    self.__class__._primary_model_fail_count += 1

                    # 检查是否达到阈值
                    if self.__class__._primary_model_fail_count >= self.__class__._primary_model_fail_threshold:
                        print(f"🚨 切换至备选模型")
                        self.__class__._switched_to_backup = True
                        self.__class__._backup_success_count = 0  # 重置备选成功计数

                    # 切换至备选模型重试（效率优先：不重试主模型）
                    backup_index = self.__class__._current_backup_index
                    model = self.BACKUP_MODELS[backup_index]

            # 使用备选模型（已切换或主模型失败）
            if not use_primary_model or (use_primary_model and self._primary_model_fail_count > 0):
                # 选择备选模型
                backup_index = self.__class__._current_backup_index
                model = self.BACKUP_MODELS[backup_index]

                try:
                    print(f"🤖 备选模型 {model.split('/')[-1]} 请求中...")
                    
                    # 创建客户端
                    client = OpenAI(
                        api_key=self.SILICONFLOW_API_KEY,
                        base_url=self.SILICONFLOW_BASE_URL,
                        timeout=240
                    )
                    
                    # 检查是否已被中断
                    if self._interrupted:
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
                        return

                    total_elapsed = time.time() - start_time
                    print(f"✅ {model.split('/')[-1]} 完成 ({total_elapsed:.2f}s)")

                    # 备选模型成功，更新状态
                    self.__class__._backup_success_count += 1
                    self.__class__._current_backup_index = (backup_index + 1) % len(self.BACKUP_MODELS)

                    # 在结果前添加使用的模型信息
                    result_with_model = f"[使用模型: {model}]\n\n{content}"
                    self.kimi_completed.emit(result_with_model, total_elapsed)
                    return

                except Exception as e:
                    if self._interrupted:
                        return
                    print(f"❌ {model.split('/')[-1]} 失败: {str(e)[:50]}")
                    # 备选模型也失败，重置成功计数，尝试下一个
                    self.__class__._backup_success_count = 0
                    self.__class__._current_backup_index = (backup_index + 1) % len(self.BACKUP_MODELS)

            # 所有尝试都失败
            if not self._interrupted:
                self.error_occurred.emit(f"所有模型均调用失败（主模型 + 备选模型）")
            else:
                print("✅ Kimi 任务已安全中断")

        except SystemExit:
            # 【关键】捕获系统退出信号，静默处理
            print("✅ Kimi 任务已被系统终止")
            return
        except KeyboardInterrupt:
            # 【关键】捕获键盘中断
            print("✅ Kimi 任务被用户中断")
            return
        except Exception as e:
            if self._interrupted:
                print("✅ Kimi 任务已安全中断")
                return
            import traceback
            error_detail = traceback.format_exc()
            print(f"Kimi 工作线程错误详情:\n{error_detail}")
            self.error_occurred.emit(f"图片分析失败: {str(e)}")
        finally:
            # 【关键】确保 client 被正确清理
            try:
                if client is not None:
                    # 关闭客户端连接
                    if hasattr(client, 'close'):
                        client.close()
                    client = None
            except:
                pass
            # 【关键】释放大对象
            try:
                del image_url
            except:
                pass

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
    
    @classmethod
    def toggle_kimi_model(cls):
        """切换 Kimi 主模型（Kimi-K2.5 ↔ QwenA3B）"""
        # 检查当前主模型是什么
        current_primary = getattr(cls, '_custom_primary_model', 'kimi-k2.5')
        
        if current_primary == 'kimi-k2.5':
            # 切换到 QwenA3B
            cls._custom_primary_model = 'Qwen/Qwen3-Omni-30B-A3B-Instruct'
            cls._primary_model_fail_count = 0
            cls._switched_to_backup = False
            cls._backup_success_count = 0
            print("🔄 Kimi 主模型已切换: Kimi-K2.5 → QwenA3B")
            return "QwenA3B"
        else:
            # 切换回 Kimi-K2.5
            cls._custom_primary_model = 'kimi-k2.5'
            cls._primary_model_fail_count = 0
            cls._switched_to_backup = False
            cls._backup_success_count = 0
            print("🔄 Kimi 主模型已切换: QwenA3B → Kimi-K2.5")
            return "Kimi-K2.5"
    
    @classmethod
    def set_primary_model(cls, model_name):
        """设置指定的模型为主模型"""
        cls._custom_primary_model = model_name
        cls._primary_model_fail_count = 0
        cls._switched_to_backup = False
        cls._backup_success_count = 0
        model_short = model_name.split('/')[-1]
        print(f"🔄 Kimi 主模型已设置为: {model_short}")
        return model_short


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
                # 检查是否为JSON格式（图片上传）
                try:
                    import json
                    data = json.loads(message)
                    if isinstance(data, dict) and data.get('type') == 'image_upload':
                        # 处理图片上传
                        await self.handle_image_upload(data, client_ip)
                        continue
                except (json.JSONDecodeError, AttributeError):
                    pass
                
                # 普通文本消息
                print(f"[←] 收到手机消息: {message}")
                await websocket.send("已收到!")
                
        except websockets.exceptions.ConnectionClosed:
            print(f"[-] 手机断开: {client_ip}")
        finally:
            self.clients.discard(websocket)
    
    async def handle_image_upload(self, data, client_ip):
        """处理图片上传
        
        Args:
            data: 包含图片信息的字典
            client_ip: 客户端IP
        """
        try:
            from datetime import datetime
            import threading
            
            # 提取数据并验证必填字段
            filename = data.get('filename', 'unknown.png')
            index = data.get('index', 1)
            total = data.get('total', 1)
            counter = data.get('counter', 1)
            base64_data = data.get('data', '')
            batch_id = data.get('batch_id', None)  # 批次ID，用于关联同一批图片
            
            if not base64_data:
                print(f"[!] 收到空图片数据")
                await self._send_upload_response(client_ip, False, "图片数据为空")
                return
            
            # 验证base64数据格式
            if len(base64_data) > 10 * 1024 * 1024:  # 限制10MB
                print(f"[!] 图片数据过大: {len(base64_data)} bytes")
                await self._send_upload_response(client_ip, False, "图片大小超过限制(10MB)")
                return
            
            # 解析base64数据（移除data:image/xxx;base64,前缀）
            if ',' in base64_data:
                prefix = base64_data.split(',', 1)[0]
                base64_data = base64_data.split(',', 1)[1]
                # 验证前缀格式
                if not prefix.startswith('data:image/'):
                    print(f"[!] 无效的base64前缀: {prefix}")
            
            # 解码图片并验证
            try:
                image_bytes = base64.b64decode(base64_data, validate=True)
            except Exception as decode_error:
                print(f"[!] Base64解码失败: {decode_error}")
                await self._send_upload_response(client_ip, False, f"图片数据格式错误: {str(decode_error)}")
                return
            
            if len(image_bytes) == 0:
                print(f"[!] 解码后图片数据为空")
                await self._send_upload_response(client_ip, False, "图片数据无效")
                return
            
            # 使用线程锁确保文件夹创建的原子性
            if not hasattr(self, '_folder_lock'):
                self._folder_lock = threading.Lock()

            # 创建保存目录 phone_photo
            if getattr(sys, 'frozen', False):
                # 打包后：使用 exe 所在目录
                base_dir = os.path.dirname(sys.executable)
            else:
                # 开发环境：使用当前工作目录
                base_dir = os.getcwd()

            phone_photo_dir = os.path.join(base_dir, 'phone_photo')

            with self._folder_lock:
                if not os.path.exists(phone_photo_dir):
                    os.makedirs(phone_photo_dir, exist_ok=True)
                    print(f"📁 创建图片保存目录: {phone_photo_dir}")
                
                # 使用批次ID或时间戳创建文件夹名
                if batch_id:
                    # 如果有批次ID，使用它来确保同一批图片在同一文件夹
                    folder_name = f"{batch_id}_{total}张"
                else:
                    # 否则使用时间戳（注意：这会导致同一秒内的图片在同一文件夹）
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    folder_name = f"{timestamp}_{total}张"
                
                folder_path = os.path.join(phone_photo_dir, folder_name)
                
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path, exist_ok=True)
                    print(f"📁 创建批次文件夹: {folder_name}")
            
            # 验证文件扩展名安全性（防止路径遍历攻击）
            ext = os.path.splitext(filename)[1].lower() or '.png'
            # 只允许常见的图片格式
            allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
            if ext not in allowed_extensions:
                print(f"[!] 不支持的文件格式: {ext}，使用.png代替")
                ext = '.png'
            
            # 【关键修复】直接使用前端传来的 index 作为文件名，确保顺序一致
            # 不再扫描文件夹动态分配编号，避免异步到达导致的顺序混乱
            with self._folder_lock:
                save_filename = f"{index}{ext}"
                save_path = os.path.join(folder_path, save_filename)
                
                # 检查文件是否已存在（理论上不应该发生，但作为保险）
                if os.path.exists(save_path):
                    print(f"⚠️ 文件已存在，将被覆盖: {save_filename}")
            
            # 保存图片
            with open(save_path, 'wb') as f:
                f.write(image_bytes)
            
            print(f"✅ 保存图片 [{index}/{total}]: {filename} -> {save_filename} (文件夹: {folder_name}, 大小: {len(image_bytes)} bytes)")
            
            # 发送成功响应给客户端
            await self._send_upload_response(client_ip, True, "上传成功", {
                'filename': save_filename,  # 返回实际保存的文件名
                'original_filename': filename,  # 返回原始文件名
                'folder': folder_name,
                'size': len(image_bytes),
                'index': index,
                'total': total,
                'counter': index  # 返回使用的索引号
            })
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"❌ 保存图片失败: {e}")
            print(f"错误详情:\n{error_detail}")
            await self._send_upload_response(client_ip, False, f"服务器错误: {str(e)}")
    
    async def _send_upload_response(self, client_ip, success, message, extra_data=None):
        """发送上传响应给客户端
        
        Args:
            client_ip: 客户端IP
            success: 是否成功
            message: 响应消息
            extra_data: 额外数据
        """
        try:
            response = {
                'type': 'upload_response',
                'success': success,
                'message': message
            }
            if extra_data:
                response.update(extra_data)
            
            # 查找对应的客户端连接并发送响应
            for client in self.clients:
                try:
                    # 这里假设可以通过某种方式识别客户端，实际可能需要维护client_ip到websocket的映射
                    await client.send(json.dumps(response))
                    break  # 发送给第一个可用的客户端
                except:
                    continue
        except Exception as e:
            print(f"[!] 发送上传响应失败: {e}")
    
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


class AutoStartManager:
    """Windows开机自启管理器"""
    
    def __init__(self, app_name="windows_ace_process", app_path=None):
        """
        初始化自启管理器
        
        Args:
            app_name: 应用程序名称（注册表中的显示名称）
            app_path: 应用程序路径（默认为当前可执行文件路径）
        """
        self.app_name = app_name
        self.app_path = app_path or self._get_executable_path()
        
        # Windows注册表启动项路径
        self.reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    def _get_executable_path(self):
        """获取可执行文件路径"""
        if getattr(sys, 'frozen', False):
            # 打包后的exe路径
            return sys.executable
        else:
            # 开发环境：Python脚本路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            main_app = os.path.join(parent_dir, "main_app.py")
            return f'"{sys.executable}" "{main_app}"'
    
    def add_to_startup(self):
        """
        添加到开机自启
        
        Returns:
            bool: 是否成功添加
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.reg_path,
                0,
                winreg.KEY_SET_VALUE
            )
            
            # 确保路径用引号包裹（处理空格）
            app_path = self.app_path
            if not app_path.startswith('"'):
                app_path = f'"{app_path}"'
            
            winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, app_path)
            winreg.CloseKey(key)
            
            print(f"✅ 已添加到开机自启: {self.app_name}")
            return True
            
        except Exception as e:
            print(f"❌ 添加到开机自启失败: {e}")
            return False
    
    def remove_from_startup(self):
        """
        从开机自启中移除
        
        Returns:
            bool: 是否成功移除
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.reg_path,
                0,
                winreg.KEY_SET_VALUE
            )
            
            winreg.DeleteValue(key, self.app_name)
            winreg.CloseKey(key)
            
            print(f"✅ 已从开机自启中移除: {self.app_name}")
            return True
            
        except FileNotFoundError:
            print(f"⚠️ 未在开机自启中找到: {self.app_name}")
            return True
        except Exception as e:
            print(f"❌ 从开机自启移除失败: {e}")
            return False
    
    def is_enabled(self):
        """
        检查是否已启用开机自启
        
        Returns:
            bool: 是否已启用
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.reg_path,
                0,
                winreg.KEY_READ
            )
            
            value, _ = winreg.QueryValueEx(key, self.app_name)
            winreg.CloseKey(key)
            
            return True
            
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"❌ 检查开机自启状态失败: {e}")
            return False
    
    def toggle_startup(self):
        """
        切换开机自启状态
        
        Returns:
            tuple: (bool success, str message)
        """
        if self.is_enabled():
            if self.remove_from_startup():
                return True, "已禁用开机自启"
            else:
                return False, "禁用开机自启失败"
        else:
            if self.add_to_startup():
                return True, "已启用开机自启"
            else:
                return False, "启用开机自启失败"


class WindowsServiceManager:
    """Windows服务管理器 - 使用schtasks创建计划任务实现自启和守护"""
    
    def __init__(self, task_name="windows_ace_process", app_path=None):
        """
        初始化服务管理器
        
        Args:
            task_name: 计划任务名称
            app_path: 应用程序路径
        """
        self.task_name = task_name
        self.app_path = app_path or self._get_executable_path()
    
    def _get_executable_path(self):
        """获取可执行文件路径"""
        if getattr(sys, 'frozen', False):
            # 打包后的exe路径
            return sys.executable
        else:
            # 开发环境
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            main_app = os.path.join(parent_dir, "main_app.py")
            return f'"{sys.executable}" "{main_app}"'
    
    def _get_main_app_path(self):
        """获取主程序路径"""
        if getattr(sys, 'frozen', False):
            # 打包后，直接运行exe
            return sys.executable
        else:
            # 开发环境，返回main_app.py的路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            main_app_path = os.path.join(parent_dir, "main_app.py")
            return main_app_path
    
    def install_as_service(self, max_restarts=10, restart_delay=3):
        """
        安装为系统服务（使用计划任务）
        
        注意: 此操作需要管理员权限
        
        Args:
            max_restarts: 最大重启次数
            restart_delay: 重启延迟
            
        Returns:
            tuple: (bool success, str message)
        """
        try:
            main_app_path = self._get_main_app_path()
            
            if not os.path.exists(main_app_path):
                return False, f"找不到主程序: {main_app_path}"
            
            # 构建命令 - 直接运行主程序，不再需要守护脚本
            if getattr(sys, 'frozen', False):
                # 打包环境：直接运行exe
                cmd = sys.executable
            else:
                # 开发环境：运行Python脚本
                python_exe = sys.executable
                cmd = f'{python_exe} "{main_app_path}"'
            
            # 删除旧任务（如果存在）
            self.uninstall_service()
            
            # 使用 schtasks 创建计划任务（登录时启动 + 崩溃后重启）
            # 注意: 这需要管理员权限
            create_task_cmd = [
                'schtasks', '/Create',
                '/TN', self.task_name,
                '/TR', cmd,
                '/SC', 'ONLOGON',  # 登录时启动
                '/RL', 'HIGHEST',   # 最高权限（需要管理员）
                '/F'                # 强制覆盖
            ]
            
            result = subprocess.run(
                create_task_cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                return True, "✅ 已成功安装为系统服务（计划任务）"
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                
                # 检查是否是权限问题
                if "access is denied" in error_msg.lower() or "拒绝访问" in error_msg or "unauthorized" in error_msg.lower():
                    return False, (
                        "❌ 权限不足，无法创建计划任务。\n\n"
                        "⚠️ 重要提示：计划任务功能必须以管理员身份运行！\n\n"
                        "请按照以下步骤操作：\n"
                        "1. 关闭当前程序\n"
                        "2. 右键点击程序图标\n"
                        "3. 选择「以管理员身份运行」\n"
                        "4. 再次尝试安装服务\n\n"
                        "💡 替代方案：\n"
                        "如果不方便使用管理员权限，可以使用「开机自启」功能\n"
                        "（设置标签页 → 开机自启设置），无需管理员权限。\n\n"
                        f"详细错误：{error_msg[:200]}"
                    )
                
                return False, f"❌ 安装失败: {error_msg[:300]}"
                
        except Exception as e:
            return False, f"❌ 安装异常: {str(e)}"
    
    def uninstall_service(self):
        """
        卸载系统服务
        
        Returns:
            tuple: (bool success, str message)
        """
        try:
            delete_task_cmd = [
                'schtasks', '/Delete',
                '/TN', self.task_name,
                '/F'  # 强制删除，不提示
            ]
            
            result = subprocess.run(
                delete_task_cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                return True, "✅ 已成功卸载系统服务"
            else:
                # 任务不存在也算成功
                if "cannot find the file" in result.stderr.lower():
                    return True, "ℹ️ 服务未安装"
                return False, f"❌ 卸载失败: {result.stderr}"
                
        except Exception as e:
            return False, f"❌ 卸载异常: {str(e)}"
    
    def is_installed(self):
        """
        检查服务是否已安装
        
        Returns:
            bool: 是否已安装
        """
        try:
            query_task_cmd = [
                'schtasks', '/Query',
                '/TN', self.task_name,
                '/FO', 'LIST'
            ]
            
            result = subprocess.run(
                query_task_cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            return result.returncode == 0
            
        except:
            return False
    
    def start_service(self):
        """
        立即启动服务
        
        Returns:
            tuple: (bool success, str message)
        """
        try:
            run_task_cmd = [
                'schtasks', '/Run',
                '/TN', self.task_name
            ]
            
            result = subprocess.run(
                run_task_cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                return True, "✅ 服务已启动"
            else:
                return False, f"❌ 启动失败: {result.stderr}"
                
        except Exception as e:
            return False, f"❌ 启动异常: {str(e)}"
    
    def stop_service(self):
        """
        停止服务
        
        Returns:
            tuple: (bool success, str message)
        """
        try:
            end_task_cmd = [
                'schtasks', '/End',
                '/TN', self.task_name
            ]
            
            result = subprocess.run(
                end_task_cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                return True, "✅ 服务已停止"
            else:
                return False, f"❌ 停止失败: {result.stderr}"
                
        except Exception as e:
            return False, f"❌ 停止异常: {str(e)}"
    
    def get_service_status(self):
        """
        获取服务状态
        
        Returns:
            dict: 服务状态信息
        """
        status = {
            'installed': False,
            'running': False,
            'last_run': None,
            'next_run': None
        }
        
        try:
            if not self.is_installed():
                return status
            
            status['installed'] = True
            
            # 查询详细信息
            query_cmd = [
                'schtasks', '/Query',
                '/TN', self.task_name,
                '/FO', 'LIST',
                '/V'
            ]
            
            result = subprocess.run(
                query_cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # 解析状态
                for line in output.split('\n'):
                    if 'Status:' in line:
                        if 'Running' in line:
                            status['running'] = True
                    elif 'Last Run Time:' in line:
                        status['last_run'] = line.split(':', 1)[1].strip()
                    elif 'Next Run Time:' in line:
                        status['next_run'] = line.split(':', 1)[1].strip()
            
        except Exception as e:
            print(f"获取服务状态失败: {e}")
        
        return status


class CodeOrganizeWorker(QThread):
    """代码整理工作线程 - 将API结果整理为面试代码并自动写入"""
    
    organize_completed = Signal(str, float)  # 整理完成信号，参数为整理后的代码和耗时(秒)
    error_occurred = Signal(str)  # 错误信号
    status_update = Signal(str)  # 状态更新信号（用于UI显示）
    file_saved = Signal(str)  # 文件保存信号，参数为文件路径
    code_to_clipboard = Signal(str)  # 复制到剪切板信号，参数为过滤后的代码
    
    # LongCat API 配置
    LONGCAT_API_KEY = "ak_2Fw1hL0xA8H33yj1wn4pW8ag0w84y"
    LONGCAT_BASE_URL = "https://api.longcat.chat/openai/v1/chat/completions"
    LONGCAT_MODEL = "LongCat-Flash-Chat"
    
    def __init__(self, kimi_result=None, llm_result=None, save_dir="./code_output", custom_prompt=None):
        super().__init__()
        self.kimi_result = kimi_result  # KimiWorker的结果（优先使用）
        self.llm_result = llm_result    # LLMWorker的结果（备选）
        self.save_dir = save_dir
        self.custom_prompt = custom_prompt  # 自定义提示词
        self._interrupted = False
        self._session = None
        os.makedirs(save_dir, exist_ok=True)
    
    def run(self):
        """执行代码整理流程"""
        self._session = None
        try:
            start_time = time.time()
            
            # 步骤1: 确定输入源
            if self.kimi_result:
                input_text = self.kimi_result
                source = "Kimi"
            elif self.llm_result:
                input_text = self.llm_result
                source = "LLM"
            else:
                self.error_occurred.emit("没有可用的API结果进行整理")
                return
            
            print(f"📝 开始整理 {source} 的代码结果...")
            self.status_update.emit("正在整理代码...")
            
            # 步骤2: 调用LLM API进行代码整理
            organized_code = self._organize_code(input_text)
            
            # 检查是否被中断
            if self._interrupted:
                return
            
            # 步骤2.5: 过滤Markdown代码块标记并复制到剪切板
            filtered_code_lines = []
            for line in organized_code.split('\n'):
                stripped = line.strip()
                # 跳过代码块标记（如 ```python, ```, ```java 等）
                if stripped.startswith('```'):
                    print(f"⏭️ 过滤代码块标记: {stripped}")
                    continue
                filtered_code_lines.append(line)
            
            filtered_code = '\n'.join(filtered_code_lines)
            
            # 保存过滤后的代码，等待自动输入完成后再复制到剪切板
            self.filtered_code = filtered_code
            print("💾 过滤后的代码已保存，等待自动输入完成后复制到剪切板")
            
            elapsed_time = time.time() - start_time
            print(f"✅ 代码整理完成 ({elapsed_time:.2f}s)")
            self.status_update.emit("代码整理完成")
            
            # 步骤3: 保存为txt文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interview_code_{timestamp}.txt"
            filepath = os.path.join(self.save_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(organized_code)
            
            print(f"💾 代码已保存: {filepath}")
            self.file_saved.emit(filepath)
            self.status_update.emit("文件已保存")
            
            # 步骤4: 发送完成信号
            self.organize_completed.emit(organized_code, elapsed_time)
            
        except Exception as e:
            if not self._interrupted:
                import traceback
                error_detail = traceback.format_exc()
                print(f"❌ 代码整理失败: {str(e)}\n{error_detail}")
                self.error_occurred.emit(f"代码整理失败: {str(e)}")
        finally:
            if self._session:
                try:
                    self._session.close()
                except:
                    pass
                self._session = None
    
    def _organize_code(self, raw_text):
        """调用LLM API整理代码"""
        try:
            self._session = requests.Session()
            
            headers = {
                "Authorization": f"Bearer {self.LONGCAT_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # 使用自定义提示词或默认提示词
            if self.custom_prompt:
                system_prompt = self.custom_prompt
            else:
                system_prompt = """角色设定：你是一名正在参加技术面试的候选人，需要在白板上写出最优解。

任务指令：请根据以下要求，对提供的代码进行重构和整理：

解法选择：
- 仅保留最经典/最优的解法，舍弃其他非主流解法及所有文字分析
- 如果有多种解法，只保留时间复杂度最优的那个

代码规范（面试级）：
- 去噪：删除代码中所有的注释和多余的空行，仅保留核心逻辑
- 命名：使用最符合 Python 语法的极简变量名（如 x, y, k, v, i, j, t, l, r 等）
- 避免大众化命名（不要用 result, temp, data, output 等常见变量名）
- 风格：模拟人在面试高压环境下书写的极简风格

输出约束：
- 直接输出 Markdown 代码块，不要包含任何前置的解释、标题或后置的说明
- 只输出一个代码块，格式为：```python\n...代码...\n```
- 如果原内容包含多个题目，用 --- 分隔每个题目的代码块"""
            
            data = {
                "model": self.LONGCAT_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请整理以下代码：\n\n{raw_text}"}
                ],
                "max_tokens": 2000,
                "temperature": 0.3  # 降低温度以获得更确定的输出
            }
            
            # 检查是否已被中断
            if self._interrupted:
                return ""
            
            response = self._session.post(
                self.LONGCAT_BASE_URL,
                headers=headers,
                json=data,
                timeout=(10, 60)
            )
            response.raise_for_status()
            
            # 检查是否被中断
            if self._interrupted:
                return ""
            
            result = response.json()
            
            # 提取回复内容
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                
                # 最后检查是否被中断
                if self._interrupted:
                    return ""
                
                return content
            else:
                raise Exception("LLM API 返回格式异常")
                
        except requests.exceptions.Timeout:
            raise Exception("LLM API 请求超时")
        except requests.exceptions.ConnectionError:
            raise Exception("LLM API 连接失败")
        except requests.exceptions.RequestException as e:
            raise Exception(f"LLM API 请求失败: {str(e)}")
        except Exception as e:
            raise e
    
    def interrupt(self):
        """中断当前任务"""
        self._interrupted = True
        print("🛑 代码整理任务收到中断信号")
        if self._session:
            try:
                self._session.close()
            except:
                pass

class AutoTypeWorker(QThread):
    """自动写入工作线程 - 将整理好的代码自动输入到目标窗口"""

    typing_started = Signal()  # 开始输入信号
    typing_paused = Signal()  # 暂停输入信号
    typing_resumed = Signal()  # 恢复输入信号
    typing_completed = Signal(float)  # 完成输入信号，参数为总耗时(秒)
    clipboard_ready = Signal(str)  # 剪切板就绪信号，参数为过滤后的代码
    error_occurred = Signal(str)  # 错误信号
    status_update = Signal(str)  # 状态更新信号
    progress_update = Signal(int, int)  # 进度更新信号，参数为(当前行, 总行数)

    def __init__(self, code_file_path, delay=0.05, think_time_min=1.0, think_time_max=2.0, error_rate=0.08, line_break_rate=0.7):
        super().__init__()
        self.code_file_path = code_file_path
        self.delay = delay
        self.think_time_min = think_time_min  # 思考时间最小值
        self.think_time_max = think_time_max  # 思考时间最大值
        self.error_rate = error_rate  # 错误率（默认8%）
        self.line_break_rate = line_break_rate  # 长行随机换行率（默认70%概率触发）
        self._stop_flag = False
        self._paused = False
        self.filtered_code = None  # 存储过滤后的代码，用于输入完成后复制到剪切板

    def _get_nearby_keys(self, char):
        """
        获取键盘上字符周围的按键（用于模拟打错字）
        :param char: 要输入的字符
        :return: 附近按键列表
        """
        # 键盘布局映射（可以根据需要扩展）
        keyboard_layout = {
            'q': ['w', 'a', 's'], 'w': ['q', 'e', 's', 'd'], 'e': ['w', 'r', 'd', 'f'],
            'r': ['e', 't', 'f', 'g'], 't': ['r', 'y', 'g', 'h'], 'y': ['t', 'u', 'h', 'j'],
            'u': ['y', 'i', 'j', 'k'], 'i': ['u', 'o', 'k', 'l'], 'o': ['i', 'p', 'l'],
            'p': ['o'], 'a': ['q', 'w', 's', 'z'], 's': ['w', 'e', 'a', 'd', 'x', 'z'],
            'd': ['e', 'r', 's', 'f', 'c', 'x'], 'f': ['r', 't', 'd', 'g', 'v', 'c'],
            'g': ['t', 'y', 'f', 'h', 'b', 'v'], 'h': ['y', 'u', 'g', 'j', 'n', 'b'],
            'j': ['u', 'i', 'h', 'k', 'm', 'n'], 'k': ['i', 'o', 'j', 'l', 'm'],
            'l': ['o', 'p', 'k'], 'z': ['a', 's', 'x'], 'x': ['s', 'd', 'z', 'c'],
            'c': ['d', 'f', 'x', 'v'], 'v': ['f', 'g', 'c', 'b'], 'b': ['g', 'h', 'v', 'n'],
            'n': ['h', 'j', 'b', 'm'], 'm': ['j', 'k', 'n']
        }

        char_lower = char.lower()
        if char_lower in keyboard_layout:
            return keyboard_layout[char_lower]
        return []

    def _type_with_realistic_errors(self, char, delay=0.05, error_rate=0.08):
        """
        模拟真实打字，有一定概率打错并退格修正
        :param char: 要输入的字符
        :param delay: 输入延迟
        :param error_rate: 出错概率 (默认8%)
        """
        import pyautogui

        if random.random() < error_rate:
            nearby_chars = self._get_nearby_keys(char)
            if nearby_chars:
                num_errors = random.randint(1, min(3, len(nearby_chars)))
                wrong_chars = random.sample(nearby_chars, num_errors)

                for wrong_char in wrong_chars:
                    pyautogui.typewrite(wrong_char, interval=delay * 0.7)
                    time.sleep(random.uniform(0.1, 0.3))
                    pyautogui.press('backspace')
                    time.sleep(random.uniform(0.05, 0.15))
                return True  # 发生了错误并修正
        return False  # 没有错误

    def run(self):
        """执行自动写入"""
        import pyautogui

        typing_start_time = time.time()

        try:
            # 读取文件内容
            if not os.path.exists(self.code_file_path):
                self.error_occurred.emit(f"代码文件不存在: {self.code_file_path}")
                return

            with open(self.code_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 过滤Markdown代码块标记行（```python 和 ```）
            filtered_lines = []
            for line in lines:
                stripped = line.strip()
                # 跳过代码块开始标记（如 ```python, ```, ```java 等）
                if stripped.startswith('```'):
                    print(f"⏭️ 跳过代码块标记: {stripped}")
                    continue
                filtered_lines.append(line)
            lines = filtered_lines

            total_chars = sum(len(line) for line in lines)
            print(f"准备输入 {len(lines)} 行（已过滤Markdown标记），共 {total_chars} 个字符")

            self.typing_started.emit()
            self.status_update.emit("准备输入...")

            # 给用户3秒时间切换到目标窗口
            self.status_update.emit("请在5秒内切换到目标窗口...并检查是否为英文输入状态！！")
            time.sleep(5)
            print("开始输入...")
            self.status_update.emit("正在输入代码...")

            last_leading_spaces = None
            need_home = False

            # 逐行输入
            for line_idx, line in enumerate(lines):
                # 检查停止信号
                if self._stop_flag:
                    print("\n用户中断输入！")
                    self.status_update.emit("输入已中断")
                    return

                # 检查暂停状态
                while self._paused and not self._stop_flag:
                    time.sleep(0.1)
                if self._stop_flag:
                    return

                # 发送进度更新
                self.progress_update.emit(line_idx + 1, len(lines))

                # 展开tab为4空格并计算缩进
                expanded_line = line.expandtabs(4)
                leading_spaces = len(expanded_line) - len(expanded_line.lstrip(" "))

                # 判断是否需要Home键处理（缩进减少时）
                if last_leading_spaces is not None and leading_spaces < last_leading_spaces:
                    need_home = True

                if need_home:
                    pyautogui.press('home')
                    need_home = False
                    # 逐字符输入（带错误模拟）
                    for char in line:
                        if char == '\n' and line.strip():
                            pyautogui.typewrite(' ')
                        else:
                            random_delay = random.uniform(self.delay * 0.5, self.delay * 1.5)
                            self._type_with_realistic_errors(char, delay=random_delay, error_rate=self.error_rate)
                            pyautogui.typewrite(char, interval=random_delay)
                    # 输入换行
                    if line.strip():
                        pyautogui.typewrite('\n')
                        think_time = random.uniform(self.think_time_min, self.think_time_max)
                        time.sleep(think_time)
                    print(f"[Home] 已输入行 {line_idx + 1}")
                else:
                    # 普通行输入
                    line_content = line.strip()
                    for char in line_content:
                        random_delay = random.uniform(self.delay * 0.5, self.delay * 2.5)
                        # 使用错误模拟打字
                        self._type_with_realistic_errors(char, delay=random_delay, error_rate=self.error_rate)
                        pyautogui.typewrite(char, interval=random_delay)

                    # 输入空格和换行
                    if line_content:
                        pyautogui.typewrite(' ')
                    pyautogui.typewrite('\n')

                    # 随机延迟模拟思考时间
                    think_time = random.uniform(self.think_time_min, self.think_time_max)
                    time.sleep(think_time)

                # 长行随机换行（更自然的打字行为）
                line_content = line.strip()
                if len(line_content) > 18 and random.random() > self.line_break_rate:
                    pyautogui.press('enter')
                    pause_time = random.uniform(1, 3)
                    time.sleep(pause_time)

                # 每10行显示进度
                if (line_idx + 1) % 10 == 0 or line_idx == len(lines) - 1:
                    print(f"已输入 {line_idx + 1}/{len(lines)} 行")
                    self.status_update.emit(f"已输入 {line_idx + 1}/{len(lines)} 行")

                last_leading_spaces = leading_spaces

            total_elapsed = time.time() - typing_start_time
            print(f"✅ 输入完成! (总耗时: {total_elapsed:.2f}s)")
            self.status_update.emit("写入完成")

            # 自动输入完成后，发送信号触发剪切板复制
            if self.filtered_code:
                self.clipboard_ready.emit(self.filtered_code)
                print("📋 自动输入完成，代码已发送至主线程进行剪切板复制")

            self.typing_completed.emit(total_elapsed)

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"❌ 自动写入失败: {str(e)}\n{error_detail}")
            self.error_occurred.emit(f"自动写入失败: {str(e)}")

    def stop_typing(self):
        """停止自动输入"""
        self._stop_flag = True
        print("\n正在停止输入...")

    def toggle_pause(self):
        """切换暂停/恢复状态（线程安全）"""
        # 如果已经停止，不允许切换暂停状态
        if self._stop_flag:
            print("⚠️ 任务已停止，无法切换暂停状态")
            return

        self._paused = not self._paused
        if self._paused:
            print("\n⏸️ [已暂停] - 按 Alt+L 恢复或 Ctrl+K 停止")
            self.typing_paused.emit()
            self.status_update.emit("已暂停")
        else:
            print("\n▶️ [已恢复] 继续输入...")
            self.typing_resumed.emit()
            self.status_update.emit("恢复输入")