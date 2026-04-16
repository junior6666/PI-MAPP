"""
Windows 服务管理器
功能：将程序注册为Windows服务，实现真正的7×24小时运行
"""

import os
import sys
import subprocess
import winreg


class WindowsServiceManager:
    """Windows服务管理器 - 使用schtasks创建计划任务实现自启和守护"""
    
    def __init__(self, task_name="AceInterviewGuardian", app_path=None):
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
            return f'"{sys.executable}" "{os.path.abspath("main_app.py")}"'
    
    def _get_guardian_script_path(self):
        """获取守护脚本路径"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        guardian_path = os.path.join(script_dir, "process_guardian.py")
        
        if getattr(sys, 'frozen', False):
            # 打包后，守护脚本应该在exe同目录
            exe_dir = os.path.dirname(sys.executable)
            guardian_path = os.path.join(exe_dir, "process_guardian.py")
        
        return guardian_path
    
    def install_as_service(self, max_restarts=10, restart_delay=3):
        """
        安装为系统服务（使用计划任务）
        
        Args:
            max_restarts: 最大重启次数
            restart_delay: 重启延迟
            
        Returns:
            tuple: (bool success, str message)
        """
        try:
            guardian_script = self._get_guardian_script_path()
            
            if not os.path.exists(guardian_script):
                return False, f"找不到守护脚本: {guardian_script}"
            
            # 构建命令
            if getattr(sys, 'frozen', False):
                # 打包环境：直接运行exe
                cmd = f'"{sys.executable}"'
            else:
                # 开发环境：运行Python脚本
                python_exe = sys.executable
                cmd = f'"{python_exe}" "{guardian_script}" --script main_app.py --max-restarts {max_restarts} --restart-delay {restart_delay}'
            
            # 删除旧任务（如果存在）
            self.uninstall_service()
            
            # 创建计划任务（登录时启动 + 崩溃后重启）
            create_task_cmd = [
                'schtasks', '/Create',
                '/TN', self.task_name,
                '/TR', cmd,
                '/SC', 'ONLOGON',  # 登录时启动
                '/RL', 'HIGHEST',   # 最高权限
                '/RU', 'SYSTEM',    # 以系统账户运行
                '/F'                # 强制覆盖
            ]
            
            result = subprocess.run(
                create_task_cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                # 额外添加：程序崩溃后自动重启的任务
                self._add_restart_on_failure()
                return True, "✅ 已成功安装为系统服务（计划任务）"
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return False, f"❌ 安装失败: {error_msg}"
                
        except Exception as e:
            return False, f"❌ 安装异常: {str(e)}"
    
    def _add_restart_on_failure(self):
        """添加崩溃后自动重启的配置"""
        try:
            # 使用PowerShell设置任务的重启策略
            ps_script = f'''
            $task = Get-ScheduledTask -TaskName "{self.task_name}"
            $settings = $task.Settings
            $settings.RestartCount = 5
            $settings.RestartInterval = "PT5M"  # 5分钟后重启
            $settings.ExecutionTimeLimit = "PT0S"  # 无时间限制
            $settings.DisallowStartIfOnBatteries = $false
            $settings.StopIfGoingOnBatteries = $false
            Set-ScheduledTask -InputObject $task
            '''
            
            subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except:
            pass  # 忽略错误，基本功能已可用
    
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


if __name__ == "__main__":
    # 测试代码
    manager = WindowsServiceManager()
    
    print("=" * 60)
    print("Windows 服务管理器测试")
    print("=" * 60)
    
    # 检查状态
    status = manager.get_service_status()
    print(f"\n当前状态:")
    print(f"  已安装: {'是' if status['installed'] else '否'}")
    print(f"  运行中: {'是' if status['running'] else '否'}")
    
    if status['last_run']:
        print(f"  上次运行: {status['last_run']}")
    if status['next_run']:
        print(f"  下次运行: {status['next_run']}")
    
    print("\n" + "=" * 60)
