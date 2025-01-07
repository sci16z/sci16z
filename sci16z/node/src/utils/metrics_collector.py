from __future__ import annotations
import os
import json
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from utils.logger import get_logger
from utils.config import server_config
import aiohttp

class MetricsCollector:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.db_path = os.path.join(os.path.dirname(__file__), '../data/metrics.db')
        self.retention_days = 7  # Keep metrics for 7 days
        self.metrics_endpoint = server_config.get_endpoint('metrics')
        self._init_database()

    def _init_database(self):
        """Initialize metrics database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        metric_type TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        value REAL,
                        metadata TEXT
                    )
                """)
                
                # Create index on timestamp
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                    ON metrics(timestamp)
                """)
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to initialize metrics database: {str(e)}")
            raise

    async def store(self, metrics: Dict[str, Any]):
        """Store metrics in database"""
        try:
            timestamp = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Flatten and store metrics
                for metric_type, values in metrics.items():
                    if isinstance(values, dict):
                        for name, value in values.items():
                            if isinstance(value, (int, float)):
                                cursor.execute(
                                    """
                                    INSERT INTO metrics 
                                    (timestamp, metric_type, metric_name, value)
                                    VALUES (?, ?, ?, ?)
                                    """,
                                    (timestamp, metric_type, name, value)
                                )
                            else:
                                cursor.execute(
                                    """
                                    INSERT INTO metrics 
                                    (timestamp, metric_type, metric_name, metadata)
                                    VALUES (?, ?, ?, ?)
                                    """,
                                    (timestamp, metric_type, name, json.dumps(value))
                                )
                
                conn.commit()
                
            # Cleanup old metrics
            await self._cleanup_old_metrics()
            
        except Exception as e:
            self.logger.error(f"Failed to store metrics: {str(e)}")

    async def get_metrics(self, 
                         metric_type: Optional[str] = None,
                         metric_name: Optional[str] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None
                         ) -> List[Dict[str, Any]]:
        """Retrieve metrics from database"""
        try:
            query = "SELECT * FROM metrics WHERE 1=1"
            params = []
            
            if metric_type:
                query += " AND metric_type = ?"
                params.append(metric_type)
                
            if metric_name:
                query += " AND metric_name = ?"
                params.append(metric_name)
                
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())
                
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())
                
            query += " ORDER BY timestamp DESC"
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve metrics: {str(e)}")
            return []

    async def get_summary(self, metric_type: str, interval: str = '1h') -> Dict[str, Any]:
        """Get metrics summary for specified interval"""
        try:
            interval_map = {
                '1h': '1 hour',
                '6h': '6 hours',
                '1d': '1 day',
                '7d': '7 days'
            }
            
            if interval not in interval_map:
                raise ValueError(f"Invalid interval: {interval}")
                
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    SELECT 
                        metric_name,
                        AVG(value) as avg_value,
                        MIN(value) as min_value,
                        MAX(value) as max_value,
                        COUNT(*) as sample_count
                    FROM metrics
                    WHERE metric_type = ?
                    AND timestamp >= datetime('now', '-' || ?)
                    AND value IS NOT NULL
                    GROUP BY metric_name
                    """,
                    (metric_type, interval_map[interval])
                )
                
                rows = cursor.fetchall()
                
                return {
                    'interval': interval,
                    'metrics': {
                        row[0]: {
                            'avg': row[1],
                            'min': row[2],
                            'max': row[3],
                            'samples': row[4]
                        }
                        for row in rows
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get metrics summary: {str(e)}")
            return {}

    async def _cleanup_old_metrics(self):
        """Clean up metrics older than retention period"""
        try:
            cutoff = datetime.now() - timedelta(days=self.retention_days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "DELETE FROM metrics WHERE timestamp < ?",
                    (cutoff.isoformat(),)
                )
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old metrics: {str(e)}")

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total records
                cursor.execute("SELECT COUNT(*) FROM metrics")
                total_records = cursor.fetchone()[0]
                
                # Get database size
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                # Get metric types
                cursor.execute("SELECT DISTINCT metric_type FROM metrics")
                metric_types = [row[0] for row in cursor.fetchall()]
                
                return {
                    'total_records': total_records,
                    'database_size_mb': db_size / (1024 * 1024),
                    'metric_types': metric_types,
                    'retention_days': self.retention_days
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {str(e)}")
            return {} 

    async def send_metrics(self, metrics: Dict[str, Any]):
        """Send metrics to server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.metrics_endpoint, json=metrics) as response:
                    return await response.json()
        except Exception as e:
            self.logger.error(f"Failed to send metrics: {str(e)}")
            return None 