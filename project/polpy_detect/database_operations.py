import mysql.connector
from mysql.connector import Error
from datetime import datetime
import json
import traceback
from database_setup import DatabaseManager

class DatabaseOperations:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def save_detection_record(self, patient_info, detection_results, source_path, result_path, detection_type="图片"):
        """保存检测记录到数据库"""
        try:
            if not self.db_manager or not self.db_manager.connection:
                return False
            
            cursor = self.db_manager.connection.cursor()
            
            # 数据验证
            if not patient_info.get('name', '').strip():
                print("患者姓名不能为空")
                return False
            
            if not detection_results:
                print("检测结果不能为空")
                return False
            
            # 插入患者信息
            patient_sql = """
                INSERT INTO patients (name, gender, age, medical_record_number, phone)
                VALUES (%s, %s, %s, %s, %s)
            """
            patient_data = (
                patient_info['name'].strip(),
                patient_info['gender'],
                patient_info['age'],
                patient_info['medical_record_number'].strip(),
                patient_info['phone'].strip()
            )
            cursor.execute(patient_sql, patient_data)
            patient_id = cursor.lastrowid
            
            # 计算总处理时间
            total_processing_time = sum(result.get('time_ms', 0) for result in detection_results)
            
            # 插入检测记录
            record_sql = """
                INSERT INTO detection_records 
                (patient_id, doctor_id, source_file_path, result_file_path, detection_type, processing_time_ms, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            record_data = (
                patient_id,
                1,  # 默认医生ID
                source_path,
                result_path,
                detection_type,
                total_processing_time,
                patient_info.get('notes', '').strip()
            )
            cursor.execute(record_sql, record_data)
            record_id = cursor.lastrowid
            
            # 插入检测详情
            for result in detection_results:
                detail_sql = """
                    INSERT INTO detection_details 
                    (record_id, polyp_type, confidence, coordinates_x1, coordinates_y1, coordinates_x2, coordinates_y2, detection_time_ms)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # 解析坐标字符串
                coords_str = result.get('coordinates', '(0,0,0,0)')
                coords = self.parse_coordinates(coords_str)
                
                detail_data = (
                    record_id,
                    result.get('class', '未知'),
                    result.get('confidence', 0),
                    coords[0], coords[1], coords[2], coords[3],
                    result.get('time_ms', 0)
                )
                cursor.execute(detail_sql, detail_data)
            
            self.db_manager.connection.commit()
            cursor.close()
            print(f"成功保存检测记录，记录ID: {record_id}")
            return True
            
        except Error as e:
            print(f"保存检测记录错误: {e}")
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
            return False
        except Exception as e:
            print(f"保存检测记录异常: {e}")
            print(traceback.format_exc())
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
            return False
    
    def parse_coordinates(self, coords_str):
        """解析坐标字符串"""
        try:
            # 移除括号和空格，分割逗号
            coords = coords_str.strip('()').replace(' ', '').split(',')
            return [float(x) for x in coords]
        except:
            return [0, 0, 0, 0]

    def get_detection_history(
            self,
            search_keyword: str = "",
            search_field: str = "患者信息",
            date_from=None,
            date_to=None,
            page: int = 1,
            page_size: int = 10,
    ):
        """
        在事务内一次性完成总数+分页查询，保证一致性
        返回 (records, total_count)
        """
        if not self.db_manager or not self.db_manager.connection:
            return [], 0

        try:
            conn = self.db_manager.connection
            # 开启事务，使用 REPEATABLE READ 隔离级别
            conn.start_transaction(isolation_level='REPEATABLE READ')
            cursor = conn.cursor(dictionary=True)

            # ---------- 1. 构造 WHERE 条件 ----------
            where_conditions = []
            params = []

            if search_keyword:
                kw = f"%{search_keyword}%"
                if search_field == "患者信息":
                    where_conditions.append("(p.name LIKE %s OR p.medical_record_number LIKE %s)")
                    params.extend([kw, kw])
                elif search_field == "医生信息":
                    where_conditions.append("(d.name LIKE %s OR d.department LIKE %s)")
                    params.extend([kw, kw])
                elif search_field == "类别":
                    where_conditions.append("dd.polyp_type LIKE %s")
                    params.append(kw)
                elif search_field == "日期":
                    where_conditions.append("DATE(dr.detection_date) LIKE %s")
                    params.append(kw)

            if date_from:
                where_conditions.append("dr.detection_date >= %s")
                params.append(date_from)
            if date_to:
                where_conditions.append("dr.detection_date <= %s")
                params.append(date_to)

            where_clause = " AND ".join(where_conditions)
            if where_clause:
                where_clause = "WHERE " + where_clause

            # ---------- 2. 查总数 ----------
            count_sql = f"""
                   SELECT COUNT(DISTINCT dr.id) AS total
                   FROM detection_records dr
                   LEFT JOIN patients p   ON dr.patient_id = p.id
                   LEFT JOIN doctors d    ON dr.doctor_id  = d.id
                   LEFT JOIN detection_details dd ON dr.id = dd.record_id
                   {where_clause}
               """
            cursor.execute(count_sql, params)
            total_count = cursor.fetchone()["total"]

            # ---------- 3. 查分页数据 ----------
            offset = (page - 1) * page_size
            data_sql = f"""
                   SELECT DISTINCT
                       dr.id,
                       p.name AS patient_name,
                       d.name AS doctor_name,
                       d.department AS doctor_department,
                       dr.detection_type,
                       dr.detection_date,
                       dr.processing_time_ms,
                       dr.source_file_path,
                       dr.result_file_path,
                       dr.notes,
                       GROUP_CONCAT(DISTINCT dd.polyp_type) AS polyp_types,
                       COUNT(dd.id) AS detection_count,
                       AVG(dd.confidence) AS avg_confidence
                   FROM detection_records dr
                   LEFT JOIN patients p   ON dr.patient_id = p.id
                   LEFT JOIN doctors d    ON dr.doctor_id  = d.id
                   LEFT JOIN detection_details dd ON dr.id = dd.record_id
                   {where_clause}
                   GROUP BY dr.id
                   ORDER BY dr.detection_date DESC
                   LIMIT %s OFFSET %s
               """
            cursor.execute(data_sql, params + [page_size, offset])
            records = cursor.fetchall()

            # ---------- 4. 提交事务 ----------
            conn.commit()
            return records, total_count

        except Error as e:
            conn.rollback()
            print(f"获取历史记录错误: {e}")
            return [], 0
        except Exception as e:
            conn.rollback()
            print(f"获取历史记录异常: {e}")
            traceback.print_exc()
            return [], 0
        finally:
            # 如果 cursor 已创建，确保关闭
            try:
                cursor.close()
            except:
                pass
    
    def get_detection_details(self, record_id):
        """获取检测详情"""
        try:
            if not self.db_manager or not self.db_manager.connection:
                return []
            
            cursor = self.db_manager.connection.cursor(dictionary=True)
            
            sql = """
                SELECT 
                    dd.id,
                    dd.polyp_type,
                    dd.confidence,
                    CONCAT('(', dd.coordinates_x1, ',', dd.coordinates_y1, ',', dd.coordinates_x2, ',', dd.coordinates_y2, ')') as coordinates,
                    dd.detection_time_ms
                FROM detection_details dd
                WHERE dd.record_id = %s
                ORDER BY dd.id
            """
            cursor.execute(sql, (record_id,))
            details = cursor.fetchall()
            
            cursor.close()
            return details
            
        except Error as e:
            print(f"获取检测详情错误: {e}")
            return []
        except Exception as e:
            print(f"获取检测详情异常: {e}")
            print(traceback.format_exc())
            return []
    
    def get_patient_info(self, record_id):
        """获取患者信息"""
        try:
            if not self.db_manager or not self.db_manager.connection:
                return {}
            
            cursor = self.db_manager.connection.cursor(dictionary=True)
            
            sql = """
                SELECT 
                    p.name, p.gender, p.age, p.medical_record_number, p.phone,
                    d.name as doctor_name, d.department, d.title,
                    dr.detection_date, dr.notes, dr.detection_type, dr.processing_time_ms
                FROM detection_records dr
                LEFT JOIN patients p ON dr.patient_id = p.id
                LEFT JOIN doctors d ON dr.doctor_id = d.id
                WHERE dr.id = %s
            """
            cursor.execute(sql, (record_id,))
            patient_info = cursor.fetchone()
            
            cursor.close()
            return patient_info or {}
            
        except Error as e:
            print(f"获取患者信息错误: {e}")
            return {}
        except Exception as e:
            print(f"获取患者信息异常: {e}")
            print(traceback.format_exc())
            return {}

    def get_record_paths(self, record_id):
        """从 detection_records 获取源图与结果图路径"""
        try:
            if not self.db_manager or not self.db_manager.connection:
                return {}
            cursor = self.db_manager.connection.cursor(dictionary=True)
            sql = """
                SELECT source_file_path, result_file_path
                FROM detection_records
                WHERE id = %s
            """
            cursor.execute(sql, (record_id,))
            paths = cursor.fetchone()
            cursor.close()
            return paths or {}
        except Exception as e:
            print(f"获取记录路径异常: {e}")
            traceback.print_exc()
            return {}
    def get_system_config(self, config_key=None):
        """获取系统配置"""
        try:
            if not self.db_manager or not self.db_manager.connection:
                return {}
            
            cursor = self.db_manager.connection.cursor(dictionary=True)
            
            if config_key:
                sql = "SELECT config_key, config_value FROM system_config WHERE config_key = %s"
                cursor.execute(sql, (config_key,))
                result = cursor.fetchone()
                cursor.close()
                return result['config_value'] if result else None
            else:
                sql = "SELECT config_key, config_value FROM system_config"
                cursor.execute(sql)
                results = cursor.fetchall()
                cursor.close()
                return {row['config_key']: row['config_value'] for row in results}
                
        except Error as e:
            print(f"获取系统配置错误: {e}")
            return {}
        except Exception as e:
            print(f"获取系统配置异常: {e}")
            print(traceback.format_exc())
            return {}
    
    def update_system_config(self, config_key, config_value):
        """更新系统配置"""
        try:
            if not self.db_manager or not self.db_manager.connection:
                return False
            
            cursor = self.db_manager.connection.cursor()
            
            sql = """
                INSERT INTO system_config (config_key, config_value) 
                VALUES (%s, %s) 
                ON DUPLICATE KEY UPDATE config_value = VALUES(config_value)
            """
            cursor.execute(sql, (config_key, config_value))
            self.db_manager.connection.commit()
            cursor.close()
            return True
            
        except Error as e:
            print(f"更新系统配置错误: {e}")
            return False
        except Exception as e:
            print(f"更新系统配置异常: {e}")
            print(traceback.format_exc())
            return False
    
    def get_statistics(self):
        """获取统计信息"""
        try:
            if not self.db_manager or not self.db_manager.connection:
                return {}
            
            cursor = self.db_manager.connection.cursor(dictionary=True)
            
            # 总检测次数
            cursor.execute("SELECT COUNT(*) as total_detections FROM detection_records")
            total_detections = cursor.fetchone()['total_detections']
            
            # 息肉类型统计
            cursor.execute("""
                SELECT polyp_type, COUNT(*) as count 
                FROM detection_details 
                GROUP BY polyp_type
            """)
            polyp_stats = cursor.fetchall()
            
            # 今日检测次数
            cursor.execute("""
                SELECT COUNT(*) as today_detections 
                FROM detection_records 
                WHERE DATE(detection_date) = CURDATE()
            """)
            today_detections = cursor.fetchone()['today_detections']
            
            # 平均处理时间
            cursor.execute("""
                SELECT AVG(processing_time_ms) as avg_time 
                FROM detection_records 
                WHERE processing_time_ms > 0
            """)
            avg_time = cursor.fetchone()['avg_time'] or 0
            
            # 检测类型统计
            cursor.execute("""
                SELECT detection_type, COUNT(*) as count 
                FROM detection_records 
                GROUP BY detection_type
            """)
            type_stats = cursor.fetchall()
            
            # 最近7天检测趋势
            cursor.execute("""
                SELECT DATE(detection_date) as date, COUNT(*) as count 
                FROM detection_records 
                WHERE detection_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY DATE(detection_date)
                ORDER BY date
            """)
            trend_stats = cursor.fetchall()
            
            cursor.close()
            
            return {
                'total_detections': total_detections,
                'today_detections': today_detections,
                'avg_processing_time': avg_time,
                'polyp_statistics': polyp_stats,
                'type_statistics': type_stats,
                'trend_statistics': trend_stats
            }
            
        except Error as e:
            print(f"获取统计信息错误: {e}")
            return {}
        except Exception as e:
            print(f"获取统计信息异常: {e}")
            print(traceback.format_exc())
            return {}
    
    def delete_detection_record(self, record_id):
        """删除检测记录"""
        try:
            if not self.db_manager or not self.db_manager.connection:
                return False
            
            cursor = self.db_manager.connection.cursor()
            
            # 删除检测详情（级联删除）
            cursor.execute("DELETE FROM detection_details WHERE record_id = %s", (record_id,))
            
            # 删除检测记录
            cursor.execute("DELETE FROM detection_records WHERE id = %s", (record_id,))
            
            self.db_manager.connection.commit()
            cursor.close()
            print(f"成功删除检测记录，记录ID: {record_id}")
            return True
            
        except Error as e:
            print(f"删除检测记录错误: {e}")
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
            return False
        except Exception as e:
            print(f"删除检测记录异常: {e}")
            print(traceback.format_exc())
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
            return False
    
    def batch_delete_records(self, record_ids):
        """批量删除检测记录"""
        try:
            if not self.db_manager or not self.db_manager.connection:
                return False
            
            if not record_ids:
                return True
            
            cursor = self.db_manager.connection.cursor()
            
            # 构建IN查询
            placeholders = ','.join(['%s'] * len(record_ids))
            
            # 删除检测详情
            cursor.execute(f"DELETE FROM detection_details WHERE record_id IN ({placeholders})", record_ids)
            
            # 删除检测记录
            cursor.execute(f"DELETE FROM detection_records WHERE id IN ({placeholders})", record_ids)
            
            self.db_manager.connection.commit()
            cursor.close()
            print(f"成功批量删除 {len(record_ids)} 条检测记录")
            return True
            
        except Error as e:
            print(f"批量删除检测记录错误: {e}")
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
            return False
        except Exception as e:
            print(f"批量删除检测记录异常: {e}")
            print(traceback.format_exc())
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
            return False
    
    def export_records_to_json(self, record_ids=None, output_file="exported_records.json"):
        """导出记录到JSON文件"""
        try:
            if not self.db_manager or not self.db_manager.connection:
                return False
            
            cursor = self.db_manager.connection.cursor(dictionary=True)
            
            if record_ids:
                # 导出指定记录
                placeholders = ','.join(['%s'] * len(record_ids))
                sql = f"""
                    SELECT 
                        dr.id, dr.detection_date, dr.detection_type, dr.processing_time_ms,
                        p.name as patient_name, p.gender, p.age, p.medical_record_number,
                        d.name as doctor_name, d.department,
                        dd.polyp_type, dd.confidence, dd.coordinates_x1, dd.coordinates_y1, 
                        dd.coordinates_x2, dd.coordinates_y2, dd.detection_time_ms
                    FROM detection_records dr
                    LEFT JOIN patients p ON dr.patient_id = p.id
                    LEFT JOIN doctors d ON dr.doctor_id = d.id
                    LEFT JOIN detection_details dd ON dr.id = dd.record_id
                    WHERE dr.id IN ({placeholders})
                    ORDER BY dr.detection_date DESC
                """
                cursor.execute(sql, record_ids)
            else:
                # 导出所有记录
                sql = """
                    SELECT 
                        dr.id, dr.detection_date, dr.detection_type, dr.processing_time_ms,
                        p.name as patient_name, p.gender, p.age, p.medical_record_number,
                        d.name as doctor_name, d.department,
                        dd.polyp_type, dd.confidence, dd.coordinates_x1, dd.coordinates_y1, 
                        dd.coordinates_x2, dd.coordinates_y2, dd.detection_time_ms
                    FROM detection_records dr
                    LEFT JOIN patients p ON dr.patient_id = p.id
                    LEFT JOIN doctors d ON dr.doctor_id = d.id
                    LEFT JOIN detection_details dd ON dr.id = dd.record_id
                    ORDER BY dr.detection_date DESC
                """
                cursor.execute(sql)
            
            records = cursor.fetchall()
            cursor.close()
            
            # 转换为JSON格式
            export_data = {
                'export_date': datetime.now().isoformat(),
                'total_records': len(records),
                'records': records
            }
            
            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"成功导出 {len(records)} 条记录到 {output_file}")
            return True
            
        except Error as e:
            print(f"导出记录错误: {e}")
            return False
        except Exception as e:
            print(f"导出记录异常: {e}")
            print(traceback.format_exc())
            return False

if __name__ == '__main__':
    import mysql.connector

    # 1. 建立连接
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root123",
        database="polyp_detection",
        charset="utf8mb4"
    )


    # 2. 包装成 db_manager
    class DBManager:
        def __init__(self, conn):
            self.connection = conn


    db_mgr = DBManager(conn)

    # 3. 调用服务
    svc = DatabaseOperations(db_mgr)
    records, total = svc.get_detection_history(
        search_keyword='',
        search_field="患者信息",
        date_from="2025-07-06",
        date_to="2025-08-06",
        page=1,
        page_size=10
    )

    print("总数:", total)
    print("本页记录:", records)