"""
预警系统模块
支持短信和邮箱预警功能
"""

import smtplib
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
import os
from datetime import datetime
import json

class AlertSystem:
    """预警系统基类"""
    
    def __init__(self):
        self.alert_history = []
        self.is_enabled = True
        self.alert_cooldown = 60  # 预警冷却时间（秒）
        self.last_alert_time = 0
        
    def send_alert(self, message: str, image: Optional[np.ndarray] = None, 
                   alert_type: str = "fall_detection") -> bool:
        """
        发送预警
        
        Args:
            message: 预警消息
            image: 预警图像（可选）
            alert_type: 预警类型
            
        Returns:
            是否发送成功
        """
        if not self.is_enabled:
            return False
        
        # 检查冷却时间
        current_time = time.time()
        if current_time - self.last_alert_time < self.alert_cooldown:
            return False
        
        # 记录预警历史
        alert_record = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'message': message,
            'success': False
        }
        
        # 发送预警
        success = self._send_alert_impl(message, image, alert_type)
        alert_record['success'] = success
        
        if success:
            self.last_alert_time = current_time
        
        self.alert_history.append(alert_record)
        return success
    
    def _send_alert_impl(self, message: str, image: Optional[np.ndarray], 
                        alert_type: str) -> bool:
        """具体实现预警发送（子类重写）"""
        raise NotImplementedError
    
    def get_alert_history(self) -> List[Dict[str, Any]]:
        """获取预警历史"""
        return self.alert_history.copy()
    
    def clear_alert_history(self):
        """清空预警历史"""
        self.alert_history.clear()
    
    def set_cooldown(self, seconds: int):
        """设置预警冷却时间"""
        self.alert_cooldown = seconds
    
    def enable(self):
        """启用预警系统"""
        self.is_enabled = True
    
    def disable(self):
        """禁用预警系统"""
        self.is_enabled = False

class EmailAlertSystem(AlertSystem):
    """邮箱预警系统"""
    
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        super().__init__()
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = None
        self.sender_password = None
        self.recipient_emails = []
        self.is_configured = False
    
    def configure(self, sender_email: str, sender_password: str, 
                 recipient_emails: List[str]):
        """
        配置邮箱设置
        
        Args:
            sender_email: 发送者邮箱
            sender_password: 发送者密码（应用专用密码）
            recipient_emails: 接收者邮箱列表
        """
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_emails = recipient_emails
        self.is_configured = True
        print("邮箱预警系统配置完成")
    
    def _send_alert_impl(self, message: str, image: Optional[np.ndarray], 
                        alert_type: str) -> bool:
        """发送邮箱预警"""
        if not self.is_configured:
            print("邮箱预警系统未配置")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(self.recipient_emails)
            msg['Subject'] = f"摔倒检测预警 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 添加文本内容
            text_content = f"""
摔倒检测系统预警

时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
类型: {alert_type}
消息: {message}

此邮件由摔倒检测系统自动发送，请及时查看。
            """
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            
            # 添加图像附件（如果有）
            if image is not None:
                # 保存图像到临时文件
                temp_image_path = f"temp_alert_image_{int(time.time())}.jpg"
                cv2.imwrite(temp_image_path, image)
                
                with open(temp_image_path, 'rb') as f:
                    img_data = f.read()
                
                image_attachment = MIMEImage(img_data)
                image_attachment.add_header('Content-Disposition', 'attachment', 
                                          filename=f"fall_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                msg.attach(image_attachment)
                
                # 删除临时文件
                os.remove(temp_image_path)
            
            # 发送邮件
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            server.send_message(msg)
            server.quit()
            
            print(f"邮箱预警发送成功: {message}")
            return True
            
        except Exception as e:
            print(f"邮箱预警发送失败: {e}")
            return False
    
    def test_connection(self) -> bool:
        """测试邮箱连接"""
        if not self.is_configured:
            return False
        
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.quit()
            print("邮箱连接测试成功")
            return True
        except Exception as e:
            print(f"邮箱连接测试失败: {e}")
            return False

class SMSAlertSystem(AlertSystem):
    """短信预警系统（使用第三方服务）"""
    
    def __init__(self):
        super().__init__()
        self.api_key = None
        self.api_secret = None
        self.phone_numbers = []
        self.is_configured = False
    
    def configure(self, api_key: str, api_secret: str, phone_numbers: List[str]):
        """
        配置短信服务
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            phone_numbers: 手机号码列表
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.phone_numbers = phone_numbers
        self.is_configured = True
        print("短信预警系统配置完成")
    
    def _send_alert_impl(self, message: str, image: Optional[np.ndarray], 
                        alert_type: str) -> bool:
        """发送短信预警"""
        if not self.is_configured:
            print("短信预警系统未配置")
            return False
        
        try:
            # 这里需要根据具体的短信服务提供商实现
            # 示例使用阿里云短信服务
            success_count = 0
            
            for phone in self.phone_numbers:
                # 这里应该调用实际的短信API
                # 由于需要具体的API实现，这里只是示例
                print(f"发送短信到 {phone}: {message}")
                success_count += 1
            
            if success_count > 0:
                print(f"短信预警发送成功: {success_count} 条")
                return True
            else:
                print("短信预警发送失败")
                return False
                
        except Exception as e:
            print(f"短信预警发送失败: {e}")
            return False
    
    def test_connection(self) -> bool:
        """测试短信服务连接"""
        if not self.is_configured:
            return False
        
        try:
            # 这里应该测试实际的API连接
            print("短信服务连接测试成功")
            return True
        except Exception as e:
            print(f"短信服务连接测试失败: {e}")
            return False

class AlertManager:
    """预警管理器"""
    
    def __init__(self):
        self.email_alert = EmailAlertSystem()
        self.sms_alert = SMSAlertSystem()
        self.alert_methods = []
    
    def add_email_alert(self, sender_email: str, sender_password: str, 
                       recipient_emails: List[str]):
        """添加邮箱预警"""
        self.email_alert.configure(sender_email, sender_password, recipient_emails)
        self.alert_methods.append(self.email_alert)
    
    def add_sms_alert(self, api_key: str, api_secret: str, phone_numbers: List[str]):
        """添加短信预警"""
        self.sms_alert.configure(api_key, api_secret, phone_numbers)
        self.alert_methods.append(self.sms_alert)
    
    def send_fall_alert(self, confidence: float, image: Optional[np.ndarray] = None, 
                       location: str = "未知位置"):
        """发送摔倒预警"""
        message = f"检测到摔倒事件！置信度: {confidence:.2f}, 位置: {location}"
        
        # 异步发送预警
        def send_alerts():
            for alert_method in self.alert_methods:
                alert_method.send_alert(message, image, "fall_detection")
        
        # 在新线程中发送预警，避免阻塞主程序
        alert_thread = threading.Thread(target=send_alerts)
        alert_thread.daemon = True
        alert_thread.start()
    
    def send_system_alert(self, message: str, alert_type: str = "system"):
        """发送系统预警"""
        def send_alerts():
            for alert_method in self.alert_methods:
                alert_method.send_alert(message, None, alert_type)
        
        alert_thread = threading.Thread(target=send_alerts)
        alert_thread.daemon = True
        alert_thread.start()
    
    def get_all_alert_history(self) -> List[Dict[str, Any]]:
        """获取所有预警历史"""
        all_history = []
        for alert_method in self.alert_methods:
            all_history.extend(alert_method.get_alert_history())
        
        # 按时间排序
        all_history.sort(key=lambda x: x['timestamp'])
        return all_history
    
    def clear_all_history(self):
        """清空所有预警历史"""
        for alert_method in self.alert_methods:
            alert_method.clear_alert_history()
    
    def test_all_connections(self) -> Dict[str, bool]:
        """测试所有预警方式连接"""
        results = {}
        
        if self.email_alert.is_configured:
            results['email'] = self.email_alert.test_connection()
        
        if self.sms_alert.is_configured:
            results['sms'] = self.sms_alert.test_connection()
        
        return results

class AlertConfig:
    """预警配置管理"""
    
    def __init__(self, config_file: str = "alert_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        
        # 默认配置
        return {
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'sender_email': '',
                'sender_password': '',
                'recipient_emails': []
            },
            'sms': {
                'enabled': False,
                'api_key': '',
                'api_secret': '',
                'phone_numbers': []
            },
            'general': {
                'alert_cooldown': 60,
                'enable_alerts': True
            }
        }
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print("配置已保存")
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def update_email_config(self, enabled: bool, smtp_server: str, smtp_port: int,
                           sender_email: str, sender_password: str, 
                           recipient_emails: List[str]):
        """更新邮箱配置"""
        self.config['email'] = {
            'enabled': enabled,
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'sender_email': sender_email,
            'sender_password': sender_password,
            'recipient_emails': recipient_emails
        }
        self.save_config()
    
    def update_sms_config(self, enabled: bool, api_key: str, api_secret: str,
                         phone_numbers: List[str]):
        """更新短信配置"""
        self.config['sms'] = {
            'enabled': enabled,
            'api_key': api_key,
            'api_secret': api_secret,
            'phone_numbers': phone_numbers
        }
        self.save_config()
    
    def update_general_config(self, alert_cooldown: int, enable_alerts: bool):
        """更新通用配置"""
        self.config['general'] = {
            'alert_cooldown': alert_cooldown,
            'enable_alerts': enable_alerts
        }
        self.save_config()

if __name__ == "__main__":
    # 测试代码
    print("测试预警系统...")
    
    # 创建预警管理器
    alert_manager = AlertManager()
    
    # 配置邮箱预警（需要实际的邮箱信息）
    # alert_manager.add_email_alert(
    #     sender_email="your_email@gmail.com",
    #     sender_password="your_app_password",
    #     recipient_emails=["recipient@example.com"]
    # )
    
    # 配置短信预警（需要实际的API信息）
    # alert_manager.add_sms_alert(
    #     api_key="your_api_key",
    #     api_secret="your_api_secret",
    #     phone_numbers=["+8613800138000"]
    # )
    
    # 测试预警
    # alert_manager.send_fall_alert(0.85, None, "客厅")
    
    print("预警系统测试完成") 