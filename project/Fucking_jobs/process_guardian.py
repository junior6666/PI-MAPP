"""
守护进程 - 监控主程序并自动重启
功能：检测主程序异常退出，自动重新启动
"""

import os
import sys
import time
import subprocess
import signal
import logging
from datetime import datetime


class ProcessGuardian:
    """进程守护器"""
    
    def __init__(self, main_script, max_restarts=10, restart_delay=3, log_file="guardian.log"):
        """
        初始化守护进程
        
        Args:
            main_script: 主程序脚本路径或可执行文件路径
            max_restarts: 最大重启次数（防止无限重启循环）
            restart_delay: 重启延迟（秒）
            log_file: 日志文件路径
        """
        self.main_script = main_script
        self.max_restarts = max_restarts
        self.restart_delay = restart_delay
        self.log_file = log_file
        self.process = None
        self.restart_count = 0
        self.running = False
        
        # 配置日志
        self._setup_logging()
    
    def _setup_logging(self):
        """配置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("ProcessGuardian")
    
    def start_main_process(self):
        """启动主程序进程"""
        try:
            # 构建命令
            if self.main_script.endswith('.py'):
                cmd = [sys.executable, self.main_script]
            else:
                cmd = [self.main_script]
            
            self.logger.info(f"🚀 启动主程序: {' '.join(cmd)}")
            
            # 启动子进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            
            self.logger.info(f"✅ 主程序已启动 (PID: {self.process.pid})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 启动主程序失败: {e}")
            return False
    
    def monitor_process(self):
        """监控主进程状态"""
        self.running = True
        self.logger.info("👁️ 守护进程开始监控...")
        
        while self.running:
            if self.process is None:
                # 首次启动
                if not self.start_main_process():
                    self.logger.error("无法启动主程序，退出守护进程")
                    break
            
            # 检查进程是否仍在运行
            poll_result = self.process.poll()
            
            if poll_result is not None:
                # 进程已结束
                exit_code = poll_result
                
                # 读取输出（非阻塞）
                try:
                    stdout, stderr = self.process.communicate(timeout=2)
                    if stderr:
                        self.logger.warning(f"主程序错误输出:\n{stderr.decode('utf-8', errors='ignore')}")
                except:
                    pass
                
                self.logger.warning(f"⚠️ 主程序已退出 (退出码: {exit_code})")
                
                # 判断是否需要重启
                if self.restart_count < self.max_restarts:
                    self.restart_count += 1
                    self.logger.info(f"🔄 准备第 {self.restart_count} 次重启 (延迟 {self.restart_delay}s)...")
                    
                    # 等待一段时间后重启
                    time.sleep(self.restart_delay)
                    
                    # 重置进程对象
                    self.process = None
                    
                    # 重新启动
                    if not self.start_main_process():
                        self.logger.error("重启失败，退出守护进程")
                        break
                else:
                    self.logger.error(f"❌ 已达到最大重启次数 ({self.max_restarts})，停止重启")
                    break
            else:
                # 进程仍在运行，短暂休眠
                time.sleep(1)
        
        self.logger.info("🛑 守护进程已停止")
    
    def stop(self):
        """停止守护进程和主程序"""
        self.logger.info("🛑 正在停止守护进程...")
        self.running = False
        
        # 终止主进程
        if self.process and self.process.poll() is None:
            try:
                self.logger.info(f"🛑 正在终止主程序 (PID: {self.process.pid})...")
                
                if sys.platform == 'win32':
                    self.process.terminate()
                    # 等待进程结束
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.logger.warning("主程序未响应，强制终止...")
                        self.process.kill()
                else:
                    os.kill(self.process.pid, signal.SIGTERM)
                
                self.logger.info("✅ 主程序已终止")
                
            except Exception as e:
                self.logger.error(f"终止主程序失败: {e}")
        
        self.logger.info("✅ 守护进程已停止")


def main():
    """守护进程入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="进程守护器")
    parser.add_argument("--script", type=str, default="main_app.py",
                       help="主程序脚本路径")
    parser.add_argument("--max-restarts", type=int, default=10,
                       help="最大重启次数")
    parser.add_argument("--restart-delay", type=int, default=3,
                       help="重启延迟（秒）")
    parser.add_argument("--log-file", type=str, default="guardian.log",
                       help="日志文件路径")
    
    args = parser.parse_args()
    
    # 获取绝对路径
    script_path = os.path.abspath(args.script)
    
    if not os.path.exists(script_path):
        print(f"❌ 主程序不存在: {script_path}")
        sys.exit(1)
    
    print("=" * 60)
    print("🛡️  进程守护器 v1.0")
    print("=" * 60)
    print(f"主程序: {script_path}")
    print(f"最大重启次数: {args.max_restarts}")
    print(f"重启延迟: {args.restart_delay}s")
    print("=" * 60)
    
    # 创建并运行守护进程
    guardian = ProcessGuardian(
        main_script=script_path,
        max_restarts=args.max_restarts,
        restart_delay=args.restart_delay,
        log_file=args.log_file
    )
    
    try:
        guardian.monitor_process()
    except KeyboardInterrupt:
        print("\n⚠️ 收到中断信号")
        guardian.stop()


if __name__ == "__main__":
    main()
