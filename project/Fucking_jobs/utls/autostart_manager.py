"""
开机自启管理模块
功能：添加/移除Windows开机自启、检查自启状态
"""

import os
import sys
import winreg


class AutoStartManager:
    """Windows开机自启管理器"""
    
    def __init__(self, app_name="AceInterview", app_path=None):
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
            return f'"{sys.executable}" "{os.path.abspath(__file__)}"'
    
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


if __name__ == "__main__":
    # 测试代码
    manager = AutoStartManager()
    
    print(f"当前自启状态: {'已启用' if manager.is_enabled() else '未启用'}")
    
    # 切换状态
    success, msg = manager.toggle_startup()
    print(msg)
    
    print(f"切换后状态: {'已启用' if manager.is_enabled() else '未启用'}")
