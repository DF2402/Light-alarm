import sqlite3
import datetime
from typing import List, Dict, Optional

TIMEZONE_OFFSET = datetime.timedelta(hours=8)

def get_local_time():
    return datetime.datetime.utcnow() + TIMEZONE_OFFSET


class SensorDB:
    
    def __init__(self, db_path: str = 'sensor_data.db'):
        self.db_path = db_path
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                sensor_id TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_device_sensor_time 
            ON sensor_data(device_id, sensor_id, timestamp)
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_data TEXT NOT NULL,
                result TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
            
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_detection_time 
            ON detection_records(timestamp)
        ''')
        
        conn.commit()
        conn.close()
        print(f"[SensorDB] Database initialized: {self.db_path}")
    
    
    def insert_sensor_data(self, device_id: str, sensor_id: str, value: float) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            sql = '''
                INSERT INTO sensor_data (device_id, sensor_id, value, timestamp)
                VALUES (?, ?, ?, ?)
            '''
            timestamp = get_local_time().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(sql, (device_id, sensor_id, float(value), timestamp))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"[SensorDB] Error inserting sensor data: {e}")
            return False
        finally:
            conn.close()
    
    def get_hourly_average(
        self, 
        device_id: str, 
        sensor_id: str,
        hours: int = 24
    ) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            time_threshold = get_local_time() - datetime.timedelta(hours=hours)
            time_threshold_str = time_threshold.strftime('%Y-%m-%d %H:%M:%S')
            
            sql = '''
                SELECT 
                    strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                    AVG(value) as avg_value
                FROM sensor_data
                WHERE device_id = ? 
                    AND sensor_id = ?
                    AND timestamp >= ?
                GROUP BY hour
                ORDER BY hour
            '''
            cursor.execute(sql, (device_id, sensor_id, time_threshold_str))
            results = cursor.fetchall()
            
            return [
                {
                    'timestamp': row['hour'],
                    'value': round(row['avg_value'], 2)
                }
                for row in results
            ]
        except Exception as e:
            print(f"[SensorDB] Error getting hourly average: {e}")
            return []
        finally:
            conn.close()
    
    
    def save_detection(self, image_data: str, result: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            sql = '''
                INSERT INTO detection_records (image_data, result, timestamp)
                VALUES (?, ?, ?)
            '''
            timestamp = get_local_time().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(sql, (image_data, result, timestamp))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"[SensorDB] Error saving detection: {e}")
            return False
        finally:
            conn.close()
    
    def get_latest_detection(self) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            sql = '''
                SELECT id, image_data, result, timestamp
                FROM detection_records
                ORDER BY timestamp DESC
                LIMIT 1
            '''
            cursor.execute(sql)
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return None
        except Exception as e:
            print(f"[SensorDB] Error getting latest detection: {e}")
            return None
        finally:
            conn.close()
    
    def get_detection_history(self, limit: int = 10) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            sql = '''
                SELECT id, image_data, result, timestamp
                FROM detection_records
                ORDER BY timestamp DESC
                LIMIT ?
            '''
            cursor.execute(sql, (limit,))
            results = cursor.fetchall()
            
            return [dict(row) for row in results]
        except Exception as e:
            print(f"[SensorDB] Error getting detection history: {e}")
            return []
        finally:
            conn.close()
