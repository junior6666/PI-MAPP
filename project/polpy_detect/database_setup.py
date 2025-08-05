import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, host='localhost', port=3306, user='root', password='root123', database='polyp_detection'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        
    def connect(self):
        """连接到MySQL数据库"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                print(f"成功连接到MySQL数据库: {self.database}")
                return True
        except Error as e:
            print(f"数据库连接错误: {e}")
            return False
    
    def create_database(self):
        """创建数据库"""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            print(f"数据库 {self.database} 创建成功")
            cursor.close()
            connection.close()
        except Error as e:
            print(f"创建数据库错误: {e}")
    
    def create_tables(self):
        """创建表结构"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return False
        
        cursor = self.connection.cursor()
        
        # 创建患者信息表
        patient_table = """
        CREATE TABLE IF NOT EXISTS patients (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            gender ENUM('男', '女') DEFAULT '男',
            age INT DEFAULT 30,
            medical_record_number VARCHAR(50) DEFAULT '666',
            phone VARCHAR(20) DEFAULT '120120120120120',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        
        # 创建医生信息表
        doctor_table = """
        CREATE TABLE IF NOT EXISTS doctors (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL DEFAULT '王医生',
            department VARCHAR(100),
            title VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # 创建检测记录表
        detection_records_table = """
        CREATE TABLE IF NOT EXISTS detection_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT,
            doctor_id INT,
            source_file_path VARCHAR(500) NOT NULL,
            result_file_path VARCHAR(500),
            detection_type ENUM('图片', '视频', '摄像头') NOT NULL,
            processing_time_ms INT,
            detection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
        """
        
        # 创建检测详情表
        detection_details_table = """
        CREATE TABLE IF NOT EXISTS detection_details (
            id INT AUTO_INCREMENT PRIMARY KEY,
            record_id INT,
            polyp_type ENUM('增生性息肉', '腺瘤息肉') NOT NULL,
            confidence DECIMAL(5,4) NOT NULL,
            coordinates_x1 DECIMAL(10,8),
            coordinates_y1 DECIMAL(10,8),
            coordinates_x2 DECIMAL(10,8),
            coordinates_y2 DECIMAL(10,8),
            detection_time_ms INT,
            FOREIGN KEY (record_id) REFERENCES detection_records(id) ON DELETE CASCADE
        )
        """
        
        # 创建系统配置表
        config_table = """
        CREATE TABLE IF NOT EXISTS system_config (
            id INT AUTO_INCREMENT PRIMARY KEY,
            config_key VARCHAR(100) UNIQUE NOT NULL,
            config_value TEXT,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        
        tables = [
            ("patients", patient_table),
            ("doctors", doctor_table),
            ("detection_records", detection_records_table),
            ("detection_details", detection_details_table),
            ("system_config", config_table)
        ]
        
        try:
            for table_name, table_sql in tables:
                cursor.execute(table_sql)
                print(f"表 {table_name} 创建成功")
            
            self.connection.commit()
            
            # 插入默认数据
            self.insert_default_data(cursor)
            
            return True
        except Error as e:
            print(f"创建表错误: {e}")
            return False
        finally:
            cursor.close()
    
    def insert_default_data(self, cursor):
        """插入默认数据"""
        # 插入默认医生
        cursor.execute("""
            INSERT IGNORE INTO doctors (id, name, department, title) 
            VALUES (1, '王医生', '消化内科', '主任医师')
        """)
        
        # 插入默认配置
        default_configs = [
            ("iou_threshold", "0.5", "IOU阈值"),
            ("confidence_threshold", "0.5", "置信度阈值"),
            ("model_weight", "pt_models/polpy_best.pt", "模型权重文件"),
            ("database_host", "localhost", "数据库主机"),
            ("database_port", "3306", "数据库端口"),
            ("database_name", "polyp_detection", "数据库名称"),
            ("database_user", "root", "数据库用户名"),
            ("database_password", "", "数据库密码")
        ]
        
        for key, value, description in default_configs:
            cursor.execute("""
                INSERT IGNORE INTO system_config (config_key, config_value, description)
                VALUES (%s, %s, %s)
            """, (key, value, description))
        
        self.connection.commit()
        print("默认数据插入成功")
    
    def test_connection(self):
        """测试数据库连接"""
        try:
            if self.connect():
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                return result is not None
        except Error as e:
            print(f"连接测试失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("数据库连接已关闭")

def setup_database():
    """设置数据库"""
    db_manager = DatabaseManager()
    
    # 创建数据库
    db_manager.create_database()
    
    # 连接数据库
    if db_manager.connect():
        # 创建表
        if db_manager.create_tables():
            print("数据库设置完成")
        else:
            print("数据库设置失败")
        db_manager.close()
    else:
        print("无法连接到数据库")

if __name__ == "__main__":
    setup_database() 